#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_REL = Path('meta/transport-state.json')
LEDGER_REL = Path('meta/production-ledger.json')
SCHEMA_VERSION = 1
CIRCUIT_THRESHOLD = 3
TECH_CATEGORIES = {'network', 'timeout', 'backend', 'rate_limit', 'no_candidate', 'auth', 'other'}
ACTIVE_FRAME_STATES = {'GENERATING', 'REPAIRING'}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise SystemExit(f'file not found: {path}')
    except json.JSONDecodeError as e:
        raise SystemExit(f'invalid JSON: {path}: {e}')
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


def ensure_state(ep: Path) -> tuple[Path, dict]:
    path = ep / STATE_REL
    if path.exists():
        return path, load_json(path)
    data = {
        'schema_version': SCHEMA_VERSION,
        'created_at': now_iso(),
        'updated_at': now_iso(),
        'note': 'Transport reliability evidence only. This is NOT an episode stage source.',
        'policy': {
            'circuit_threshold': CIRCUIT_THRESHOLD,
            'technical_failures_consume_content_repair': False,
            'technical_retry_must_preserve_request_fingerprint': True,
        },
        'frames': {},
    }
    save_json(path, data)
    return path, data


def ledger_frame(ep: Path, raw_frame: str) -> tuple[str, dict, dict]:
    ledger = load_json(ep / LEDGER_REL)
    try:
        key = f'{int(raw_frame):02d}'
    except ValueError:
        raise SystemExit(f'invalid frame: {raw_frame}')
    frames = ledger.get('frames')
    if not isinstance(frames, dict) or key not in frames:
        raise SystemExit(f'frame {key} not registered in production ledger')
    frame = frames[key]
    if not isinstance(frame, dict):
        raise SystemExit(f'frame {key} ledger entry is invalid')
    return key, frame, ledger


def latest_attempt(frame: dict) -> dict:
    attempts = frame.get('attempts') or []
    if not attempts:
        raise SystemExit('frame has no production attempt; run production_ledger.py begin first')
    attempt = attempts[-1]
    if not isinstance(attempt, dict):
        raise SystemExit('latest production attempt is invalid')
    return attempt


def previous_technical_attempt(frame: dict) -> dict | None:
    attempts = frame.get('attempts') or []
    if len(attempts) < 2:
        return None
    for attempt in reversed(attempts[:-1]):
        if isinstance(attempt, dict) and attempt.get('result') == 'technical_failure':
            return attempt
    return None


def stable_request_digest(attempt: dict) -> str:
    request = attempt.get('request')
    if not isinstance(request, dict):
        raise SystemExit('latest attempt has no request payload')
    encoded = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def frame_state(data: dict, key: str) -> dict:
    frames = data.setdefault('frames', {})
    item = frames.setdefault(key, {
        'consecutive_technical_failures': 0,
        'circuit': 'CLOSED',
        'locked_request_fingerprint': None,
        'events': [],
    })
    return item


def event(item: dict, kind: str, **fields) -> None:
    row = {'at': now_iso(), 'event': kind}
    row.update(fields)
    item.setdefault('events', []).append(row)


def cmd_preflight(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    key, frame, _ = ledger_frame(ep, args.frame)
    if frame.get('status') not in ACTIVE_FRAME_STATES:
        raise SystemExit(f'frame {key} must be GENERATING/REPAIRING before transport preflight; got {frame.get("status")}')
    attempt = latest_attempt(frame)
    fp = attempt.get('request_fingerprint')
    if not isinstance(fp, str) or not fp:
        raise SystemExit('latest production attempt has no request_fingerprint')
    recalculated = stable_request_digest(attempt)
    if recalculated != fp:
        raise SystemExit('production ledger request_fingerprint does not match request payload; aborting transport')

    prev = previous_technical_attempt(frame)
    if prev is not None:
        prev_fp = prev.get('request_fingerprint')
        if prev_fp != fp:
            raise SystemExit(
                f'technical retry changed request fingerprint for frame {key}: previous={prev_fp}, current={fp}. '
                'Do not change prompt/model/capture/references during a technical retry.'
            )

    path, data = ensure_state(ep)
    item = frame_state(data, key)
    if item.get('circuit') == 'OPEN' and not args.reset_circuit:
        raise SystemExit(f'frame {key} transport circuit is OPEN; inspect failures and use --reset-circuit only after fixing transport')
    if args.reset_circuit:
        item['circuit'] = 'CLOSED'
        item['consecutive_technical_failures'] = 0
        event(item, 'circuit_reset', reason=args.reason or 'manual reset')

    locked = item.get('locked_request_fingerprint')
    if locked and locked != fp and item.get('consecutive_technical_failures', 0) > 0:
        raise SystemExit(f'frame {key} fingerprint drift after technical failure: locked={locked}, current={fp}')
    item['locked_request_fingerprint'] = fp
    item['active_attempt_id'] = attempt.get('attempt_id')
    item['last_preflight_at'] = now_iso()
    event(item, 'preflight_passed', attempt_id=attempt.get('attempt_id'), fingerprint=fp)
    data['updated_at'] = now_iso()
    save_json(path, data)
    print(f'{key}: transport preflight PASS fingerprint={fp}')
    return 0


def require_fingerprint(item: dict, fingerprint: str | None) -> str:
    locked = item.get('locked_request_fingerprint')
    if not locked:
        raise SystemExit('no transport preflight recorded for this frame')
    if fingerprint and fingerprint != locked:
        raise SystemExit(f'fingerprint mismatch: expected {locked}, got {fingerprint}')
    return locked


def cmd_failure(args: argparse.Namespace) -> int:
    if args.category not in TECH_CATEGORIES:
        raise SystemExit(f'invalid category: {args.category}')
    ep = resolve_episode(args.episode_dir)
    key, _, _ = ledger_frame(ep, args.frame)
    path, data = ensure_state(ep)
    item = frame_state(data, key)
    fp = require_fingerprint(item, args.fingerprint)
    item['consecutive_technical_failures'] = int(item.get('consecutive_technical_failures', 0)) + 1
    item['last_failure'] = {'at': now_iso(), 'category': args.category, 'message': args.message}
    event(item, 'technical_failure', category=args.category, message=args.message, fingerprint=fp)
    if args.category == 'auth' or item['consecutive_technical_failures'] >= int(data.get('policy', {}).get('circuit_threshold', CIRCUIT_THRESHOLD)):
        item['circuit'] = 'OPEN'
        event(item, 'circuit_opened', reason='auth' if args.category == 'auth' else 'failure_threshold')
    data['updated_at'] = now_iso()
    save_json(path, data)
    print(f'{key}: recorded technical failure #{item["consecutive_technical_failures"]} category={args.category} circuit={item["circuit"]}')
    return 0


def cmd_success(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    key, _, _ = ledger_frame(ep, args.frame)
    path, data = ensure_state(ep)
    item = frame_state(data, key)
    fp = require_fingerprint(item, args.fingerprint)
    item['consecutive_technical_failures'] = 0
    item['circuit'] = 'CLOSED'
    item['last_success_at'] = now_iso()
    event(item, 'transport_success', fingerprint=fp, candidate=args.candidate)
    data['updated_at'] = now_iso()
    save_json(path, data)
    print(f'{key}: transport success recorded; circuit=CLOSED')
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ep = resolve_episode(args.episode_dir)
    path, data = ensure_state(ep)
    if args.frame:
        key = f'{int(args.frame):02d}'
        print(json.dumps(data.get('frames', {}).get(key, {}), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({'path': str(path), 'policy': data.get('policy'), 'frames': data.get('frames', {})}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description='Story OS V1.7 transport reliability guard')
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('preflight', help='lock and verify the latest production request fingerprint')
    p.add_argument('episode_dir')
    p.add_argument('frame')
    p.add_argument('--reset-circuit', action='store_true')
    p.add_argument('--reason')
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser('failure', help='record a technical transport failure')
    p.add_argument('episode_dir')
    p.add_argument('frame')
    p.add_argument('--category', required=True, choices=sorted(TECH_CATEGORIES))
    p.add_argument('--message', required=True)
    p.add_argument('--fingerprint')
    p.set_defaults(func=cmd_failure)

    p = sub.add_parser('success', help='record successful transport')
    p.add_argument('episode_dir')
    p.add_argument('frame')
    p.add_argument('--fingerprint')
    p.add_argument('--candidate')
    p.set_defaults(func=cmd_success)

    p = sub.add_parser('status')
    p.add_argument('episode_dir')
    p.add_argument('--frame')
    p.set_defaults(func=cmd_status)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
