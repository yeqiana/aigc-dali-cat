# -*- coding: utf-8 -*-
import json, io, os

EP = "episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/story-gates.json"
with io.open(EP, "r", encoding="utf-8") as f:
    g = json.load(f)
visual = g["visual"]

env = {
  "schema_version": 1,
  "season": "深秋",
  "baseline": {
    "condition": "干冷晴夜转深夜，婚房室内白炽灯与窗洞天光",
    "time_of_day": "黄昏入夜到第二天凌晨",
    "temperature_feel": "干冷，夜越深越凉，室外农田更冷",
    "ground_state": "室内夯土地面+红纸碎屑，室外土路与农田",
    "visibility": "夜间弱光，靠白炽灯、窗洞与手电，暗部易糊",
    "wind": "微风干燥",
    "precipitation": "无降水",
    "physical_cues": ["白炽灯暖光溢出偏低", "暗部噪点与边缘偏软", "窗洞冷光与室内暖光并存", "土坯墙纹理与红纸喜字", "手电光斑在黑暗中割裂"]
  },
  "segments": [
    {"id": "S1", "start_frame": 1, "end_frame": 2, "condition": "婚房布置完成，室内白炽灯，黄昏入夜", "physical_cues": ["红纸喜字反光", "木床红绸", "搪瓷盆", "土墙与糊窗纸"], "conditional_effects": [{"effect": "白炽灯下红纸颜色偏艳但周围发灰", "when": ["室内", "贴近红纸"]}]},
    {"id": "S2", "start_frame": 3, "end_frame": 4, "condition": "睡梦空间，昏暗土墙，仅门缝与微弱光", "physical_cues": ["报纸糊窗", "脚踝铁环冰凉", "灌药动作偏糊", "门缝外一双眼"], "conditional_effects": [{"effect": "画面更糊、暗部更重，边缘更软", "when": ["梦境", "弱光", "近距离"]}]},
    {"id": "S3", "start_frame": 5, "end_frame": 8, "condition": "惊醒回婚房，室内白炽灯稳定，夜", "physical_cues": ["他从床边递药", "满屋亲友", "镜子反射", "镜中母亲陌生脸"], "conditional_effects": [{"effect": "镜子反射亮度略低于实景", "when": ["镜面", "反射"]}]},
    {"id": "S4", "start_frame": 9, "end_frame": 11, "condition": "深夜摸黑，室内暗到只靠手电与门缝微光", "physical_cues": ["婚鞋沉", "鞋底焊两道铁环", "金镯内侧合缝小锁孔", "喜字下露土坯", "窗从外焊死"], "conditional_effects": [{"effect": "手电光斑在土墙上割出明暗分界", "when": ["打手电", "近距离"]}]},
    {"id": "S5", "start_frame": 12, "end_frame": 13, "condition": "院门口深夜，货车车灯白花花，手电补光", "physical_cues": ["厢式货车", "同款红嫁衣女孩", "脚踝铁环", "车灯扫过田埂"], "conditional_effects": [{"effect": "车灯方向性拖影与高光溢出", "when": ["车灯", "背光"]}]},
    {"id": "S6", "start_frame": 14, "end_frame": 15, "condition": "对峙，室内白炽灯，紧张", "physical_cues": ["那瓶无标签药", "床头旧花盆", "金镯", "绣鞋"], "conditional_effects": [{"effect": "灯光在白炽灯下偏硬，人物半身更清楚", "when": ["近景", "对峙"]}]},
    {"id": "S7", "start_frame": 16, "end_frame": 18, "condition": "出逃，深夜室外，月光/车灯/检查站灯光", "physical_cues": ["赤脚满泥", "脚踝半截铁环", "货车灯", "省道检查站", "花白头发女人"], "conditional_effects": [{"effect": "室外冷光与检查站白光更硬", "when": ["室外", "检查站"]}]},
    {"id": "S8", "start_frame": 19, "end_frame": 20, "condition": "最后梦空间与清晨留白，明亮干净或斑驳天花板", "physical_cues": ["镜子试婚鞋", "脚上干净无铁环", "空药瓶", "斑驳天花板", "窗洞光"], "conditional_effects": [{"effect": "明亮房间与土房留白形成级差", "when": ["梦", "天花板"]}]}
  ],
  "frame_overrides": {}
}

fd = {
  "01": {"narrative_role": "setup", "frame_mode": "normal_record", "impact_level": 0, "required_visual_cues": ["门口土房", "红纸喜字", "无标签白药瓶", "木床", "搪瓷盆"], "scale_reference": "", "escalation_from": None},
  "02": {"narrative_role": "evidence", "frame_mode": "normal_record", "impact_level": 0, "required_visual_cues": ["白药瓶递交", "男方温和眼神紧盯", "亲友缝喜被背景"], "scale_reference": "", "escalation_from": None},
  "03": {"narrative_role": "reveal", "frame_mode": "anomaly_reveal", "impact_level": 2, "required_visual_cues": ["土墙", "报纸糊窗", "脚踝铁环", "门缝外一双眼"], "scale_reference": "门缝与脚踝铁环", "escalation_from": None},
  "04": {"narrative_role": "reveal", "frame_mode": "anomaly_reveal", "impact_level": 2, "required_visual_cues": ["木板", "手脚拴链子", "白瓶灌药", "偏糊昏暗"], "scale_reference": "链子与手", "escalation_from": None},
  "05": {"narrative_role": "reveal", "frame_mode": "anomaly_reveal", "impact_level": 1, "required_visual_cues": ["他从床边递药", "与梦里一致姿势", "温和侧脸"], "scale_reference": "", "escalation_from": None},
  "06": {"narrative_role": "evidence", "frame_mode": "normal_record", "impact_level": 0, "required_visual_cues": ["纸/手机逐句背词", "她眼神茫然", "婚房背景"], "scale_reference": "", "escalation_from": None},
  "07": {"narrative_role": "evidence", "frame_mode": "anomaly_reveal", "impact_level": 1, "required_visual_cues": ["满屋亲友喊新娘子", "无人叫名字", "镜中母亲梳头", "手凉"], "scale_reference": "", "escalation_from": None},
  "08": {"narrative_role": "reveal", "frame_mode": "anomaly_reveal", "impact_level": 2, "required_visual_cues": ["镜面反射", "陌生母亲脸", "暗部可辨表情"], "scale_reference": "镜框与脸", "escalation_from": None},
  "09": {"narrative_role": "evidence", "frame_mode": "anomaly_reveal", "impact_level": 2, "required_visual_cues": ["摸黑下床", "婚鞋沉", "鞋底焊两道铁环"], "scale_reference": "婚鞋与脚", "escalation_from": None},
  "10": {"narrative_role": "reveal", "frame_mode": "anomaly_reveal", "impact_level": 2, "required_visual_cues": ["金镯拉近", "内侧合缝", "小锁孔", "另一手摸镯口"], "scale_reference": "金镯与手指", "escalation_from": None},
  "11": {"narrative_role": "reveal", "frame_mode": "anomaly_amplified", "impact_level": 3, "required_visual_cues": ["喜字下露土坯", "墙皮剥落", "木窗从外焊死", "旧铁条加固"], "scale_reference": "窗户与墙、人体尺度", "escalation_from": 9},
  "12": {"narrative_role": "escalation", "frame_mode": "anomaly_amplified", "impact_level": 3, "required_visual_cues": ["厢式货车后门", "同款红嫁衣女孩", "脚踝铁环", "车灯白花花"], "scale_reference": "车厢与人、车灯", "escalation_from": 11},
  "13": {"narrative_role": "escalation", "frame_mode": "anomaly_amplified", "impact_level": 3, "required_visual_cues": ["他拿药走近", "温柔表情", "门缝光打半身"], "scale_reference": "药瓶与手、门框", "escalation_from": 12},
  "14": {"narrative_role": "transition", "frame_mode": "normal_record", "impact_level": 1, "required_visual_cues": ["含药不咽", "趁他转身", "低头吐进花盆"], "scale_reference": "", "escalation_from": None},
  "15": {"narrative_role": "climax", "frame_mode": "climax_impact", "impact_level": 4, "required_visual_cues": ["摘下金镯逼问", "眼神直直", "他愣住", "金镯递到面前"], "scale_reference": "金镯与手、脸", "escalation_from": 13},
  "16": {"narrative_role": "transition", "frame_mode": "anomaly_amplified", "impact_level": 3, "required_visual_cues": ["后门被撞开", "女孩跌出车", "赤脚跑进田", "泥脚回头看红字与车灯"], "scale_reference": "田埂与院门、车灯", "escalation_from": 15},
  "17": {"narrative_role": "payoff", "frame_mode": "normal_record", "impact_level": 1, "required_visual_cues": ["省道检查站", "赤脚泥", "脚踝半截铁环", "做笔录问名字"], "scale_reference": "", "escalation_from": None},
  "18": {"narrative_role": "payoff", "frame_mode": "normal_record", "impact_level": 1, "required_visual_cues": ["窗外花白头发女人", "被搀跑过来", "哭得站不住", "喊出名字"], "scale_reference": "", "escalation_from": None},
  "19": {"narrative_role": "residue", "frame_mode": "payoff", "impact_level": 0, "required_visual_cues": ["明亮干净房间", "镜前试婚鞋", "镜中人笑", "脚干净无铁环无药"], "scale_reference": "", "escalation_from": None},
  "20": {"narrative_role": "residue", "frame_mode": "payoff", "impact_level": 0, "required_visual_cues": ["床上醒着", "盯着斑驳天花板", "窗洞光", "身边空药瓶"], "scale_reference": "", "escalation_from": None}
}

visual["environment_contract"] = env
visual["frame_directives"] = fd
visual["continuity"]["anchors"] = {
  "protagonist": "23岁碎花长袖上衣+深色长裤+旧布鞋，只露手/脚/局部，不露清晰正脸",
  "location": "西北农村土房婚房，土坯墙、白纸糊窗、红纸喜字、木床、搪瓷盆、窗外土路农田",
  "key_prop": "无标签白色小药瓶；大红绣花婚鞋（鞋底焊两道铁环）；一对金镯（内侧合缝小锁孔）；从外焊死的木窗",
  "wardrobe": "主角碎花长袖上衣+深色长裤+旧布鞋；嫁衣内衬同款；男方干净深色外套",
  "weather_time": "深秋，黄昏入夜到第二天凌晨；白炽灯/窗洞天光/手电/车灯"
}
visual["authenticity_card"] = {
  "story_era": "2007年前后，中国西北农村",
  "location": "西北农村土房婚房",
  "photographer": "23岁被安排成亲的新娘（第一人称）",
  "shooting_reason": "给老人看嫁妆/留个纪念，也顺手把看到的不对劲拍下来",
  "primary_capture": {"id": "CP03", "device": "2007年前后廉价卡片数码相机"},
  "secondary_captures": [],
  "secondary_source_explanation": "全部画面均由主角手持旧数码相机记录，无第二来源",
  "aspect_ratio": "4:5",
  "capture_states": {"stable": "婚房布置、婚礼彩排等平稳场景，手持正常，画面相对稳", "restricted": "深夜摸黑、看货车、她被迫服药时，手抖、对焦犹豫、构图偏位", "lost_control": "撞开后门逃进田里时，画面剧烈晃动、糊片、高光溢出"},
  "camera_rules": {"current_device_may_be_fully_visible": False, "current_device_visibility_explanation": "第一人称手持记录，不主动展示相机全貌", "photographer_may_be_fully_visible": True, "photographer_visibility_explanation": "主角作为摄影者可以局部入画（手、脚步、半身、镜中反射），避免露清晰正脸"}
}

with io.open(EP, "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False, indent=2)
print("FILLED")
