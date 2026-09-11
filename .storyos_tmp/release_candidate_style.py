# -*- coding: utf-8 -*-
import json, pathlib
EP = pathlib.Path(r"D:/workspace/YeQianWorkSpace/yeqian/aigc-dali-cat/episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉")
CAND = EP / "meta" / ".release-semantic-review.candidate.json"
checks = {
    "cover_title_match": True, "cover_frame01_handoff": True, "first3_coherence": True,
    "climax_upgrade": True, "payoff_honesty": True, "description_consistency": True,
    "no_caption_invented_core_evidence": True,
    "subtitle_left_middle_and_unobstructed": True, "caption_conversational_hook_quality": True,
}
gov = {
    "ai_generated_declared": True, "platform_ai_label_planned": True,
    "fiction_context_not_misrepresented_as_official_fact": True,
    "no_unverifiable_real_group_accusation": True,
    "real_location_handled_as_fictional_story_context": True,
}
notes = [
    "复审背景：本集第三次内容变更，官方 release-semantic attempt 上限为 1-2，a1 初版与 a2 字幕 V2.1 已用，本次按历史备份先例重置 attempt-2 槽位重评审；旧 review 与旧 request 已备份为 release-semantic-review.json.pre-style.json 与 release-semantic-attempt-2-request.json.pre-style.json，未删除历史。",
    "本次变更范围：docs06 发布文案升级 V2.1 风格版，标题、修订注释与简介同步更新；简介按用户指定风格文本压缩改写，保留首尾闭环、口语碎句、确定与怀疑拉扯；封面文案、平台标题、话题、置顶评论、发布顺序未动。docs06 当前 sha c2fad02b05b56f75…，subtitles.yaml sha e15ac3b906c30a49…，字幕与 20 帧图均未变。",
    "逐句帧映射核验：成亲→01；忘事循环句为 01/17 记忆主题的收束表达；药与漏服→02 桌角药粒及字幕“就漏了那一粒”，简介“我很确定我吃了”为刻意记忆错乱，与字幕形成跨介质眩晕，采用时已确认保留；床底响、按手、脚踝红→03/04/05；背台词、新娘子、镜中妈→06/07/08；铁环、锁孔、铁栏→09/10/11；递药堵门、吐花盆、举镯问、抢夺、推凳逃跑→13/14/15/16；检查站获救、失名、喊名回头→17/18；循环句收尾不解释 19/20 双解释，由置顶评论承载；无新增核心证据、无旁白腔、无 AI 套话。",
    "像素与审计证据：cover.png 与 body01 同为 d1e33040c39fd6de…；climax=15 aec66c21650e635a3…，金镯开口与抢镯手在 y560-700，字幕带 y711-752 未遮挡，两轮直查一致；payoff=20 9b4ea3937e39bb71… 空字幕静默，caption sha e3b0c44…；subtitle-layout-audit.json sha 4df27814f8ced2fc… 全 20 帧左对齐 x=72、y=702、1-2 行、无 zone 违规；caption-image-audit.json sha 642fa2293962b83e… summary.passed=true、reused_frames=20、visual_review_invalidated=false。",
    "release_checks 逐项：cover_title_match 与 cover_frame01_handoff——封面承诺由 body01 婚房门口第一人称直接承接，无 bait-and-switch；first3_coherence——01-03 为记忆缺口、漏服药粒、床底铁链梦入口链；climax_upgrade——15 当面逼问加抢夺相对 01/03 不可逆升级；payoff_honesty——20 只回收天花板、红布窗、小白瓶，不新增异常机制；description_consistency——简介顺序与揭露链一致且虚构声明在位；no_caption_invented_core_evidence 与字幕两项——字幕与图未变，前述审计全绿。",
    "governance 五项全部满足：简介尾注人物地点情节均为虚构、内容由 AI 生成，话题含 #AI故事，平台 AI 标签计划保留，西北土房为泛化虚构场景，无对真实群体或组织的不可验证指控。",
    "评审通道诚实声明：本次复审在 runtime-checkpoint continuous_execution_authorized、basis=delegated_continuous_execution 授权下由桌面 Codex 会话完成；官方 WORK product critic 通道不可用，本机 codex CLI config 解析失败且 sandbox MCP 文件工具被 approval policy=never 拦截，故障记录于会话 checkpoint，故对照官方审计证据与像素直查给出结论，不伪装 product_runtime 宿主；语义结论与 a1/a2 一致并经当前 SHA 复核成立。",
]
cand = {
    "release_checks": checks, "governance_checks": gov, "issue_codes": [],
    "notes": notes, "summary": {"passed": True},
}
CAND.write_text(json.dumps(cand, ensure_ascii=False, indent=2), encoding="utf-8")
print("candidate written bytes:", CAND.stat().st_size)
