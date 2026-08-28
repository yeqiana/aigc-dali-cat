#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

MAX_CAPTION_CHARS = 48
AI_PATTERNS = [
    (re.compile(r'不是.{0,24}而是'), '“不是……而是……”句式'),
    (re.compile(r'每次.{0,24}都会'), '“每次……都会……”句式'),
    (re.compile(r'直到.{0,24}才'), '“直到……才……”句式'),
    (re.compile(r'这证明|这意味着'), '作者总结式表达'),
    (re.compile(r'更怪的是|更可怕的是|更诡异的是'), '公式化升级连接词'),
]
PREFIX_PATTERNS = ['我发现', '我看到', '更怪的是', '更可怕的是', '直到这时', '后来我才', '这证明', '这意味着']


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')


def parse_scalar(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return ''
    if raw[0:1] in {'"', "'"} and raw[-1:] == raw[0:1]:
        body = raw[1:-1]
        if raw[0] == '"':
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return body
        return body.replace("''", "'")
    return raw


def parse_simple_subtitles_yaml(path: Path) -> dict:
    text = path.read_text(encoding='utf-8')
    section = None
    frames: dict[int, str] = {}
    voice: dict[str, str] = {}
    silent_frames: list[int] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if not line.startswith((' ', '\t')) and stripped.endswith(':'):
            section = stripped[:-1]
            continue
        if not line.startswith((' ', '\t')) and stripped.startswith('silent_frames:'):
            section = None
            m = re.search(r'\[(.*?)\]', stripped)
            if m:
                for token in m.group(1).split(','):
                    token = token.strip()
                    if token.isdigit():
                        silent_frames.append(int(token))
            continue
        if section == 'frames':
            m = re.match(r'\s*(\d+)\s*:\s*(.*)$', line)
            if m:
                frames[int(m.group(1))] = parse_scalar(m.group(2))
        elif section == 'voice_card':
            m = re.match(r'\s*([A-Za-z0-9_]+)\s*:\s*(.*)$', line)
            if m:
                voice[m.group(1)] = parse_scalar(m.group(2))
    return {'frames': frames, 'voice_card': voice, 'silent_frames': sorted(set(silent_frames)), 'raw_text': text}


def captions_from_text(path: Path) -> dict:
    lines = []
    for line in path.read_text(encoding='utf-8').splitlines():
        value = line.strip()
        if value:
            lines.append(value)
    return {'frames': {i + 1: value for i, value in enumerate(lines)}, 'voice_card': {}, 'silent_frames': [], 'raw_text': '\n'.join(lines)}


def discover_input(ep: Path) -> Path:
    candidates = [
        ep / 'meta/subtitles.yaml',
        ep / 'meta/subtitles.yml',
        ep / 'subtitles.yaml',
        ep / 'subtitles.yml',
        ep / 'docs/subtitles.yaml',
        ep / 'docs/subtitles.yml',
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise SystemExit('no subtitle file discovered; pass --file explicitly')


def split_forbidden_terms(value: str) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in re.split(r'[,，、;/；\s]+', value) if len(x.strip()) >= 2]


def sentence_prefix(text: str) -> str | None:
    for prefix in PREFIX_PATTERNS:
        if text.startswith(prefix):
            return prefix
    return None


def audit(data: dict, source: Path) -> dict:
    frames: dict[int, str] = data['frames']
    silent = set(data.get('silent_frames') or [])
    voice = data.get('voice_card') or {}
    hard: list[dict] = []
    warnings: list[dict] = []

    ordered = sorted(frames.items())
    for number, caption in ordered:
        caption = caption.strip()
        if not caption and number not in silent:
            hard.append({'code': 'EMPTY_CAPTION_NOT_SILENT', 'frame': number, 'message': '字幕为空但未登记为 silent frame'})
            continue
        if len(caption) > MAX_CAPTION_CHARS:
            hard.append({'code': 'CAPTION_TOO_LONG', 'frame': number, 'chars': len(caption), 'message': f'字幕超过 {MAX_CAPTION_CHARS} 字'})
        for pattern, label in AI_PATTERNS:
            if pattern.search(caption):
                warnings.append({'code': 'AI_PHRASE', 'frame': number, 'message': label, 'text': caption})

    seen: dict[str, int] = {}
    for number, caption in ordered:
        norm = re.sub(r'\s+', '', caption)
        if not norm:
            continue
        if norm in seen:
            warnings.append({'code': 'DUPLICATE_CAPTION', 'frame': number, 'previous_frame': seen[norm], 'message': '字幕与前帧完全重复'})
        else:
            seen[norm] = number

    nonempty = [(n, c.strip()) for n, c in ordered if c.strip()]
    for i in range(len(nonempty) - 2):
        window = nonempty[i:i + 3]
        prefixes = [sentence_prefix(c) for _, c in window]
        if prefixes[0] and prefixes[0] == prefixes[1] == prefixes[2]:
            warnings.append({'code': 'REPEATED_PREFIX_3', 'frames': [n for n, _ in window], 'message': f'连续三帧都以“{prefixes[0]}”开头'})
        lengths = [len(c) for _, c in window]
        if max(lengths) - min(lengths) <= 2 and min(lengths) >= 8:
            warnings.append({'code': 'UNIFORM_LENGTH_3', 'frames': [n for n, _ in window], 'message': '连续三帧句长过于整齐，像批量生成'})

    if len(nonempty) >= 5:
        lengths = [len(c) for _, c in nonempty]
        mean = statistics.mean(lengths)
        if mean > 0:
            cv = statistics.pstdev(lengths) / mean
            if cv < 0.16:
                warnings.append({'code': 'LOW_LENGTH_VARIANCE', 'value': round(cv, 3), 'message': '整篇字幕句长变化偏小，建议增加短句/停顿/改口'})

    forbidden = split_forbidden_terms(str(voice.get('forbidden_technical_terms', '')))
    for term in forbidden:
        hits = [number for number, caption in ordered if term in caption]
        if hits:
            hard.append({'code': 'FORBIDDEN_TECH_TERM', 'term': term, 'frames': hits, 'message': '人物声音卡明确禁止该技术词'})

    raw = data.get('raw_text', '')
    if 'voice_card:' in raw:
        required_voice = ['person', 'role', 'education_and_knowledge_boundary', 'recording_reason', 'knows_now', 'does_not_know', 'stress_language', 'fear_language_change']
        missing = [key for key in required_voice if not str(voice.get(key, '')).strip()]
        if missing:
            warnings.append({'code': 'VOICE_CARD_INCOMPLETE', 'fields': missing, 'message': '声音卡关键字段未填写完整'})

    return {
        'schema_version': 1,
        'audited_at': now_iso(),
        'source': str(source),
        'caption_count': len(nonempty),
        'silent_frames': sorted(silent),
        'hard_errors': hard,
        'warnings': warnings,
        'summary': {'hard_error_count': len(hard), 'warning_count': len(warnings), 'passed': len(hard) == 0},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='Story OS V1.7 human-caption and AI-tone audit')
    ap.add_argument('episode_dir', nargs='?', help='episode directory; used for discovery/output')
    ap.add_argument('--file', help='subtitle YAML or plain text file')
    ap.add_argument('--report', help='output JSON report path')
    ap.add_argument('--strict-warnings', action='store_true', help='return non-zero when warnings exist')
    args = ap.parse_args()

    ep = Path(args.episode_dir).resolve() if args.episode_dir else None
    if ep is not None and not ep.is_dir():
        raise SystemExit(f'episode directory not found: {ep}')
    source = Path(args.file).resolve() if args.file else discover_input(ep) if ep else None
    if source is None or not source.is_file():
        raise SystemExit(f'input file not found: {source}')

    if source.suffix.lower() in {'.yaml', '.yml'}:
        data = parse_simple_subtitles_yaml(source)
    else:
        data = captions_from_text(source)
    report = audit(data, source)

    if args.report:
        out = Path(args.report).resolve()
    elif ep:
        out = ep / 'meta/text-audit.json'
    else:
        out = source.with_suffix(source.suffix + '.audit.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(f'Text audit: hard={report["summary"]["hard_error_count"]}, warnings={report["summary"]["warning_count"]}')
    print(f'Report: {out}')
    for item in report['hard_errors'][:10]:
        print(f'HARD {item.get("code")}: {item.get("message")}')
    for item in report['warnings'][:10]:
        print(f'WARN {item.get("code")}: {item.get("message")}')
    if report['hard_errors']:
        return 2
    if args.strict_warnings and report['warnings']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
