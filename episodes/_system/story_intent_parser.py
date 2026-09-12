#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Story OS Story Intent Parser (Autonomous Production Pipeline Phase 5.1).

Purpose:
    One sentence story request -> Story Intent Contract (machine form).

Boundaries
----------
- Structuring only. No prompt text, no image instruction, no scoring.
- Deterministic rule parser: keyword tables, no model call, no network.
- Nothing is written. A Story Intent is a value, not an Episode asset.
- An unrecognised request fails closed (STORY_INTENT_NO_SIGNAL) instead of being
  silently turned into a default story. World/era signatures that are absent are
  recorded as unspecified with a note, never asserted as fact.

Vocabulary note
---------------
The world / era / theme / genre / experience_type / audience enums are the Visual
Profile Selector input enums (standards/visual_profiles/schema/selector-input.schema.json),
so an intent can be handed to visual_profile_selector without translation. v1
derives genre from the same signals as theme; they may diverge once a dedicated
genre signal exists. A finer subject label (for example "ordinary_people") is kept
in theme_detail, which the Selector does not read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    # Repo convention is script execution (python episodes/_system/x.py). The same
    # module is also runnable as python -m episodes._system.x, which puts the
    # repository root on sys.path instead, so both entry points are kept working.
    sys.path.insert(0, str(_HERE))

import story_json  # noqa: E402
import visual_profile_registry as registry  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_REL = Path("standards/story/schema/story-intent.schema.json")

PARSER_VERSION = "1.0"
SOURCE = "rule_parser"

ERROR_EMPTY = "STORY_INTENT_EMPTY"
ERROR_NO_SIGNAL = "STORY_INTENT_NO_SIGNAL"
ERROR_INVALID = "STORY_INTENT_INVALID"

WORLD_REAL = "real"
WORLD_HISTORICAL_REAL = "historical_real"
WORLD_FICTIONAL = "fictional"

SELECTOR_THEMES = ("daily_life", "work_life", "anomaly_mystery", "folk_life", "travel_life")

# A fictional world is only assumed to be high fantasy when an actual fantasy
# marker is present; otherwise the level stays low and M02 is not selected.
FICTIONAL_TOKENS = (
    "天界", "天庭", "仙界", "天宫", "灵界", "冥界", "阴间", "神仙", "仙女", "仙侠",
    "妖怪", "妖精", "修真", "玄幻", "异世界", "魔法", "天堂", "架空",
    "heaven", "celestial", "immortal", "fantasy",
)
FANTASY_HIGH_TOKENS = (
    "天界", "天庭", "仙界", "天宫", "灵界", "冥界", "阴间", "神仙", "仙女", "仙侠",
    "妖怪", "妖精", "修真", "玄幻", "异世界", "魔法", "天堂",
    "heaven", "celestial", "immortal", "fantasy",
)
HISTORICAL_TOKENS = (
    "古代", "古时", "古装", "古风", "唐宋", "唐朝", "宋朝", "北宋", "南宋", "明朝",
    "清朝", "汉代", "汉朝", "民国", "客栈", "衙门", "秀才", "书生", "镖局", "县令",
)
MODERN_TOKENS = (
    "现代", "当代", "都市", "如今", "手机", "地铁", "公交", "高铁", "外卖", "互联网",
    "写字楼", "公司", "小区", "直播", "便利店", "咖啡馆", "校园", "宿舍", "加班", "工位",
)
LOCATION_JIANGNAN_TOKENS = (
    "江南", "水乡", "乌镇", "周庄", "西塘", "南浔", "苏州", "杭州", "绍兴", "扬州",
    "jiangnan",
)
LOCATION_JIANGNAN = "jiangnan"
IMMERSIVE_TOKENS = (
    "沉浸", "第一人称", "第一视角", "视角", "相册", "我的一天", "一天", "日记", "vlog",
    "记录", "亲历", "随手拍", "跟拍",
)
OBSERVED_TOKENS = ("旁观", "第三人称", "观察者", "路人视角", "旁人视角")
THEME_ANOMALY_TOKENS = ("异常", "诡异", "怪事", "失踪", "灵异", "怪谈", "神秘事件")
THEME_FOLK_TOKENS = ("民俗", "风俗", "庙会", "祠堂", "香火", "祭祀", "祭祖", "节庆", "传说")
THEME_TRAVEL_TOKENS = ("旅行", "旅游", "自驾", "旅途", "出行", "沿途", "远行", "骑行")
THEME_WORK_TOKENS = (
    "上班", "上班族", "工作", "打工人", "职场", "岗位", "值班", "员工", "职员", "同事",
)
THEME_DAILY_TOKENS = ("日常", "一天", "生活", "普通", "百姓", "卖花", "做饭", "买菜", "赶集", "遛弯")
REALISM_MAXIMUM_TOKENS = ("纪实", "真实", "相册", "随手拍", "纪录片", "真实生活", "原相机")
REALISM_HIGH_TOKENS = ("日常", "记录", "生活", "第一人称")
ORDINARY_DETAIL_TOKENS = (
    "普通", "百姓", "市井", "民间", "卖花", "小贩", "摊贩", "手艺人", "匠人", "农家",
)
# Longest first: a matched long label suppresses its own substrings.
CHARACTER_TOKENS = (
    "卖花女子", "卖花姑娘", "卖花女", "普通女子", "普通百姓", "工作人员", "上班族",
    "打工人", "外卖员", "快递员", "女子", "姑娘", "女生", "男生", "小伙", "百姓",
    "工人", "职员", "学生", "老人", "孩子", "老板", "导游", "医生", "教师",
)
CHARACTER_LIMIT = 5


class StoryIntentError(SystemExit):
    """Fail-fast parser error (shares the registry SystemExit convention)."""

    code = ERROR_INVALID

    def __init__(self, message, code=None):
        self.code = code or self.code
        super().__init__(self.code + ": " + str(message))


# --------------------------------------------------------------------------- #
# contract
# --------------------------------------------------------------------------- #

def _root(story_root=None) -> Path:
    return Path(story_root) if story_root else ROOT


def schema_path(story_root=None) -> Path:
    return _root(story_root) / SCHEMA_REL


def load_intent_schema(story_root=None) -> dict:
    path = schema_path(story_root)
    if not path.is_file():
        raise StoryIntentError("story intent schema missing: " + path.as_posix(), ERROR_INVALID)
    data = story_json.read_json(path)
    if not isinstance(data, dict):
        raise StoryIntentError(
            "story intent schema root must be an object: " + path.as_posix(), ERROR_INVALID)
    return data


def validate_intent(intent, story_root=None) -> list:
    """Return schema errors for a Story Intent document ([] means legal)."""
    return registry.validate_json(intent, load_intent_schema(story_root))


# --------------------------------------------------------------------------- #
# rule engine
# --------------------------------------------------------------------------- #

def normalize_text(text) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


def _hits(haystack: str, tokens) -> list:
    return [token for token in tokens if token in haystack]


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse(text, *, story_root=None) -> dict:
    """Parse a natural language story request into a Story Intent Contract.

    Raises StoryIntentError(code=STORY_INTENT_EMPTY) for an empty request and
    StoryIntentError(code=STORY_INTENT_NO_SIGNAL) when nothing in the text is
    recognised. Both are deliberate: a story is never invented from noise.
    """
    source = normalize_text(text)
    if not source:
        raise StoryIntentError("a story request is required", ERROR_EMPTY)
    hay = source.lower()
    signals: list = []
    notes: list = []

    fictional = _hits(hay, FICTIONAL_TOKENS)
    historical = _hits(hay, HISTORICAL_TOKENS)
    modern = _hits(hay, MODERN_TOKENS)

    if fictional:
        world = WORLD_FICTIONAL
        era = "unspecified"
        high = _hits(hay, FANTASY_HIGH_TOKENS)
        fantasy_level = "high" if high else "low"
        signals.append("world=fictional:" + fictional[0])
        if high:
            signals.append("fantasy_level=high:" + high[0])
        else:
            notes.append("fictional world without a fantasy marker: fantasy_level=low")
    elif historical:
        world = WORLD_HISTORICAL_REAL
        era = "ancient"
        fantasy_level = "none"
        signals.append("world=historical_real:" + historical[0])
        signals.append("era=ancient")
    elif modern:
        world = WORLD_REAL
        era = "modern"
        fantasy_level = "none"
        signals.append("world=real:" + modern[0])
        signals.append("era=modern")
    else:
        world = WORLD_REAL
        era = "unspecified"
        fantasy_level = "none"
        notes.append("no world marker: treated as a real world story")

    location_tokens = _hits(hay, LOCATION_JIANGNAN_TOKENS)
    location = LOCATION_JIANGNAN if location_tokens else ""
    if location:
        signals.append("location=jiangnan:" + location_tokens[0])

    observed = _hits(hay, OBSERVED_TOKENS)
    immersive = _hits(hay, IMMERSIVE_TOKENS)
    if observed and not immersive:
        experience_type = "observed"
        signals.append("experience_type=observed:" + observed[0])
    elif immersive:
        experience_type = "immersive_first_person"
        signals.append("experience_type=immersive_first_person:" + immersive[0])
    else:
        experience_type = ""
        notes.append("no capture viewpoint marker: experience_type left unspecified")

    theme = ""
    theme_hits: list = []
    for candidate, tokens in (
        ("anomaly_mystery", THEME_ANOMALY_TOKENS),
        ("folk_life", THEME_FOLK_TOKENS),
        ("travel_life", THEME_TRAVEL_TOKENS),
        ("work_life", THEME_WORK_TOKENS),
        ("daily_life", THEME_DAILY_TOKENS),
    ):
        found = _hits(hay, tokens)
        if found:
            theme, theme_hits = candidate, found
            signals.append("theme=" + candidate + ":" + found[0])
            break
    if not theme:
        notes.append("no theme marker: theme left unspecified")

    theme_detail = None
    if theme == "daily_life" and _hits(hay, ORDINARY_DETAIL_TOKENS):
        theme_detail = "ordinary_people"

    maximum = _hits(hay, REALISM_MAXIMUM_TOKENS)
    if maximum:
        realism = "maximum"
        signals.append("realism=maximum:" + maximum[0])
    elif _hits(hay, REALISM_HIGH_TOKENS):
        realism = "high"
    else:
        realism = ""

    characters: list = []
    for token in CHARACTER_TOKENS:
        if token in hay and not any(token in kept for kept in characters):
            characters.append(token)
        if len(characters) >= CHARACTER_LIMIT:
            break

    matched = bool(
        fictional or historical or modern or location_tokens or immersive or observed
        or theme or maximum or characters
    )
    if not matched:
        raise StoryIntentError(
            "no recognizable story signal in " + repr(source), ERROR_NO_SIGNAL)

    digest = _digest(source)
    intent = {
        "schema_version": 1,
        "parser_version": PARSER_VERSION,
        "intent_id": "intent:" + digest[:16],
        "source_text": source,
        "world": world,
        "era": era,
        "location": location,
        "theme": theme,
        "genre": theme,
        "theme_detail": theme_detail,
        "experience_type": experience_type,
        "fantasy_level": fantasy_level,
        "realism_expectation": realism,
        "characters": characters,
        "audience_expectation": {
            "realism": realism,
            "immersion": "high" if experience_type == "immersive_first_person" else "",
            "fantasy_level": fantasy_level,
        },
        "evidence": {
            "parser_version": PARSER_VERSION,
            "source": SOURCE,
            "inputs_digest": "sha256:" + digest,
            "signals": signals,
            "notes": notes,
        },
    }
    errors = validate_intent(intent, story_root)
    if errors:
        raise StoryIntentError(
            "parser produced a non-conformant intent: " + "; ".join(errors), ERROR_INVALID)
    return intent


def selector_input(intent, *, forced_profile_id=None, episode_context=None) -> dict:
    """Build a Selector Input (Phase 3.2 contract) from a Story Intent.

    Only declared intent fields are forwarded; empty values stay empty so the
    Selector sees the absence of a signal instead of an invented one.
    """
    data = intent if isinstance(intent, dict) else {}
    story_intent = {
        key: (data.get(key) if data.get(key) is not None else "")
        for key in ("world", "era", "location", "theme", "genre", "experience_type")
    }
    payload = {"story_intent": story_intent}
    context = {k: v for k, v in dict(episode_context or {}).items() if v not in (None, "")}
    if context:
        payload["episode_context"] = context
    audience = {
        k: v for k, v in dict(data.get("audience_expectation") or {}).items()
        if v not in (None, "")
    }
    if audience:
        payload["audience_expectation"] = audience
    forced = str(forced_profile_id or "").strip()
    if forced:
        payload["user_override"] = {"forced_profile_id": forced}
    return payload


def self_test() -> None:
    ancient = parse("古代江南普通女子卖花的一天")
    assert ancient["world"] == WORLD_HISTORICAL_REAL and ancient["era"] == "ancient", ancient
    assert ancient["location"] == LOCATION_JIANGNAN, ancient
    assert ancient["theme"] == "daily_life" and ancient["theme_detail"] == "ordinary_people", ancient
    assert ancient["experience_type"] == "immersive_first_person", ancient
    assert validate_intent(ancient, ROOT) == [], validate_intent(ancient, ROOT)
    assert parse("天界普通工作人员的一天")["world"] == WORLD_FICTIONAL
    assert parse("天界普通工作人员的一天")["fantasy_level"] == "high"
    assert parse("现代都市上班族的一天")["world"] == WORLD_REAL
    assert parse(ancient["source_text"])["intent_id"] == ancient["intent_id"]
    assert selector_input(ancient)["story_intent"]["world"] == WORLD_HISTORICAL_REAL
    for bad, code in (("", ERROR_EMPTY), ("   ", ERROR_EMPTY), ("qwerty", ERROR_NO_SIGNAL)):
        try:
            parse(bad)
        except StoryIntentError as exc:
            assert getattr(exc, "code", None) == code, (bad, exc)
        else:
            raise AssertionError("expected a fail-closed parse for " + repr(bad))
    print("STORY INTENT PARSER SELF-TEST PASS")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse", help="parse a one sentence story request")
    p.add_argument("--text")
    p.add_argument("--file")
    p.add_argument("--root", help="repository root override (tests)")
    p.add_argument("--selector-input", action="store_true",
                   help="also print the Visual Profile Selector input")
    sub.add_parser("self-test")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "self-test":
        self_test()
        return 0
    text = args.text
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
    intent = parse(text, story_root=args.root)
    if args.selector_input:
        print(json.dumps(selector_input(intent), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(intent, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
