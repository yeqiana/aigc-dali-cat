#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import storyos_config

SYSTEM_DIR = Path(__file__).resolve().parent
ROOT = SYSTEM_DIR.parents[1]
GATES_REL = Path('meta/story-gates.json')
_CONFIG = storyos_config.load_config()
DEFAULT_PROFILE_ID = str(storyos_config.get_path(_CONFIG, 'visual.default_profile_id'))
DEFAULT_PROFILE_PATH = Path(str(storyos_config.get_path(_CONFIG, 'visual.default_profile_path')))


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise SystemExit(f'JSON root must be object: {path}')
    return data


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    tmp.replace(path)


def resolve_episode(raw: str) -> Path:
    ep = Path(raw).resolve()
    if not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    return ep


def default_profile() -> dict:
    path = ROOT / DEFAULT_PROFILE_PATH
    if not path.is_file():
        raise SystemExit(f'default visual profile missing: {DEFAULT_PROFILE_PATH.as_posix()}')
    data = load_json(path)
    return {
        'selection': 'default',
        'profile_id': data.get('profile_id', DEFAULT_PROFILE_ID),
        'profile_name': data.get('profile_name'),
        'profile_path': DEFAULT_PROFILE_PATH.as_posix(),
        'capture_profile': 'auto',
        'override_reason': None,
        'rule': '默认视觉母风格只约束视觉语言；具体年代/设备物理表现优先。',
    }


def list_registered_profiles() -> list[dict]:
    """Enumerate visual profiles registered under standards/visual_profiles."""
    profiles = []
    profile_dir = ROOT / "standards" / "visual_profiles"
    if profile_dir.is_dir():
        for p in sorted(profile_dir.glob("*.json")):
            try:
                data = load_json(p)
            except SystemExit:
                continue
            pid = str(data.get("profile_id") or "").strip()
            if pid:
                profiles.append({
                    "profile_id": pid,
                    "profile_name": str(data.get("profile_name") or "").strip() or p.stem,
                    "profile_path": p.relative_to(ROOT).as_posix(),
                })
    return profiles


def resolve_profile(ep: Path) -> dict:
    resolved = default_profile()
    gates_path = ep / GATES_REL
    if not gates_path.is_file():
        return resolved
    gates = load_json(gates_path)
    cfg = gates.get('visual_profile')
    if not isinstance(cfg, dict):
        return resolved
    mode = str(cfg.get('mode') or 'default').strip().lower()
    if mode == 'default':
        if str(cfg.get('capture_profile') or '').strip():
            resolved['capture_profile'] = str(cfg['capture_profile']).strip()
        return resolved
    if mode != 'override':
        raise SystemExit(f'invalid visual_profile.mode={mode!r}; expected default|override')
    profile_path = str(cfg.get('profile_path') or '').strip()
    profile_id = str(cfg.get('profile_id') or '').strip()
    reason = str(cfg.get('override_reason') or '').strip()
    if not profile_path or not profile_id or not reason:
        raise SystemExit('override visual profile requires profile_id + profile_path + override_reason')
    p = (ROOT / profile_path).resolve()
    try:
        p.relative_to(ROOT.resolve())
    except ValueError:
        raise SystemExit(f'profile_path escapes repository: {profile_path}')
    if not p.is_file():
        raise SystemExit(f'override profile file missing: {profile_path}')
    data = load_json(p) if p.suffix.lower() == '.json' else {}
    return {
        'selection': 'override',
        'profile_id': profile_id,
        'profile_name': data.get('profile_name') if isinstance(data, dict) else None,
        'profile_path': profile_path.replace('\\', '/'),
        'capture_profile': str(cfg.get('capture_profile') or 'auto'),
        'override_reason': reason,
        'rule': '显式单集/系列风格优先；具体年代/设备物理表现仍高于母风格质感。',
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def compile_prompt_contract(ep: Path) -> dict:
    """Compile the resolved visual profile into a compact production contract."""
    profile = resolve_profile(ep)
    p = (ROOT / profile["profile_path"]).resolve()
    data = load_json(p) if p.suffix.lower() == ".json" else {}
    dna = data.get("visual_dna") or {}
    lines = [
        f"profile={profile['profile_id']} | {profile.get('profile_name') or ''}",
        "reality first; the image must still feel like a plausible personal/work record without the anomaly",
        f"ordinary Chinese life density={dna.get('ordinary_chinese_life_density', 'high')}; retain causal incidental clutter",
        f"practical available light={dna.get('practical_available_light', dna.get('available_light_only', True))}; no invented cinematic key/rim lighting",
        f"composition={dna.get('composition', 'unposed_imperfect_personal_record')}",
        f"people={dna.get('people', 'ordinary_unprepared_not_actor_like')}",
        f"color={dna.get('color', 'environment-driven low/medium saturation')}",
        f"texture={dna.get('texture', 'capture-device/scene-caused imperfection only')}",
        f"anomaly={dna.get('anomaly', 'embedded_in_reality_before_spectacle')}",
        "forbid commercial HDR, promo polish, default portrait bokeh, heroic framing and causeless retro/noise effects",
        "capture physics and story era override texture; never fake an old device when the story uses a modern phone",
    ]
    return {
        **profile,
        "profile_sha256": sha256_file(p),
        "text": "\n".join(lines),
    }

def cmd_show(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    result = resolve_profile(ep)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"profile: {result['profile_id']} | {result.get('profile_name')}")
        print(f"selection: {result['selection']}")
        print(f"path: {result['profile_path']}")
        print(f"capture_profile: {result['capture_profile']}")
        if result.get('override_reason'):
            print(f"override_reason: {result['override_reason']}")
        print(result['rule'])
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    profiles = list_registered_profiles()
    if args.json:
        print(json.dumps(profiles, ensure_ascii=False, indent=2))
    else:
        for p in profiles:
            print(f"{p['profile_id']} | {p['profile_name']} | {p['profile_path']}")
    return 0


def cmd_set_default(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    path = ep / GATES_REL
    gates = load_json(path)
    gates['visual_profile'] = {
        'mode': 'default',
        'profile_id': DEFAULT_PROFILE_ID,
        'profile_path': DEFAULT_PROFILE_PATH.as_posix(),
        'capture_profile': args.capture_profile or 'auto',
        'override_reason': None,
    }
    save_json(path, gates)
    print('visual profile set to default M00')
    return 0


def cmd_set_override(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    if not args.reason.strip():
        raise SystemExit('--reason is required for visual profile override')
    if args.profile_path:
        profile_path = Path(args.profile_path)
        if profile_path.is_absolute():
            try:
                rel = profile_path.resolve().relative_to(ROOT.resolve())
            except ValueError:
                raise SystemExit('override profile must be inside repository')
        else:
            rel = profile_path
    else:
        rel = Path('standards/visual_profiles') / f'{args.profile_id}.json'
        if not (ROOT / rel).is_file():
            registered = [p['profile_id'] for p in list_registered_profiles()]
            raise SystemExit(
                f'profile file missing for profile_id={args.profile_id!r}: {rel.as_posix()} '
                f'(registered profiles: {", ".join(registered) or "none"})'
            )
    p = ROOT / rel
    if not p.is_file():
        raise SystemExit(f'profile file missing: {rel.as_posix()}')
    gates_path = ep / GATES_REL
    gates = load_json(gates_path)
    gates['visual_profile'] = {
        'mode': 'override',
        'profile_id': args.profile_id,
        'profile_path': rel.as_posix(),
        'capture_profile': args.capture_profile or 'auto',
        'override_reason': args.reason.strip(),
    }
    save_json(gates_path, gates)
    print(f'visual profile override set: {args.profile_id}')
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description='Story OS V1.8 visual profile resolver')
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('show'); p.add_argument('episode_dir'); p.add_argument('--json', action='store_true'); p.set_defaults(func=cmd_show)
    p = sub.add_parser('list'); p.add_argument('--json', action='store_true'); p.set_defaults(func=cmd_list)
    p = sub.add_parser('set-default'); p.add_argument('episode_dir'); p.add_argument('--capture-profile'); p.set_defaults(func=cmd_set_default)
    p = sub.add_parser('set-override'); p.add_argument('episode_dir'); p.add_argument('--profile-id', required=True); p.add_argument('--profile-path'); p.add_argument('--reason', required=True); p.add_argument('--capture-profile'); p.set_defaults(func=cmd_set_override)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
