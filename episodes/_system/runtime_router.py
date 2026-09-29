#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
import json
import os
import shutil
from pathlib import Path

from story_os_contract import story_os_version
import storyos_config
import workspace_provider
import production_mode

ROOT = Path(__file__).resolve().parents[2]
_CONFIG = storyos_config.load_config()
CONTRACT = ROOT / str(storyos_config.get_path(_CONFIG, 'paths.runtime_contract'))
VALID = {'CODEX', 'WORK', 'WEB'}
VALID_IMAGE_RUNTIMES = {'CODEX', 'PRODUCT_RUNTIME', 'AUTO'}
VALID_REVIEW_RUNTIMES = {'CODEX', 'WORK', 'AUTO'}

_WEBCODEX_TRUE = {'1', 'true', 'yes', 'on'}
_WEBCODEX_FALSE = {'0', 'false', 'no', 'off'}


def preferred_runtime() -> str:
    # Compatibility API. The production mode is now the canonical whole-chain
    # selector; the old runtime field remains validated during migration.
    return production_mode.resolve(_CONFIG)['effective_runtime']


def image_execution_runtime() -> tuple[str, str]:
    override = os.getenv('STORY_OS_IMAGE_EXECUTOR', '').strip().upper()
    if override:
        if override not in VALID_IMAGE_RUNTIMES:
            raise ValueError(f'invalid STORY_OS_IMAGE_EXECUTOR: {override!r}')
        return override, 'STORY_OS_IMAGE_EXECUTOR override'
    legacy_override = os.getenv('STORY_OS_IMAGE_RUNTIME', '').strip().upper()
    if legacy_override:
        if legacy_override not in VALID_IMAGE_RUNTIMES:
            raise ValueError(f'invalid STORY_OS_IMAGE_RUNTIME: {legacy_override!r}')
        return legacy_override, 'STORY_OS_IMAGE_RUNTIME legacy compatibility override'
    configured = str(storyos_config.get_path(_CONFIG, 'execution.image.executor')
                     or storyos_config.get_path(_CONFIG, 'runtime.image_execution_runtime') or 'AUTO').strip().upper()
    if configured not in VALID_IMAGE_RUNTIMES:
        raise ValueError(f'invalid execution.image.executor: {configured!r}')
    source = ('config/storyos.yaml#execution.image.executor'
              if storyos_config.get_path(_CONFIG, 'execution.image.executor') is not None
              else 'config/storyos.yaml#runtime.image_execution_runtime (legacy compatibility)')
    return configured, source


def text_review_runtime() -> tuple[str, str]:
    configured = str(storyos_config.get_path(_CONFIG, 'runtime.review.text.runtime') or 'WORK').strip().upper()
    if configured not in {'WORK'}:
        raise ValueError(f'invalid runtime.review.text.runtime: {configured!r}')
    return configured, 'config runtime.review.text.runtime'


def vision_review_runtime() -> tuple[str, str]:
    override = os.getenv('STORY_OS_VISION_EXECUTOR', '').strip().upper()
    if override:
        if override not in VALID_REVIEW_RUNTIMES:
            raise ValueError(f'invalid STORY_OS_VISION_EXECUTOR: {override!r}')
        return override, 'STORY_OS_VISION_EXECUTOR override'
    legacy_override = os.getenv('STORY_OS_VISION_RUNTIME', '').strip().upper()
    if legacy_override:
        if legacy_override not in VALID_REVIEW_RUNTIMES:
            raise ValueError(f'invalid STORY_OS_VISION_RUNTIME: {legacy_override!r}')
        return legacy_override, 'STORY_OS_VISION_RUNTIME legacy compatibility override'
    configured = str(storyos_config.get_path(_CONFIG, 'execution.vision_review.executor')
                     or storyos_config.get_path(_CONFIG, 'runtime.review.vision.runtime') or 'CODEX').strip().upper()
    if configured not in VALID_REVIEW_RUNTIMES:
        raise ValueError(f'invalid execution.vision_review.executor: {configured!r}')
    source = ('config/storyos.yaml#execution.vision_review.executor'
              if storyos_config.get_path(_CONFIG, 'execution.vision_review.executor') is not None
              else 'config/storyos.yaml#runtime.review.vision.runtime (legacy compatibility)')
    return configured, source


def governance_review_runtime() -> tuple[str, str]:
    configured = str(storyos_config.get_path(_CONFIG, 'runtime.review.governance.runtime') or 'WORK').strip().upper()
    if configured not in {'WORK'}:
        raise ValueError(f'invalid runtime.review.governance.runtime: {configured!r}')
    return configured, 'config runtime.review.governance.runtime'


def vision_review_model() -> str:
    value = str(storyos_config.get_path(_CONFIG, 'runtime.review.vision.model') or '').strip()
    if not value:
        raise ValueError('runtime.review.vision.model is required')
    return value


def vision_review_effort(kind: str = 'default') -> str:
    suffix = {'fast': 'fast', 'final': 'final'}.get(str(kind).lower(), 'default')
    value = str(storyos_config.get_path(_CONFIG, f'runtime.review.vision.reasoning_effort_{suffix}') or '').strip().lower()
    if value not in {'low', 'medium', 'high'}:
        raise ValueError(f'invalid runtime.review.vision.reasoning_effort_{suffix}: {value!r}')
    return value


def vision_review_max_inflight_final() -> int:
    value = storyos_config.get_path(_CONFIG, 'runtime.review.vision.max_inflight_final')
    if type(value) is not int or not 1 <= value <= 6:
        raise ValueError('runtime.review.vision.max_inflight_final must be an int between 1 and 6')
    return value


def _codex_cli_path() -> str | None:
    return shutil.which('codex') or shutil.which('codex.exe') or shutil.which('codex.cmd')


def webcodex_available() -> tuple[bool, str]:
    """Detect the host-managed WebCodex workspace from runtime evidence, not config alone."""
    forced = os.getenv('STORY_OS_WEBCODEX_AVAILABLE', '').strip().lower()
    if forced in _WEBCODEX_TRUE:
        return True, 'STORY_OS_WEBCODEX_AVAILABLE override'
    if forced in _WEBCODEX_FALSE:
        return False, 'STORY_OS_WEBCODEX_AVAILABLE override'
    service_root = os.getenv('WEBCODEX_SERVICE_ROOT', '').strip()
    if service_root and Path(service_root).expanduser().is_dir():
        return True, 'WEBCODEX_SERVICE_ROOT detected'
    env_file = os.getenv('WEBCODEX_ENV_FILE', '').strip()
    if env_file and Path(env_file).expanduser().is_file():
        return True, 'WEBCODEX_ENV_FILE detected'
    return False, 'no WebCodex host environment detected'


def _runtime_with_reason() -> tuple[str, str]:
    resolution = production_mode.resolve(_CONFIG)
    source = resolution['source']
    if source.startswith('env:STORY_OS_RUNTIME'):
        return resolution['effective_runtime'], 'STORY_OS_RUNTIME override'
    if source.startswith('env:STORY_OS_PRODUCTION_MODE'):
        return resolution['effective_runtime'], 'STORY_OS_PRODUCTION_MODE override'
    return resolution['effective_runtime'], f"config production.mode={resolution['configured_mode']}"


def _effective_runtime() -> str:
    return _runtime_with_reason()[0]


def local_codex_allowed(*, explicit: bool = False) -> bool:
    """Return whether general non-image/non-vision work may launch local codex.exe.

    CODEX image/vision capability never grants Codex Story, PREIMAGE, governance,
    release-authority or full-auto ownership.
    """
    if _effective_runtime() == 'CODEX':
        return True
    return bool(explicit)


def local_codex_image_allowed(*, explicit: bool = False) -> bool:
    if explicit:
        return True
    image_runtime, _ = image_execution_runtime()
    if image_runtime == 'CODEX':
        return True
    return image_runtime == 'AUTO' and _effective_runtime() == 'CODEX'


def local_codex_vision_allowed(*, explicit: bool = False) -> bool:
    if explicit:
        return True
    review_runtime, _ = vision_review_runtime()
    if review_runtime == 'CODEX':
        return True
    return review_runtime == 'AUTO' and _effective_runtime() == 'CODEX'


def capabilities() -> dict:
    override = os.getenv('STORY_OS_RUNTIME', '').strip().upper()
    codex = _codex_cli_path()
    preferred = preferred_runtime()
    effective, effective_reason = _runtime_with_reason()
    webcodex_ok, webcodex_reason = webcodex_available()
    image_runtime, image_runtime_reason = image_execution_runtime()
    text_runtime, text_runtime_reason = text_review_runtime()
    vision_runtime, vision_runtime_reason = vision_review_runtime()
    governance_runtime, governance_runtime_reason = governance_review_runtime()
    workspace = workspace_provider.current()
    mode = production_mode.resolve(_CONFIG)
    return {
        'story_os_version': story_os_version(),
        'configured_production_mode': mode['configured_mode'],
        'effective_production_mode': mode['effective_mode'],
        'production_mode_source': mode['source'],
        'production_mode_override': mode['production_mode_override'],
        'legacy_runtime_override': mode['legacy_runtime_override'],
        'runtime_override': override if override in VALID else None,
        'preferred_runtime': preferred,
        'effective_runtime': effective,
        'effective_runtime_reason': effective_reason,
        'webcodex_detected': webcodex_ok,
        'webcodex_detection_reason': webcodex_reason,
        'codex_fallback_active': effective == 'CODEX' and 'fallback' in effective_reason.lower(),
        'repository_filesystem': ROOT.is_dir(),
        'repository_writable': os.access(ROOT, os.W_OK),
        'codex_cli': codex,
        'codex_cli_installed': bool(codex),
        'local_codex_spawn_allowed': effective == 'CODEX',
        'image_execution_runtime': image_runtime,
        'image_execution_runtime_reason': image_runtime_reason,
        'codex_image_controller_model': storyos_config.get_path(_CONFIG, 'runtime.codex_image_controller_model'),
        'codex_image_reasoning_effort': storyos_config.get_path(_CONFIG, 'runtime.codex_image_reasoning_effort'),
        'local_codex_image_spawn_allowed': bool(codex) and local_codex_image_allowed(),
        'codex_subscription_image_eligible': bool(codex) and local_codex_image_allowed(),
        'text_review_runtime': text_runtime,
        'text_review_runtime_reason': text_runtime_reason,
        'vision_review_runtime': vision_runtime,
        'vision_review_runtime_reason': vision_runtime_reason,
        'vision_review_model': vision_review_model(),
        'governance_review_runtime': governance_runtime,
        'governance_review_runtime_reason': governance_runtime_reason,
        'workspace_provider': workspace.provider_id,
        'workspace_transport': workspace.transport,
        'workspace_execution_mode': workspace.execution_mode,
        'workspace_host_managed': workspace.host_managed,
        'model_usage_telemetry': workspace.usage_telemetry,
        'local_codex_vision_spawn_allowed': bool(codex) and local_codex_vision_allowed(),
        'product_runtime_host_required': effective in {'WORK', 'WEB'},
        'product_runtime_image_host_required': effective in {'WORK', 'WEB'} and image_runtime in {'PRODUCT_RUNTIME', 'AUTO'},
        'automatic_runtime_fallback': False,
        'note': 'production.mode selects the whole-chain mode. COLLABORATIVE remains WORK when the host is unavailable; switch to CODEX_MANAGED only by explicit config/env. STORY_OS_RUNTIME is a legacy low-level override.',
    }


def detect() -> tuple[str, str]:
    return _runtime_with_reason()


def capability_route_resolve(request, **kwargs) -> dict:
    """Resolve an advisory task route; Runtime DAG/Scheduler still owns dispatch."""
    import capability_router
    return capability_router.resolve(request, **kwargs)


def capability_route_shadow(request, **kwargs) -> dict:
    """Record a task-level shadow proposal without changing the legacy route."""
    import capability_router
    return capability_router.observe_shadow(request, **kwargs)


def capability_route_production(request, **kwargs) -> dict:
    """Return a guarded task-level route decision; never dispatch or execute it."""
    import capability_router
    return capability_router.resolve_effective_route(request, **kwargs)


def capability_route_record_outcome(provider: str, model: str | None, *,
                                    successful: bool, failure_type: str | None = None,
                                    source: str = "execution_telemetry", reason: str = "",
                                    observed_at=None) -> dict:
    """Refresh advisory TTL health from existing deterministic execution evidence."""
    import capability_router
    return capability_router.record_execution_outcome(
        capability_router.process_health_cache(), provider, model, successful=successful,
        failure_type=failure_type, source=source, reason=reason, observed_at=observed_at).to_dict()


def capability_router_config() -> dict:
    """Expose validated P4 task routing flags without changing global runtime selection."""
    import capability_router
    return capability_router.effective_router_config()

def main() -> int:
    ap = argparse.ArgumentParser(description=f'Story OS V{story_os_version()} runtime router')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('detect'); p.add_argument('--json', action='store_true')
    sub.add_parser('capabilities')
    sub.add_parser('contract')
    p = sub.add_parser('show'); p.add_argument('runtime', choices=sorted(VALID))
    args = ap.parse_args()
    if args.cmd == 'detect':
        runtime, reason = detect()
        if args.json:
            print(json.dumps({'runtime': runtime, 'reason': reason, 'capabilities': capabilities()}, ensure_ascii=False, indent=2))
        else:
            print(runtime)
        return 0
    if args.cmd == 'capabilities':
        print(json.dumps(capabilities(), ensure_ascii=False, indent=2)); return 0
    if args.cmd == 'contract':
        print(CONTRACT.read_text(encoding='utf-8')); return 0
    print((ROOT / 'runtimes' / f'{args.runtime}.md').read_text(encoding='utf-8'))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
