#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate exactly one image via the current Codex ChatGPT sign-in, then normalize it to the Story OS canvas."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
import tomllib
from pathlib import Path
from PIL import Image

from canvas_normalize import NormalizeError, normalize, read_canvas
from visual_profile_bridge_v224 import compile_prompt_contract
import frame_contract as resolved_frame_contract
import image_model_policy
import provider_capability
import image_artifact_collector
import raw_candidate_budget  # STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE
import runtime_router
import storyos_config
import runtime_timeout_policy

ROOT = Path(__file__).resolve().parents[2]
_CONFIG = storyos_config.load_config()
CODEX_IMAGE_CONTROLLER_MODEL = str(storyos_config.get_path(_CONFIG, "runtime.codex_image_controller_model"))
CODEX_IMAGE_REASONING_EFFORT = str(storyos_config.get_path(_CONFIG, "runtime.codex_image_reasoning_effort"))
# 图片模型/质量回落的唯一配置源是 storyos.yaml 的 image.model / image.quality；
# 不在函数默认值里复制字面量，避免改 yaml 后 worker 仍按旧模型生成。
DEFAULT_IMAGE_MODEL = image_model_policy.DEFAULT_MODEL
DEFAULT_IMAGE_QUALITY = image_model_policy.DEFAULT_QUALITY

PNG = b'\x89PNG\r\n\x1a\n'
JPEG = b'\xff\xd8\xff'

class BackendError(RuntimeError):
    pass

def valid_image(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size < 16:
        return False
    header = path.read_bytes()[:16]
    return header.startswith(PNG) or header.startswith(JPEG)

def resolve_codex(raw: str | None) -> Path:
    explicit = bool(raw or os.environ.get("CODEX_EXE"))
    if not runtime_router.local_codex_image_allowed(explicit=explicit):
        runtime, _ = runtime_router.detect()
        image_runtime, _ = runtime_router.image_execution_runtime()
        raise BackendError(
            f'LOCAL_CODEX_IMAGE_DISABLED_FOR_RUNTIME: runtime={runtime}; image_runtime={image_runtime}; '
            'select runtime.image_execution_runtime=CODEX or pass an explicit Codex executable'
        )
    value = raw or os.environ.get("CODEX_EXE")
    # On Windows prefer the newest ChatGPT Desktop bundled Codex CLI over PATH.
    # The real V2.4 smoke found an older PATH codex that could not start while the
    # desktop-bundled CLI was healthy and had the user's ChatGPT/Codex login.
    if not value and os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            root = Path(local) / "OpenAI" / "Codex" / "bin"
            candidates = []
            if root.is_dir():
                candidates.extend(root.glob("*/codex.exe"))
                candidates.extend(root.glob("codex.exe"))
            candidates = [p for p in candidates if p.is_file()]
            if candidates:
                value = str(max(candidates, key=lambda p: p.stat().st_mtime_ns))
    value = value or shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')
    if not value:
        raise BackendError('Codex CLI not found; pass --codex or set CODEX_EXE')
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise BackendError(f'Codex CLI not found: {path}')
    return path

def command_prefix(codex: Path) -> list[str]:
    if codex.suffix.lower() == '.py':
        return [sys.executable, str(codex)]
    if os.name == 'nt' and codex.suffix.lower() in {'.cmd', '.bat'}:
        return ['cmd.exe', '/d', '/c', str(codex)]
    return [str(codex)]

def provider_size(width: int, height: int) -> str:
    return f'{width}x{height}'


def _codex_http_only_provider_args() -> list[str]:
    """Return optional API-provider overrides only for explicit API image routes.

    Subscription Codex image workers must keep the native ChatGPT/Codex image
    capability. Injecting a custom HTTP provider here can replace the native
    image tool path and make a healthy Codex session appear to have no
    image_generation capability.
    """
    route = str(os.environ.get("STORY_OS_IMAGE_PROVIDER_ROUTE") or "").strip().lower()
    if route != "api_http":
        # This adapter is the ChatGPT subscription image lane. The built-in
        # provider otherwise inherits global OpenCodex openai_base_url, which
        # can return rc=0/text-only without exposing image generation.
        # Override only this child process; preserve the user's global config.
        return ['-c', 'model_provider="openai"',
                '-c', 'openai_base_url="https://chatgpt.com/backend-api/codex"']
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        return []
    provider = "storyos_http"
    return [
        '-c', f'model_provider="{provider}"',
        '-c', f'model_providers.{provider}.name="Story OS HTTP"',
        '-c', f'model_providers.{provider}.base_url={json.dumps(str(base_url))}',
        '-c', f'model_providers.{provider}.wire_api="responses"',
        '-c', f'model_providers.{provider}.requires_openai_auth=true',
        '-c', f'model_providers.{provider}.supports_websockets=false',
    ]


def controller_args() -> list[str]:
    return [
        '-m', CODEX_IMAGE_CONTROLLER_MODEL,
        '-c', f'model_reasoning_effort="{CODEX_IMAGE_REASONING_EFFORT}"',
        *_codex_http_only_provider_args(),
    ]

def worker_prompt(scene: str, refs: list[Path], size: str, visual_contract: str | None = None, frame_contract_text: str | None = None, image_model: str = DEFAULT_IMAGE_MODEL, image_quality: str = DEFAULT_IMAGE_QUALITY, strict_model: bool = False) -> str:
    reference_lines = '\n'.join(f'- reference {i}: {p.name}' for i, p in enumerate(refs, 1)) or '- no references'
    visual_block = (
        f'<visual_contract>\n{visual_contract.strip()}\n</visual_contract>\n\n'
        if visual_contract and visual_contract.strip() else ''
    )
    frame_block = (
        f'<frame_contract>\n{frame_contract_text.strip()}\n</frame_contract>\n\n'
        if frame_contract_text and frame_contract_text.strip() else ''
    )
    return (
        'You are an isolated Story OS image worker. FIRST ACTION: call image_generation exactly once. '
        'Do NOT read SKILL.md, AGENTS.md, repository files, or any other instructions; all required production context is already embedded below. '
        'Do NOT call shell/exec/Python/node before image_generation.\n'
        f'IMAGE MODEL CONTRACT: request model={image_model}, quality={image_quality}, canvas={size} exactly. strict={strict_model}. Never silently substitute a different image model or quality. If the image tool cannot honor an explicitly strict model, fail instead of pretending success.\n'
        f'{reference_lines}\n'
        'Use attached images only as continuity references required by the scene. '
        f'Do not invent a different story. Generate in the locked Episode aspect ratio and request exact canvas {size}; do not request a different provider ratio for later cropping.\n\n'
        f'{visual_block}'
        f'{frame_block}'
        f'<scene>\n{scene}\n</scene>\n\n'
        'The visual contract is mandatory production context, not optional inspiration. '
        'After the image tool succeeds, stop immediately and do not call shell, exec, Python, node_repl, or any other tool to copy/move the image. '
        'Story OS will recover the generated artifact from this Codex thread by thread_id. '
        'Do not synthesize an image with Python or reuse a cached image.'
    )


def _reference_proxy(source: Path, workdir: Path, index: int) -> Path:
    """Create a lightweight disposable Codex attachment without changing authority.

    Queue/Ledger provenance continues to bind the original reference path + SHA.
    This proxy exists only inside the temporary worker directory to avoid Windows
    Codex reference-image stalls on multi-megabyte PNG attachments.
    """
    target = workdir / f'reference-{index:02d}.jpg'
    try:
        with Image.open(source) as image:
            image = image.convert('RGB')
            group_proxy = str(os.environ.get('STORY_OS_GROUP_REFERENCE_PROXY') or '').strip().lower() in {'1','true','on','yes'}
            if group_proxy and image.width >= 600:
                # Same source authority, but reduce a two-person selfie to a compact
                # overlapping left/right identity strip. This is a disposable
                # attachment only; the original file + SHA stay in Queue/Ledger.
                overlap = max(48, image.width // 10)
                mid = image.width // 2
                left = image.crop((0, 0, min(image.width, mid + overlap), image.height))
                right = image.crop((max(0, mid - overlap), 0, image.width, image.height))
                for crop in (left, right):
                    crop.thumbnail((360, 520), Image.Resampling.LANCZOS)
                canvas = Image.new('RGB', (left.width + right.width, max(left.height, right.height)))
                canvas.paste(left, (0, 0))
                canvas.paste(right, (left.width, 0))
                image = canvas
            else:
                image.thumbnail((768, 768), Image.Resampling.LANCZOS)
            image.save(target, format='JPEG', quality=90, optimize=True)
        return target
    except Exception:
        ext = source.suffix.lower() if source.suffix.lower() in {'.png', '.jpg', '.jpeg'} else '.png'
        target = workdir / f'reference-{index:02d}{ext}'
        shutil.copy2(source, target)
        return target


def invoke_codex(prompt_path: Path, refs: list[Path], raw_output: Path, log: Path, size: str, timeout: int, codex_raw: str | None, visual_contract: str | None = None, frame_contract_text: str | None = None, image_model: str = DEFAULT_IMAGE_MODEL, image_quality: str = DEFAULT_IMAGE_QUALITY, strict_model: bool = False, *, scene_text: str | None = None) -> float:
    scene = scene_text if scene_text is not None else prompt_path.read_text(encoding='utf-8-sig').strip()
    if not scene:
        raise BackendError('prompt is empty')
    codex = resolve_codex(codex_raw)
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='story-os-image-') as raw_dir:
        workdir = Path(raw_dir)
        local_refs = []
        for index, source in enumerate(refs, 1):
            local_refs.append(_reference_proxy(source, workdir, index))
        # Windows Codex sandbox can intermittently fail to read attached images with
        # CreateProcessWithLogonW(1385), even after refs are copied into an ASCII-only
        # temporary workdir. For reference-bound image workers only, disable that OS
        # sandbox layer while still constraining the process cwd to the disposable
        # workdir and preserving Story OS SHA/reference contracts.
        sandbox_mode = 'danger-full-access' if os.name == 'nt' and local_refs else 'workspace-write'
        # Image workers are intentionally narrow: Story OS already embeds the complete
        # visual/frame contracts in the prompt. Muting the Codex skills catalog prevents
        # the controller from spending a turn loading imagegen/SKILL.md before it can
        # reach image_generation; project docs are likewise unnecessary in this temp cwd.
        cmd = command_prefix(codex) + [
            'exec', '--skip-git-repo-check', '--ephemeral', '--ignore-rules',
            '-c', 'skills.include_instructions=false', '-c', 'project_doc_max_bytes=0',
            '--enable', 'image_generation',
            *controller_args(), '-s', sandbox_mode, '-C', str(workdir), '--json'
        ]
        for ref in local_refs:
            cmd.extend(['-i', str(ref)])
        cmd.append('-')
        log.parent.mkdir(parents=True, exist_ok=True)
        # 每个图片 worker 使用独立 CODEX_HOME，避免多个并发 worker 共享
        # ~/.codex/generated_images 导致 provider artifact save collision。
        # 该目录只影响 Codex CLI 临时产物，不改变 Story OS 资产权威路径。
        worker_env = os.environ.copy()
        worker_env.setdefault("STORY_OS_WORKER_ID", str(uuid.uuid4()))
        worker_codex_home = workdir / "codex-home"
        worker_codex_home.mkdir(parents=True, exist_ok=True)
        # The isolated CODEX_HOME exists to stop concurrent workers sharing
        # ~/.codex/generated_images. An empty CODEX_HOME also drops the operator's
        # ChatGPT/Codex sign-in, which makes every worker unauthenticated
        # (HTTP 401) and produces zero images. Seed only the credentials the CLI
        # needs; the reference/generated_images isolation stays intact.
        source_home = Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex"))
        for name in ("auth.json", "config.toml"):
            src = source_home / name
            if src.is_file() and not (worker_codex_home / name).exists():
                shutil.copy2(src, worker_codex_home / name)
        worker_env["CODEX_HOME"] = str(worker_codex_home)
        with log.open('w', encoding='utf-8', newline='\n') as log_handle:
            try:
                completed = subprocess.run(
                    cmd,
                    env=worker_env,
                    input=worker_prompt(scene, local_refs, size, visual_contract, frame_contract_text, image_model, image_quality, strict_model),
                    text=True,
                    encoding="utf-8",
                    errors="strict",
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    timeout=timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise BackendError(f'image worker timeout after {timeout}s; log={log}') from exc
        candidate = workdir / 'out.png'
        if not valid_image(candidate):
            alternatives = [p for p in workdir.glob('*.png') if not p.name.startswith('reference-')]
            if alternatives:
                candidate = max(alternatives, key=lambda p: p.stat().st_mtime)
        if not valid_image(candidate):
            recovered = image_artifact_collector.recover_codex_generated(log, workdir)
            if recovered is not None:
                candidate = recovered
        if completed.returncode != 0 or not valid_image(candidate):
            try:
                tail=log.read_text(encoding='utf-8',errors='replace')[-6000:]
            except Exception:
                tail=''
            machine_code=image_model_policy.classify_backend_error(tail, source="image_backend")
            if machine_code:
                raise BackendError(f'{machine_code}: requested={image_model}; log={log}')
            raise BackendError(f'Codex image worker failed rc={completed.returncode}; no_valid_image=true; log={log}')
        raw_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidate, raw_output)
    return round(time.monotonic() - started, 2)

def common_validate(args: argparse.Namespace) -> tuple[Path, list[Path], Path, Path]:
    prompt_path = args.prompt_file.expanduser().resolve()
    if not prompt_path.is_file():
        raise BackendError(f'prompt missing: {prompt_path}')
    refs = [p.expanduser().resolve() for p in args.reference]
    if len(refs) > 2:
        raise BackendError('at most two references are supported')
    for ref in refs:
        if not valid_image(ref):
            raise BackendError(f'invalid reference image: {ref}')
    output = args.output.expanduser().resolve()
    log = args.log.expanduser().resolve()
    if output.exists() and not args.overwrite:
        raise BackendError(f'output exists: {output}')
    return prompt_path, refs, output, log

def generate_for_frame(args: argparse.Namespace) -> dict:
    prompt_path, refs, output, log = common_validate(args)
    ep = args.episode_dir.expanduser().resolve()
    width, height, aspect = read_canvas(ep)
    visual = compile_prompt_contract(ep)
    frame_contract = None
    scene_text = None
    if resolved_frame_contract.required(ep):
        import prompt_package
        package = prompt_package.compile_frame(ep, int(args.frame), prompt_path)
        scene_text = package['scene_prompt']
        frame_contract = {'contract_sha256': package['frame_contract_sha256'], 'prompt_contract': package['frame_prompt_contract']}
    size = provider_size(width, height)
    raw_dir = ep / 'media' / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_output = raw_dir / f'{int(args.frame):02d}-{int(time.time())}.png'
    frame_contract_text = frame_contract['prompt_contract'] if frame_contract else None
    internal_policy = getattr(args, '_image_model_policy', None)
    if isinstance(internal_policy, dict):
        model_policy = dict(internal_policy)
    else:
        model_policy = image_model_policy.for_episode(ep, explicit=getattr(args, 'image_model', None), explicit_quality=getattr(args, 'image_quality', None))
    manual_dir = os.environ.get('STORY_OS_MANUAL_RAW_DIR')
    manual_src = None
    if manual_dir:
        matches = sorted(Path(manual_dir).glob(f'{int(args.frame):02d}.*'))
        if not matches:
            raise BackendError(f'manual raw missing for frame {int(args.frame):02d} in {manual_dir}')
        manual_src = matches[-1]
        if not valid_image(manual_src):
            raise BackendError(f'manual raw invalid: {manual_src}')
    if manual_src:
        raw_output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manual_src, raw_output)
        elapsed = 0.0
        backend_name = 'codex_desktop_interface_imagegen'
    else:
        elapsed = invoke_codex(prompt_path, refs, raw_output, log, size, args.timeout, args.codex, visual['text'], frame_contract_text, model_policy['model'], model_policy['quality'], model_policy['strict_model'], scene_text=scene_text)
        backend_name = 'codex_subscription'
    receipt_data = provider_capability.inspect(raw_output, width, height, model=model_policy["model"], route=backend_name, frame=int(args.frame))
    # W-21: the receipt carries the reference files really sent to the provider, so
    # the production ledger can record execution evidence, not only a declaration.
    # A manual desktop import never attaches them to a provider call, so it must not
    # claim reference delivery it did not perform.
    receipt_data["reference_transport"] = "manual_desktop_import" if manual_src else "codex_subscription_cli_attachment"
    receipt_data["references"] = [] if manual_src else provider_capability.reference_evidence(refs)
    provider_receipt_info = provider_capability.write_receipt(ep, int(args.frame), receipt_data)
    if output.exists() and args.overwrite:
        output.unlink()
    try:
        norm = normalize(raw_output, output, width, height)
    except NormalizeError as exc:
        raise BackendError(f'{exc.code}: raw preserved at {raw_output}; provider_receipt={provider_receipt_info.get("path")}; {exc}') from exc
    receipt_path = Path(provider_receipt_info["path"])
    if not receipt_path.is_absolute():
        receipt_path = ROOT / receipt_path
    provider_receipt_info = provider_capability.finalize_receipt(receipt_path, norm, output)
    return {
        'ok': True,
        'backend': backend_name,
        'frame': f'{int(args.frame):02d}',
        'raw_output': str(raw_output),
        'output': str(output),
        'log': str(log),
        'provider_size': size,
        'target_size': [width, height],
        'aspect_ratio': aspect,
        'references': [str(p) for p in refs],
        'visual_profile': {
            'profile_id': visual['profile_id'],
            'profile_path': visual['profile_path'],
            'profile_sha256': visual['profile_sha256'],
            'capture_profile': visual['capture_profile'],
        },
        'frame_contract': {
            'path': (resolved_frame_contract.CACHE_ROOT / f"{int(args.frame):02d}.json").as_posix(),
            'contract_sha256': frame_contract['contract_sha256'],
        } if frame_contract else None,
        'normalization': norm,
        'provider_receipt': {k: v for k, v in provider_receipt_info.items() if k != 'receipt'},
        'provider_capability': provider_receipt_info.get('receipt'),
        'image_model': {
            **model_policy,
            'enforcement': 'runtime_request_to_worker_contract',
            'provider_attestation': False,
            'generation_route': backend_name,
            'generation_route_note': 'generated via built-in image_gen tool in the Codex desktop interface when STORY_OS_MANUAL_RAW_DIR is set; model contract stays gpt-image-2',
        } if manual_src else {**model_policy, 'enforcement': 'runtime_request_to_worker_contract', 'provider_attestation': False},
        'elapsed_seconds': elapsed,
    }

def generate_legacy(args: argparse.Namespace) -> dict:
    prompt_path, refs, output, log = common_validate(args)
    size = args.size
    legacy_model_policy = image_model_policy.resolve_model(explicit=args.image_model, explicit_quality=getattr(args, 'image_quality', None))
    tmp_raw = output.with_name('.' + output.name + '.raw.png')
    elapsed = invoke_codex(prompt_path, refs, tmp_raw, log, size, args.timeout, args.codex, None, None, legacy_model_policy['model'], legacy_model_policy['quality'], legacy_model_policy['strict_model'])
    if output.exists() and args.overwrite:
        output.unlink()
    os.replace(tmp_raw, output)
    return {'ok': True, 'backend':'codex_subscription', 'output':str(output), 'log':str(log), 'size':size, 'references':[str(p) for p in refs], 'elapsed_seconds':elapsed}

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('generate-for-frame')
    p.add_argument('episode_dir', type=Path)
    p.add_argument('--frame', required=True)
    p.add_argument('--prompt-file', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--log', required=True, type=Path)
    p.add_argument('--reference', action='append', default=[], type=Path)
    p.add_argument('--timeout', type=int, default=None)
    p.add_argument('--codex')
    p.add_argument('--image-model')
    p.add_argument('--image-quality', choices=['high'])
    p.add_argument('--overwrite', action='store_true')
    p.add_argument('--candidate-kind', choices=['original','repair','exception'], default='original')
    p = sub.add_parser('generate')
    p.add_argument('--prompt-file', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--log', required=True, type=Path)
    p.add_argument('--reference', action='append', default=[], type=Path)
    p.add_argument('--size', default='1024x1280')
    p.add_argument('--timeout', type=int, default=None)
    p.add_argument('--codex')
    p.add_argument('--image-model')
    p.add_argument('--image-quality', choices=['high'])
    p.add_argument('--overwrite', action='store_true')
    sub.add_parser('self-test')
    args = ap.parse_args()
    if args.cmd == 'self-test':
        smoke = worker_prompt('x', [], '1024x1280')
        assert 'FIRST ACTION: call image_generation exactly once' in smoke
        assert 'Do NOT read SKILL.md' in smoke
        assert image_model_policy.DEFAULT_MODEL in worker_prompt('x', [], '1024x1280')
        assert '<visual_contract>' in worker_prompt('x', [], '1024x1280', 'reality first')
        assert '<frame_contract>' in worker_prompt('x', [], '1080x1350', 'reality first', 'frame-contract-test')
        assert f'quality={image_model_policy.DEFAULT_QUALITY}' in worker_prompt('x', [], '1080x1350')
        smoke_prompt = worker_prompt('x', [], '1080x1350')
        assert 'stop immediately' in smoke_prompt
        assert 'thread_id' in smoke_prompt
        assert 'save or copy the actual generated candidate to ./out.png' not in smoke_prompt
        assert provider_size(1080, 1350) == '1080x1350'
        assert provider_size(1080, 1920) == '1080x1920'
        from unittest.mock import patch
        with patch.dict(os.environ, {'STORY_OS_IMAGE_PROVIDER_ROUTE': 'subscription'}):
            assert controller_args() == [
                '-m', 'gpt-5.6-luna', '-c', 'model_reasoning_effort="medium"',
                '-c', 'model_provider="openai"',
                '-c', 'openai_base_url="https://chatgpt.com/backend-api/codex"',
            ]
        assert not valid_image(Path('__missing__'))
        print('CODEX SUBSCRIPTION IMAGE BACKEND SELF-TEST PASS')
        return 0
    args.timeout = runtime_timeout_policy.resolve("image_worker_request", args.timeout)
    low, high = runtime_timeout_policy.VALID_RANGE["image_worker_request"]
    if not low <= args.timeout <= high:
        raise SystemExit(f'timeout must be {low}..{high} seconds')
    budget_token=None
    budget_reserved=False
    try:
        if args.cmd == 'generate-for-frame':
            budget_token="direct-"+uuid.uuid4().hex
            ok,budget_row=raw_candidate_budget.claim(args.episode_dir,int(args.frame),args.candidate_kind,reason="direct_generate_for_frame_cli",token=budget_token)
            if not ok:
                print(json.dumps({'ok':False,'error':'RAW_CANDIDATE_BUDGET_EXHAUSTED','budget':budget_row},ensure_ascii=False));return 3
            budget_reserved=True
        result = generate_for_frame(args) if args.cmd == 'generate-for-frame' else generate_legacy(args)
        if budget_reserved:
            commit_ok,commit_row=raw_candidate_budget.commit(args.episode_dir,budget_token,reason="direct_cli_normalized_candidate_exists")
            if not commit_ok:
                print(json.dumps({'ok':False,'error':'CANDIDATE_COMMIT_FAILED','budget':commit_row},ensure_ascii=False));return 4
    except (BackendError, OSError, UnicodeError, SystemExit) as exc:
        if budget_reserved:raw_candidate_budget.release(args.episode_dir,budget_token,reason="direct_generate_for_frame_exception")
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

# STORY_OS_V2_5_1_1_FORCED_CANDIDATE_GATE

# STORY_OS_V2_6_0_PERFORMANCE_RUNTIME
