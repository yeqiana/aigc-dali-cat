# -*- coding: utf-8 -*-
import json, io, datetime as dt

EP = "episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/shot-progression-review.json"

def row(frame, cp, sd, subj, action, vfunc, purpose, pov, zone, scale, pos,
        ref_id="", ref_tech="", light_src="", contrast="", suspense="none",
        carrier="none", conceal_pur="", conceal_anchor="", adds_info=False,
        stage="ordinary", hstage="ordinary", present=False,
        emotion="ordinary", intensity=0, trigger="", sync="not_applicable",
        itype="none", actor="", target="", iaction="", meaningful=False,
        new_info=True, ce_reason=""):
    return {
        "frame": frame, "camera_position": cp, "subject_distance": sd,
        "primary_subject": subj, "action": action, "visual_function": vfunc,
        "capture_purpose": purpose, "pov_mode": pov, "location_zone": zone,
        "shot_scale": scale, "scene_position_id": pos,
        "cinematic_reference": {"reference_id": ref_id, "technique_translation": ref_tech, "exact_shot_recreation": False},
        "lighting_design": {"practical_source": light_src, "contrast_mode": contrast, "suspense_function": suspense, "physically_motivated": True, "invented_cinematic_light": False},
        "anomaly_concealment": {"carrier": carrier, "purpose": conceal_pur, "physical_anchor": conceal_anchor, "adds_information": adds_info},
        "anomaly_logic_stage": stage, "human_action_stage": hstage, "human_present": present,
        "emotion": {"state": emotion, "intensity": intensity, "trigger": trigger, "response_sync": sync},
        "interaction": {"type": itype, "actor": actor, "target": target, "action": iaction, "meaningful": meaningful},
        "new_information": new_info, "continuity_exception_reason": ce_reason,
    }

frames = [
  # 01 普通基线：婚房门口
  row("01","门口平视随手","近中景","新娘与布置好的婚房","P01站在门口看屋内红绸喜字，男方侧身忙碌","建立婚房外观与普通先婚后剪生活","普通相册留存，门口随手一拍","P01第一人称持机","门口中位","medium","door_entrance_01",
      light_src="bare_bulb", contrast="mixed_practical", suspense="none",
      carrier="direct_visible", stage="ordinary", hstage="ordinary", present=True,
      emotion="ordinary", intensity=0, itype="none", new_info=True),
  # 02 男方递药
  row("02","床边侧后方","近中景","男方手与白药瓶","男方把无标签药瓶递给她，眼神温和但紧盯着","建立被盯吃的控制关系与药瓶载体","记录他对她的日常照料","P01第一人称持机","床边左侧","close","bedside_handoff_02",
      light_src="bare_bulb", contrast="mixed_practical", suspense="none",
      carrier="direct_visible", stage="ordinary", hstage="ordinary", present=True,
      emotion="uneasy", intensity=1, trigger="他盯着药瓶看我吃药", sync="asynchronous",
      itype="hand_item", actor="男方", target="P01", iaction="男方把药瓶递给她", meaningful=True, new_info=True),
  # 03 梦境土墙铁环
  row("03","梦里地面仰视","近景","土墙、报纸窗与脚踝铁环","脚踝旧铁环冰凉贴在墙上，门缝外一双眼盯着","首处重大异常：被锁的事实","困在梦里的第一人称记录","P01第一人称持机","梦里土墙","close","dream_wall_iron_03",
      ref_id="FRAME_WITHIN_FRAME", ref_tech="用真实门框把门缝外那双眼睛限制在小块信息区，仍是P01梦里第一人称可拍的墙边画面",
      light_src="window_light", contrast="low_light_practical", suspense="hide_information",
      carrier="doorway_or_window", conceal_pur="异常先从门缝与铁环泄露一小块，不入海报式贴脸", conceal_anchor="门框与她的脚踝铁环", adds_info=True,
      stage="discovery", hstage="notice", present=True,
      emotion="uneasy", intensity=2, trigger="脚踝的铁环与门外眼睛", sync="asynchronous",
      itype="none", new_info=True),
  # 04 梦里灌药
  row("04","垫木板旁低位","近景","手脚拴链子与白瓶灌药","有人拿白瓶往她嘴里灌，动作偏糊","交代记忆被替换的机制来源","梦里第一人称记录","P01第一人称持机","梦里木板","close","dream_board_force_04",
      light_src="bare_bulb", contrast="low_light_practical", suspense="hide_information",
      carrier="foreground_occlusion", conceal_pur="灌药动作被手和被角遮挡，只露罐与瓶口，不展示仿效细节", conceal_anchor="她自己的手脚与被角", adds_info=True,
      stage="confirmation", hstage="observe", present=True,
      emotion="uneasy", intensity=3, trigger="有人掰开嘴往喉咙灌药", sync="asynchronous",
      itype="none", new_info=True, ce_reason="梦里陌生灌药者，非群像互动"),
  # 05 醒来喂药姿势
  row("05","床边半侧","近中景","他坐在床边拿药","他递药的姿势与梦里灌药的人一致","把梦与现实连接，锁定关系人物","醒来后立刻抬手拍下他的姿势","P01第一人称持机","床沿中侧","close","bedside_same_pose_05",
      light_src="bare_bulb", contrast="mixed_practical", suspense="reveal_partial_information",
      carrier="direct_visible", stage="confirmation", hstage="notice", present=True,
      emotion="alert", intensity=2, trigger="他抬手动作与梦里灌药那人一样", sync="asynchronous",
      itype="hand_item", actor="男方", target="P01", iaction="男方把药瓶递到她眼前", meaningful=True, new_info=True),
  # 06 婚礼彩排背六年
  row("06","婚房正中偏侧","广角","他持纸逐句背词与P01空洞眼神","他拿纸逐句教她背恋爱六年细节，她重复但眼神茫然","建立记忆被灌输","记录婚礼彩排流程","P01第一人称持机","婚房中侧","wide","hall_script_rehearsal_06",
      light_src="bare_bulb", contrast="flat_natural", suspense="none",
      carrier="direct_visible", stage="ordinary", hstage="ordinary", present=True,
      emotion="uneasy", intensity=1, trigger="她重复却像背台词", sync="asynchronous",
      itype="talk", actor="男方", target="P01", iaction="男方逐句教背恋爱六年", meaningful=True, new_info=True),
  # 07 没人叫名字
  row("07","人群边缘挤进","中景","满屋亲友与镜中母亲梳头","亲友笑着喊她新娘子，无人叫名字；镜中母亲梳头","身份被替换，没人认识货","被围住时随手拍到人群与镜面","P01第一人称持机","人群边角","medium","crowd_mirror_brush_07",
      ref_id="NEGATIVE_SPACE_SUSPENSE", ref_tech="把她自身挤在画面一边，把镜面留作第二信息区，仍是人群里实拍站位",
      light_src="bare_bulb", contrast="mixed_practical", suspense="create_negative_space",
      carrier="mirror", conceal_pur="陌生母亲的脸只在镜中成立，现实层保持人群普通热闹", conceal_anchor="梳头镜面与满屋亲友", adds_info=True,
      stage="discovery", hstage="notice", present=True,
      emotion="uneasy", intensity=2, trigger="镜子里梳头的母亲脸她不认识", sync="asynchronous",
      itype="none", new_info=True),
  # 08 镜中母亲不认识
  row("08","镜前近贴","近景","镜面反射与陌生母亲脸","母亲手继续梳头，镜中那张脸她根本不认识","确认母题推进：陌生的看守母亲","拍下镜中那张陌生脸","P01第一人称持机","镜子前沿","detail","mirror_unfamiliar_face_08",
      ref_id="REFLECTION_SECOND_LAYER", ref_tech="用真实镜框把陌生母亲脸框在第二层，反射亮度略低于实景",
      light_src="bare_bulb", contrast="partial_illumination", suspense="make_reflection_legible",
      carrier="mirror", conceal_pur="陌生脸只在镜面反射成立，避免真实特写贴脸", conceal_anchor="镜面与梳头的手", adds_info=True,
      stage="spatial_contradiction", hstage="observe", present=True,
      emotion="uneasy", intensity=2, trigger="镜中那张脸陌生到让人心慌", sync="asynchronous",
      itype="none", new_info=True),
  # 09 药劲过去
  row("09","深夜摸黑下床低机位","近景","绣花婚鞋与鞋底铁环","她摸黑下床碰到婚鞋觉得沉，翻过来鞋底焊着两道铁环","主动发现异常：婚鞋不是祝福是锁","深夜借微光拍鞋底","P01第一人称持机","床边低位","detail","shoes_iron_sole_09",
      light_src="flashlight", contrast="low_light_practical", suspense="reveal_partial_information",
      carrier="light_and_shadow", conceal_pur="手电光斑只打亮鞋底铁环一小块，其余沉在黑暗", conceal_anchor="手电光斑与鞋底铁环", adds_info=True,
      stage="discovery", hstage="verify", present=True,
      emotion="alert", intensity=2, trigger="婚鞋比想象沉，鞋底有铁", sync="asynchronous",
      itype="none", new_info=True),
  # 10 金镯锁孔
  row("10","手腕贴近","detail","金镯内侧合缝与锁孔","她抬手让金镯内侧合缝和小锁孔靠近镜头","第二个证据：锁具蔓延到首饰","拍手腕细节作为证据","P01第一人称持机","手腕前沿","detail","bracelet_lock_hole_10",
      light_src="flashlight", contrast="low_light_practical", suspense="reveal_partial_information",
      carrier="light_and_shadow", conceal_pur="锁孔只在手电照亮的小块内侧出现，其余保持普通镯子", conceal_anchor="手电与金镯内侧", adds_info=True,
      stage="discovery", hstage="verify", present=True,
      emotion="alert", intensity=2, trigger="金镯内侧藏着锁孔", sync="asynchronous",
      itype="none", new_info=True),
  # 11 喜字下土坯，窗外焊死
  row("11","撕喜字回看","近中景","土坯墙、剥落喜字与焊死木窗","她撕开墙上的喜字露出土坯，回头的木窗从外面被焊死","中点重构：婚房被重读为囚室","记录撕开后墙与窗的真实状态","P01第一人称持机","墙边中位","medium","wall_strip_window_weld_11",
      ref_id="FRAME_WITHIN_FRAME", ref_tech="用真实窗框和墙皮把土坯与焊死窗条框成第二信息层，仍是P01可拍到的站位",
      light_src="flashlight", contrast="low_light_practical", suspense="reveal_partial_information",
      carrier="foreground_occlusion", conceal_pur="土坯与焊条先被喜字碎片和墙皮部分遮住，再由她撕开逐层露出", conceal_anchor="剥落的喜字、墙皮与窗框", adds_info=True,
      stage="spatial_contradiction", hstage="verify", present=True,
      emotion="urgent", intensity=3, trigger="这不是新房是土房，窗被焊死", sync="asynchronous",
      itype="none", new_info=True),
  # 12 最差条件：货车同款女孩
  row("12","门缝向外","近中景","厢式货车、同款嫁衣女孩与车灯","她从门缝向外看，他打开货车后门，车厢里蹲着同款嫁衣女孩脚踝带铁环","不可逆升级，体系性蔓延","弱光里拍货车上女孩","P01第一人称持机","门缝内侧","medium","truck_girls_peek_12",
      ref_id="DEEP_BACKGROUND_ANOMALY", ref_tech="用门缝和车灯把货车与同款嫁衣女孩藏在画面后景，车灯扫过才露出信息",
      light_src="vehicle_headlight", contrast="backlit_silhouette", suspense="hide_information",
      carrier="doorway_or_window", conceal_pur="异常只从门缝和车灯扫过的后景出现，保持偷看的弱光恐怖", conceal_anchor="门框、车厢与车灯", adds_info=True,
      stage="confirmation", hstage="observe", present=True,
      emotion="urgent", intensity=3, trigger="车里蹲着一排同款嫁衣女孩", sync="asynchronous",
      itype="none", new_info=True),
  # 13 他拿药走近
  row("13","门口对峙","近中景","他拿药走近与半身门缝光","他转身拿药慢慢走近，脸上还是温柔表情","推向高潮前最后一刻的控制逼近","记录他走近的脚步","P01第一人称持机","门口对峙位","medium","approach_medicine_13",
      ref_id="LIGHT_BOUNDARY_REVEAL", ref_tech="用门缝冷光与室内暖光的边界把人半身照出，其余沉暗",
      light_src="bare_bulb", contrast="partial_illumination", suspense="separate_foreground_background",
      carrier="light_and_shadow", conceal_pur="门缝光只打亮他半身，药瓶与脸部分压进阴影", conceal_anchor="门缝光与门口", adds_info=True,
      stage="human_consequence", hstage="act", present=True,
      emotion="urgent", intensity=3, trigger="他拿着药慢慢走近", sync="asynchronous",
      itype="none", new_info=True),
  # 14 含药吐进花盆
  row("14","床头侧低机位","近中景","她含药与床头旧花盆","她含药不咽，趁他转身低着头把药吐进旧花盆","被动反抗的开始","记录她隐晦的反抗动作","P01第一人称持机","床头低位","close","spit_medicine_plant_14",
      light_src="bare_bulb", contrast="mixed_practical", suspense="reveal_partial_information",
      carrier="foreground_occlusion", conceal_pur="吐药的嘴与手指被花盆和手挡住一部分，动作可辨但不过于展露", conceal_anchor="床沿、花盆与她的手", adds_info=True,
      stage="human_consequence", hstage="act", present=True,
      emotion="alert", intensity=2, trigger="趁他转身把药吐进花盆", sync="asynchronous",
      itype="none", new_info=True),
  # 15 高潮：摘下金镯逼问
  row("15","正面近中景","近中景","她摘下金镯递到面前与他的愣神","她把金镯摘下来递到他面前，眼神直直逼问，他愣住","高潮选择：把锁具当证物逼问","把金镯和两人的对峙拍成高潮帧","P01第一人称持机","对峙中位","medium","bracelet_confront_15",
      ref_id="NEGATIVE_SPACE_SUSPENSE", ref_tech="把金镯和她的手偏置到一侧，另一侧留给他站的位置和他愣住的空档，仍是正面手持",
      light_src="bare_bulb", contrast="hard_directional", suspense="guide_attention_without_staging",
      carrier="direct_visible", stage="reversal", hstage="act", present=True,
      emotion="urgent", intensity=4, trigger="你送我这镯子说过它能锁住一辈子，现在是来给我锁上吗", sync="asynchronous",
      itype="hand_item", actor="P01", target="男方", iaction="P01摘下金镯递到他面前逼问", meaningful=True, new_info=True),
  # 16 逃进田里
  row("16","跑动中回头","广角","后门、田埂、院门红字与货车灯","后门被撞开，她赤脚跑进田里满脚泥，回头看见红字与车灯","高潮结果：动作后果可见","逃出时夹在奔跑与回头的一帧","P01第一人称持机","后门外","wide","escape_field_back_16",
      ref_id="OCCLUSION_REVEAL", ref_tech="用后门框和车灯在前景挡住一部分，再在她回头时露出院门红字与田埂",
      light_src="vehicle_headlight", contrast="backlit_silhouette", suspense="separate_foreground_background",
      carrier="foreground_occlusion", conceal_pur="逃跑动作被车灯逆光和门框部分遮挡，红字与田埂在她回头时透出", conceal_anchor="后门框、车厢与院门红字", adds_info=True,
      stage="reversal", hstage="act", present=True,
      emotion="urgent", intensity=4, trigger="撞开后门跑进田里，回头看见车灯", sync="asynchronous",
      itype="none", new_info=True),
  # 17 检查站被拦
  row("17","检查站受访","近中景","赤脚泥与半截铁环的脚踝","检查站做笔录的人问名字，她张口却愣住","现实目标获救但身份未闭环","在检查站被救后的一次记录","P01第一人称持机","检查站谈话位","medium","checkpoint_name_17",
      light_src="fluorescent", contrast="flat_natural", suspense="none",
      carrier="direct_visible", stage="payoff", hstage="consequence", present=True,
      emotion="uneasy", intensity=2, trigger="背得出恋爱六年每个细节却想不起自己的名字", sync="asynchronous",
      itype="talk", actor="警察", target="P01", iaction="警察问她叫什么名字她愣住", meaningful=True, new_info=True),
  # 18 陌生女人喊出名字
  row("18","窗外望去","近中景","花白头发女人被搀着跑过来","窗外一个花白头发女人被人搀着跑过来哭得站不住，喊的正是她想不起来的名字","身份锚点被外部接回","拍下窗外喊她名字的人","P01第一人称持机","检查站窗口","medium","window_caller_name_18",
      ref_id="FRAME_WITHIN_FRAME", ref_tech="用真实窗框把窗口外跑来的女人框成第二信息层，反射与遮挡物理成立",
      light_src="fluorescent", contrast="soft_directional", suspense="reveal_partial_information",
      carrier="doorway_or_window", conceal_pur="女人先被窗口和人影部分遮住，再由她转头时被认出", conceal_anchor="窗框与搀扶的人影", adds_info=True,
      stage="human_consequence", hstage="observe", present=True,
      emotion="alert", intensity=2, trigger="窗外有人喊出她想不起的名字", sync="asynchronous",
      itype="none", new_info=True),
  # 19 最后一个梦：明亮房间
  row("19","明亮房间镜前","近中景","镜中试婚鞋的笑脸","明亮房间里她在镜前试婚鞋，镜中人笑着，脚上干净没有铁环","重读整段真实与梦的级差","最后梦里第一人称记录","P01第一人称持机","明亮房间镜前","medium","bright_room_shoes_19",
      light_src="window_light", contrast="flat_natural", suspense="make_reflection_legible",
      carrier="mirror", conceal_pur="用镜中的干净笑脸与无铁环脚，形成与现实级差的梦层", conceal_anchor="镜面与婚鞋", adds_info=True,
      stage="payoff", hstage="consequence", present=True,
      emotion="relaxed", intensity=1, trigger="", sync="asynchronous",
      itype="none", new_info=True, ce_reason="梦里明亮房间，非现实婚房"),
  # 20 天花板留白
  row("20","床上仰视天花板","近中景","斑驳天花板、窗洞光与空药瓶","她躺在床上盯着斑驳天花板，身边只剩一个空药瓶，无字幕","事件闭合后留下醒在哪一层的开放解释","结尾静默空镜","P01第一人称持机","床头仰视","close","ceiling_blank_20",
      light_src="window_light", contrast="flat_natural", suspense="none",
      carrier="direct_visible", stage="payoff", hstage="consequence", present=True,
      emotion="ordinary", intensity=0, sync="asynchronous",
      itype="none", new_info=True),
]

data = {
  "schema_version": 3,
  "status": "LOCKED",
  "genre_family": "general_reality_crack",
  "anomaly_applicable": True,
  "anomaly_exception_reason": "",
  "interaction_applicable": False,
  "interaction_exception_reason": "单人第一人称POV记录，他人是环境与对手戏元素而非群像摄影；把控制与逃离作为主角自身行动链。",
  "rules": {
    "max_identical_setup_consecutive": 2,
    "min_unique_setups_in_5_frames": 3,
    "frame10_requires_new_question_or_evidence": True,
    "scale_only_escalation_is_not_enough": True,
    "max_passive_human_frames_after_confirmation": 2,
    "emotion_intensity_range": [0, 4],
    "emotion_trigger_required_at_intensity_gte": 2,
    "synchronized_theatrical_reaction_forbidden": True,
    "max_consecutive_urgent_frames": 2,
    "min_meaningful_interaction_per_5_human_frames": 1,
    "max_meaningful_interaction_ratio": 0.75,
    "opening_social_natural_interaction_required": True,
    "require_large_and_small_scene": True,
    "exact_scene_position_reuse_forbidden": True,
    "min_cinematic_reference_frames": 2,
    "practical_lighting_required": True,
    "suspense_genre_requires_concealed_anomaly": True,
  },
  "frames": frames,
}

with io.open(EP, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("SHOT PROGRESSION LOCKED:", len(frames))
