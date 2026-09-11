#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Story Lock -> feature token lexicon (MVP).

Story DNA only structures a story; it never scores it. A token is emitted only
when one of its keywords literally occurs in the Story Lock inside the scope
that owns the field. No keyword -> empty value, never a guessed value.

The lexicon is data, not a rule engine. Extending extraction means adding rows
here (plus a test); it must never mean adding an opaque score.
"""
from __future__ import annotations

RULE_VERSION = "1"

SCOPE_WHOLE = "whole"
SCOPE_STORY = "story"
SCOPE_CONTRACT = "contract"
SCOPE_VISUAL = "visual"
SCOPE_ANTI = "anti"
SCOPE_META = "meta"

# Section-scope predicates: a unit belongs to a scope when its heading contains
# one of these markers.
SCOPE_HEADINGS: dict[str, tuple[str, ...]] = {
    SCOPE_STORY: ("一句话故事", "正式剧情", "完整故事", "核心阅读问题", "高潮要求"),
    SCOPE_CONTRACT: ("story contract", "contract", "契约", "核心限制", "唯一异常", "异常机制", "认知升级", "不可替代"),
    SCOPE_VISUAL: ("视觉", "采集", "设备", "画幅", "摄影", "节奏", "传播核"),
    SCOPE_ANTI: ("反同质化", "同质化", "差异"),
}

# field -> {"scope": <scope>, "rules": [(token, (keyword, ...)), ...]}
FIELD_RULES: dict[tuple[str, str], dict] = {
    # setting ---------------------------------------------------------------
    ("setting", "location"): {"scope": SCOPE_WHOLE, "rules": (
        ("valley_area", ("山谷", "峡谷", "谷地")),
        ("mountain_area", ("山坡", "山脊", "山区", "山地", "高山", "垭口", "雪山", "半山腰")),
        ("mountain_road", ("山路", "盘山", "停车带", "观景", "公路", "国道")),
        ("rural_village", ("村落", "村子", "村庄", "村里", "农家", "院子", "土路")),
        ("county_town", ("县城", "县镇", "小镇", "镇")),
        ("lodging_room", ("民宿", "房间", "屋内", "室内", "落地窗", "屋里")),
        ("industrial_site", ("玻璃厂", "工厂", "车间", "办公室", "厂房", "旧厂")),
        ("urban_area", ("城市", "街道", "地铁", "公寓")),
    )},
    ("setting", "environment"): {"scope": SCOPE_WHOLE, "rules": (
        ("mountain_environment", ("山", "坡", "岩", "垭口")),
        ("valley_environment", ("山谷", "峡谷", "谷底")),
        ("low_cloud_environment", ("低云", "云海", "云雾", "云层")),
        ("fog_environment", ("雾", "能见度")),
        ("rain_environment", ("雨",)),
        ("night_environment", ("夜", "天黑", "夜间", "晚上")),
        ("snow_environment", ("雪", "失温", "高寒")),
        ("water_environment", ("河水", "湖水", "河流", "湖泊")),
        ("forest_environment", ("树林", "林子", "密林")),
        ("rural_environment", ("村落", "农田", "牲畜", "农家")),
    )},
    ("setting", "time_period"): {"scope": SCOPE_WHOLE, "rules": (
        ("modern", ("当代", "现代", "2023", "2024", "2022", "2021")),
        ("period_2000s", ("2000 年代", "2000年代", "2008", "2007", "2009", "旧数码")),
    )},
    ("setting", "social_context"): {"scope": SCOPE_WHOLE, "rules": (
        ("self_drive_travel", ("自驾", "旅行", "川西", "返程", "旅行素材")),
        ("couple_travel", ("情侣", "女友", "男友")),
        ("factory_clearance", ("清厂", "清仓", "估价", "待拆")),
        ("hiking", ("徒步", "登山", "穿越", "鳌太", "下撤")),
        ("wedding", ("婚礼",)),
    )},
    # relationship ----------------------------------------------------------
    ("relationship", "protagonist"): {"scope": SCOPE_WHOLE, "rules": (
        ("first_person_narrator", ("第一人称", "记录者", "主记录者")),
        ("male_narrator", ("男主", "男友", "P01")),
        ("female_narrator", ("女主", "女友为", "P02 女友")),
    )},
    ("relationship", "companion"): {"scope": SCOPE_WHOLE, "rules": (
        ("companion_present", ("女友", "男友", "队友", "父亲", "女儿", "同伴", "孩子")),
    )},
    ("relationship", "relationship_type"): {"scope": SCOPE_WHOLE, "rules": (
        ("romantic_partner", ("情侣", "男友", "女友")),
        ("family_relation", ("父亲", "女儿", "母亲", "家人", "父子", "父女")),
        ("friend_relation", ("朋友", "队友", "同伴", "工友")),
    )},
    # character -------------------------------------------------------------
    ("character", "protagonist_profile"): {"scope": SCOPE_WHOLE, "rules": (
        ("ordinary_young_adult", ("普通", "年轻人", "二十多", "24 岁", "20 岁", "普通情侣")),
    )},
    ("character", "ordinary_level"): {"scope": SCOPE_WHOLE, "rules": (
        ("high", ("普通", "普通年轻人", "普通情侣", "普通人")),
    )},
    ("character", "motivation"): {"scope": SCOPE_WHOLE, "rules": (
        ("casual_travel_record", ("拍风景", "旅行素材", "旅行记录", "补一点", "记录旅行")),
        ("prove_sighting", ("求证", "证明", "没看错", "想确认", "发给朋友")),
        ("family_financial_need", ("手术费", "筹钱", "筹手术", "定金")),
    )},
    # anomaly ---------------------------------------------------------------
    ("anomaly", "anomaly_type"): {"scope": SCOPE_CONTRACT, "rules": (
        ("spatial_overlap_anomaly", ("局部重叠", "同一现实空间", "另一个仍有人", "两个有人正常生活", "空间发生局部")),
        ("scale_mapping_anomaly", ("尺度映射", "容器", "映射并控制", "瓶体")),
        ("perception_distortion_anomaly", ("失温", "错误感知", "感知重组", "缺氧")),
        ("future_recording_anomaly", ("未来影像", "未来录像", "未来记录")),
    )},
    ("anomaly", "anomaly_mechanism"): {"scope": SCOPE_CONTRACT, "rules": (
        ("environment_condition_triggered", ("某些天气", "连续降雨", "低云", "短暂时刻", "降温", "潮湿")),
        ("device_mediated", ("无人机", "图传", "缓存画面", "定位漂移")),
        ("object_mediated", ("玻璃瓶", "瓶体", "底座刻线", "水泥底座")),
        ("space_overlap_mechanism", ("局部重叠", "与另一个仍有人", "另一边的人")),
    )},
    ("anomaly", "anomaly_visibility"): {"scope": SCOPE_CONTRACT, "rules": (
        ("partial_local", ("局部", "短暂", "一块", "半圆")),
        ("full_scene", ("完整社会", "整片", "一整片")),
    )},
    ("anomaly", "escalation_pattern"): {"scope": SCOPE_CONTRACT, "rules": (
        ("escalating_confirmation", ("逐步", "越来越", "放大", "再翻", "多看", "超过线")),
        ("escalating_danger", ("失联", "危险", "困住")),
    )},
    # emotion ---------------------------------------------------------------
    ("emotion", "primary_emotion"): {"scope": SCOPE_STORY, "rules": (
        ("unease", ("不安", "奇怪", "安静", "怪异", "不对劲", "警惕")),
        ("fear", ("害怕", "恐惧", "尖叫", "吓", "失联")),
        ("curiosity", ("好奇", "求证", "想确认", "想看清")),
    )},
    ("emotion", "secondary_emotion"): {"scope": SCOPE_STORY, "rules": (
        ("curiosity", ("好奇", "求证", "想确认", "想看")),
        ("protectiveness", ("保护", "抱走", "别拍")),
        ("regret", ("后悔", "遗憾")),
    )},
    ("emotion", "audience_feeling"): {"scope": SCOPE_STORY, "rules": (
        ("uncanny_everyday", ("太正常", "日常", "普通生活", "不该出现", "正常生活", "太普通")),
    )},
    # narrative -------------------------------------------------------------
    ("narrative", "hook_type"): {"scope": SCOPE_STORY, "rules": (
        ("observational_witness_hook", ("看见", "目击", "拍到", "灯队", "屏幕里")),
        ("active_choice_hook", ("主动", "决定", "选择", "擦开", "提瓶", "旋转", "坚持")),
    )},
    ("narrative", "conflict_type"): {"scope": SCOPE_STORY, "rules": (
        ("couple_disagreement", ("吵架", "争执", "拒绝", "争论", "冲突")),
    )},
    ("narrative", "ending_style"): {"scope": SCOPE_STORY, "rules": (
        ("open_double_explanation", ("双解释", "不裁决", "留白", "不解释")),
        ("closed_ending", ("真相大白", "完全解释")),
    )},
    # visual pattern --------------------------------------------------------
    ("visual_pattern", "camera_style"): {"scope": SCOPE_WHOLE, "rules": (
        ("first_person_handheld_capture", ("第一人称", "随手拍", "胸前", "手持")),
        ("old_digital_camera_capture", ("旧数码", "卡片数码", "2000 年代", "DV")),
        ("drone_feed_capture", ("无人机", "图传", "航拍")),
        ("phone_screen_capture", ("手机", "亮屏")),
    )},
    ("visual_pattern", "recurring_visual_elements"): {"scope": SCOPE_WHOLE, "rules": (
        ("lamp_light_motif", ("灯", "亮光")),
        ("fog_layer_motif", ("雾", "低云", "云海")),
        ("glass_surface_motif", ("玻璃", "落地窗")),
        ("drone_feed_motif", ("无人机", "图传")),
        ("thermal_blanket_motif", ("保温毯", "头灯", "运动相机")),
        ("phone_screen_motif", ("手机", "屏幕")),
    )},
    # series fit ------------------------------------------------------------
    ("series_fit", "account_style"): {"scope": SCOPE_WHOLE, "rules": (
        ("reality_grounded_anomaly", ("现实", "第一人称", "记录", "真实", "怪谈")),
    )},
    ("series_fit", "audience_expectation"): {"scope": SCOPE_WHOLE, "rules": (
        ("ordinary_person_uncanny", ("普通人", "异常", "细思极恐", "怪谈")),
    )},
    ("series_fit", "differentiation_evidence"): {"scope": SCOPE_ANTI, "rules": (
        ("declared", ("反同质化", "差异", "不可替代", "避免重复", "机制不同", "最高相似点")),
    )},
}

# Subfields derived from another subfield (documented, no independent keyword).
DERIVED_FIELDS: dict[tuple[str, str], tuple[str, str]] = {
    ("visual_pattern", "environment_pattern"): ("setting", "environment"),
}
