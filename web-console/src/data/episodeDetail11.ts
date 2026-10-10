import type { Episode } from '../types';
// 历史 Episode 只读完整证据，按选择再加载，不代表实时 Runtime 状态。
export const EPISODE_DETAIL: Episode = {
  "id": "ep-误入桃花源",
  "code": "误入桃花源",
  "title": "误入桃花源",
  "synopsis": "挂科与实习压力下的林舟误入封闭桃源，发现安宁靠隔绝外界维系，最终返回仍在奔流的现实。",
  "logline": "从逃避竞争、贪恋静止的安宁，转为接受现实压力并主动回应老师和母亲。",
  "genre": "07_误入",
  "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
  "totalFrames": 20,
  "completedFrames": 0,
  "currentStage": "STORYBOARD_LOCK",
  "stageProgressPercent": 0,
  "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
  "updatedAt": "2026-09-22T04:49:25",
  "runtimeRequest": {
    "imageModel": "gpt-image-2",
    "quality": "high",
    "aspectRatio": "4:5 1080×1350",
    "batchMode": "5 帧逻辑批次 (DAG 并发调度)",
    "maxConcurrentImages": 3,
    "executionLayer": "StoryOS 2.6.1 Engine",
    "sourceBadge": "已连接生产内核"
  },
  "characters": [
    {
      "id": "char-误入桃花源-P01",
      "name": "主角 (P01)",
      "role": "第一人称女主角 (POV 主体)",
      "avatar": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "faceEmbeddingId": "CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1",
      "consistencyScore": 98.8,
      "fixedCostume": "洗得发白的灰色连帽卫衣+深灰休闲长裤+磨平防滑纹的开胶旧运动鞋",
      "lightingAnchor": "写实自然光照，胶片颗粒质感，严禁光滑塑料磨皮",
      "archetype": "普通年轻人体型",
      "negativeConstraints": [
        "禁止国籍与文化特征漂移",
        "禁止脸部身份漂移与无依据整形",
        "禁止发型与发长无故事理由突变",
        "禁止塑料光泽与 AI 假面感",
        "禁止除衣橱合约外的随意换装"
      ],
      "status": "locked"
    }
  ],
  "visualLocks": [
    {
      "id": "VL-误入桃花源-01",
      "title": "日常基准 (Ordinary Baseline 01)",
      "category": "主角面容基准",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "aspectRatio": "4:5 (1080×1350)",
      "focalLength": "50mm 自然人像视角",
      "colorGrade": "自然暖调纪实色温，胶片质感",
      "consistencyDelta": "0.00% (主参考点)",
      "isLocked": true,
      "version": "v2.6.1-RELEASE",
      "promptSnippet": "重修考交卷铃砸在头顶，林舟把写满潦草算式的答卷往前一推，冲出阶梯教室时切到手机前置镜头，边走边拍到自己被汗雨打湿的脸和身后的走廊"
    },
    {
      "id": "VL-误入桃花源-02",
      "title": "极限环境 (Worst Condition 11)",
      "category": "高潮光影基调",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "aspectRatio": "4:5 (1080×1350)",
      "focalLength": "35mm 车内低照度广角",
      "colorGrade": "昏暗蓝调微弱侧光",
      "consistencyDelta": "0.82% (通过准入)",
      "isLocked": true,
      "version": "v2.6.1-RELEASE",
      "promptSnippet": "车内夜间低光照，雨水流过车窗侧脸投影，眼神恐慌凝视后视镜。"
    },
    {
      "id": "VL-误入桃花源-03",
      "title": "初次异常 (First Anomaly 03)",
      "category": "关键叙事道具",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "aspectRatio": "4:5 (1080×1350)",
      "focalLength": "85mm 特写景深",
      "colorGrade": "压抑中性偏暗",
      "consistencyDelta": "0.45% (通过准入)",
      "isLocked": true,
      "version": "v2.6.1-RELEASE",
      "promptSnippet": "婚鞋边缘微现铁环锁孔，阳光照在红布与金属冷光交界处。"
    },
    {
      "id": "VL-误入桃花源-04",
      "title": "高潮冲击 (High Impact 15)",
      "category": "主场景环境",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "aspectRatio": "4:5 (1080×1350)",
      "focalLength": "24mm 全景冲击机位",
      "colorGrade": "强对比逆光黄昏",
      "consistencyDelta": "0.94% (通过准入)",
      "isLocked": true,
      "version": "v2.6.1-RELEASE",
      "promptSnippet": "检查站强探照灯打亮货车车斗，铁栏后多双惊恐双眼与主角四目相对。"
    }
  ],
  "storyboardBeats": [
    {
      "id": "beat-1",
      "beatIndex": 1,
      "sceneName": "第 1 镜 · F01",
      "act": "第一幕：建立日常",
      "shotType": "近中景正面留影",
      "lighting": "纪实室内暖光",
      "narration": "重修考交卷铃砸在头顶，林舟把写满潦草算式的答卷往前一推，冲出阶梯教室时切到手机前置镜头，边走边拍到自己被汗雨打湿的脸和身后的走廊",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-2",
      "beatIndex": 2,
      "sceneName": "第 2 镜 · F02",
      "act": "第一幕：建立日常",
      "shotType": "特写细节",
      "lighting": "纪实室内暖光",
      "narration": "林舟没回宿舍也没去食堂，一路拐到学校后勤处背后的荒坡，从半人高的铁丝网缺口钻了进去",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-3",
      "beatIndex": 3,
      "sceneName": "第 3 镜 · F03",
      "act": "第一幕：建立日常",
      "shotType": "主观 POV 移动镜头",
      "lighting": "纪实室内暖光",
      "narration": "转过一道被雨水冲刷发白的石灰岩梁，林子变成成片野桃林，落花混着雨水砸在后颈上，空气里是花瓣与野草在阴暗处腐烂发酵后泛出的微酸冷甜；一条几乎被杂草淹没的干涸石渠横在面前，两头都被草盖住，可渠底和渠沿却被人踩得发亮——没人维护的渠，还留着当天的脚印；石渠尽头是被密密麻麻的铁线蕨遮住的狭窄石缝，阴冷的穿堂风正从缝隙里直往外冒",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-4",
      "beatIndex": 4,
      "sceneName": "第 4 镜 · F04",
      "act": "第一幕：建立日常",
      "shotType": "特写细节",
      "lighting": "纪实室内暖光",
      "narration": "他想起早读课背过的“初极狭，才通人”，明知里面更不会有信号，还是关掉手机页面、打开电筒弯腰钻了进去；在极逼仄的石缝里摸着湿滑岩壁爬了百十来步，水滴在空洞里回响，眼前的岩缝突然裂开一道惨白的光",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-5",
      "beatIndex": 5,
      "sceneName": "第 5 镜 · F05",
      "act": "第一幕：建立日常",
      "shotType": "主观 POV 移动镜头",
      "lighting": "纪实室内暖光",
      "narration": "林舟跌跌撞撞爬出乱石，抬手挡住刺眼的白光，整个人僵在原地——那不是仙境，而是一块被封在深渊底部的三四百亩洼地",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-6",
      "beatIndex": 6,
      "sceneName": "第 6 镜 · F06",
      "act": "第二幕：异常初显",
      "shotType": "特写细节",
      "lighting": "纪实室内暖光",
      "narration": "他的破球鞋带下一块碎石砸进溪水，“咚”的一声之后，整个山谷的动作同时定格，所有人木讷地看向他的连帽衫和双肩包",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-7",
      "beatIndex": 7,
      "sceneName": "第 7 镜 · F07",
      "act": "第二幕：异常初显",
      "shotType": "主观 POV 移动镜头",
      "lighting": "纪实室内暖光",
      "narration": "汉子把短锄插进泥里走过来，用舌根发硬的古怪口音平静地问他是不是外头来的，又看了看他的球鞋，说天快黑了、湿气重，先进屋吃碗热食",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-8",
      "beatIndex": 8,
      "sceneName": "第 8 镜 · F08",
      "act": "第二幕：异常初显",
      "shotType": "特写细节",
      "lighting": "纪实室内暖光",
      "narration": "土屋里没有一根电线、找不到一片塑料，空气里只有松木的青蓝烟气；秦家五口默默围坐，秦叔就着瓦罐喝了一口酒，淡淡问了一句“外头，还争吗？”；林舟把这些年的争一件件说给他听，秦叔讲完老祖宗当年逃进来、天子要兵将领要粮的事，把碗底最后一口米酒喝干，才补上一句不高不低的话：“外头的响动，别进娃们的耳朵。”说完叫小石把弟妹带回里屋睡了",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-9",
      "beatIndex": 9,
      "sceneName": "第 9 镜 · F09",
      "act": "第二幕：异常初显",
      "shotType": "主观 POV 移动镜头",
      "lighting": "纪实室内暖光",
      "narration": "头两天他几乎以为自己掉进了精神疗养院：跟着公鸡醒来、看晨雾拉开、午后睡到夕阳斜照、傍晚在溪边听老人讲对不上年号的旧事；三年焦虑症好像突然自愈，心跳第一次缓得像谷里的死水。但这三天里他每提一句外头的事，秦家人只是听着、谁都不接话；村里的孩子远远跟着他看，不敢走近",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-10",
      "beatIndex": 10,
      "sceneName": "第 10 镜 · F10",
      "act": "第二幕：异常初显",
      "shotType": "特写细节",
      "lighting": "纪实室内暖光",
      "narration": "第三天傍晚，他坐在老水井旁帮秦叔削竹篾，十五岁的小石蹲在旁边，眼睛一眨不眨盯着那台早就没电的黑屏手机；他忽然把前三天重新看了一遍——没有电线、没有塑料、整齐得像用尺子量过的田，这些不是清静，是这村子几百年里谁都没见过外面；秦叔留他吃饭、留他住，也不全是待客，是把他放在规矩里看着",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-11",
      "beatIndex": 11,
      "sceneName": "第 11 镜 · F11",
      "act": "第二幕：异常初显",
      "shotType": "主观 POV 移动镜头",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "他从书包侧兜摸出最后半管润喉薄荷糖，剥出一粒绿色的递过去；小石怯生生看了父亲一眼，见秦叔背对着在理竹条，飞快地把糖塞进嘴里",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-12",
      "beatIndex": 12,
      "sceneName": "第 12 镜 · F12",
      "act": "第二幕：异常初显",
      "shotType": "特写细节",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "工业提纯的浓烈薄荷脑直冲上来，少年整个人像被电击中一样僵住，声音发着抖问“这是什么果子”；而他从那片黑玻璃里听来的铁鸟、大海和月亮，让那双眼睛里烧起他在每个自习室和招聘会上见过的火",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-13",
      "beatIndex": 13,
      "sceneName": "第 13 镜 · F13",
      "act": "第三幕：危机爆发",
      "shotType": "主观 POV 移动镜头",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "他笑了笑，顺手拿起那台黑屏手机晃了晃，说在外面这东西想要多少有多少，要是它有电，能看见一万公里外的大海、天上飞的铁鸟，还有月亮其实就是个坑坑洼洼的大石头",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-14",
      "beatIndex": 14,
      "sceneName": "第 14 镜 · F14",
      "act": "第三幕：危机爆发",
      "shotType": "特写细节",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "一声极脆的裂响刺破黄昏：秦叔手里的柴刀偏了半寸，把一根厚竹劈得粉碎；他手按在刀柄上，声音平得像结了冰的深潭，只说了一句“小石，后山的羊圈该关了。去。”；那一声之后整座山谷第二次定了格，比 Frame 06 那次更彻底——远处田埂上的动作停在半途，隔壁院的织机声也停了，连狗都不叫",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-15",
      "beatIndex": 15,
      "sceneName": "第 15 镜 · F15",
      "act": "第三幕：危机爆发",
      "shotType": "主观 POV 移动镜头",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "那夜没风，天幕黑得像扣下来的生铁锅；门轴吱呀一声，秦叔端着菜籽油灯进来，把糖纸和湿纸巾放在他床头，说天亮前出山去，又讲这山谷从来不是什么仙境，是一口枯井——人要活命，就只能把这口井当成天地",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-16",
      "beatIndex": 16,
      "sceneName": "第 16 镜 · F16",
      "act": "第三幕：危机爆发",
      "shotType": "特写细节",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "拂晓时分寒雾把山谷浸成惨白；秦叔把他送到石缝前，塞给他两个用晒干的荷叶包着的硬麦饼，说顺着暗水流的方向爬、别回头，等夏至山洪下来这道缝就会被滚石彻底填死",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-17",
      "beatIndex": 17,
      "sceneName": "第 17 镜 · F17",
      "act": "第三幕：危机爆发",
      "shotType": "主观 POV 移动镜头",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "钻进石缝的最后一瞬，他回过头看了一眼：炊烟照常升起，公鸡照常啼叫，可他眼里再也没有了那种诗意，只看见一群难民的后代用世世代代的封闭给自己修的千年墓穴",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-18",
      "beatIndex": 18,
      "sceneName": "第 18 镜 · F18",
      "act": "第三幕：危机爆发",
      "shotType": "特写细节",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "他拨开洞口湿烂的藤蔓滚出后山，上午刺眼的白昼晃得眼睛生疼；山脚下高速货车的轰鸣像海啸撞进耳膜，打桩机的震动顺着地表传上来，震得脚踝发麻",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-19",
      "beatIndex": 19,
      "sceneName": "第 19 镜 · F19",
      "act": "终局：反转回响",
      "shotType": "主观 POV 移动镜头",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "口袋里的手机突然疯狂震动，未接来电和提示音连成一片；辅导员说明早九点前必须交实习证明，母亲说表哥已经帮他约好了下周二的面试，让他把衣服穿整齐点",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    },
    {
      "id": "beat-20",
      "beatIndex": 20,
      "sceneName": "第 20 镜 · F20",
      "act": "终局：反转回响",
      "shotType": "特写细节",
      "lighting": "低照度环境光 / 雨夜投影",
      "narration": "他站在风口里把那口混着尾气与沥青味的浊气吸进肺里，咬碎冷硬的麦饼，给辅导员回“收到，老师，我周一上午当面交您”，再按下母亲的通话回拨键，然后踩着满是泥的旧球鞋头也不回地走下山",
      "status": "rendering",
      "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
    }
  ],
  "currentBatch": {
    "batchId": "batch-误入桃花源-final",
    "batchNumber": 4,
    "batchName": "全量 20 帧成片批次",
    "targetFrames": "01-20",
    "totalImages": 20,
    "createdAt": "2026-09-22T04:49:25",
    "status": "processing",
    "items": [
      {
        "id": "bi-1",
        "frameIndex": 1,
        "prompt": "重修考交卷铃砸在头顶，林舟把写满潦草算式的答卷往前一推，冲出阶梯教室时切到手机前置镜头，边走边拍到自己被汗雨打湿的脸和身后的走廊",
        "seed": 42001,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-2",
        "frameIndex": 2,
        "prompt": "林舟没回宿舍也没去食堂，一路拐到学校后勤处背后的荒坡，从半人高的铁丝网缺口钻了进去",
        "seed": 42002,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-3",
        "frameIndex": 3,
        "prompt": "转过一道被雨水冲刷发白的石灰岩梁，林子变成成片野桃林，落花混着雨水砸在后颈上，空气里是花瓣与野草在阴暗处腐烂发酵后泛出的微酸冷甜；一条几乎被杂草淹没的干涸石渠横在面前，两头都被草盖住，可渠底和渠沿却被人踩得发亮——没人维护的渠，还留着当天的脚印；石渠尽头是被密密麻麻的铁线蕨遮住的狭窄石缝，阴冷的穿堂风正从缝隙里直往外冒",
        "seed": 42003,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-4",
        "frameIndex": 4,
        "prompt": "他想起早读课背过的“初极狭，才通人”，明知里面更不会有信号，还是关掉手机页面、打开电筒弯腰钻了进去；在极逼仄的石缝里摸着湿滑岩壁爬了百十来步，水滴在空洞里回响，眼前的岩缝突然裂开一道惨白的光",
        "seed": 42004,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-5",
        "frameIndex": 5,
        "prompt": "林舟跌跌撞撞爬出乱石，抬手挡住刺眼的白光，整个人僵在原地——那不是仙境，而是一块被封在深渊底部的三四百亩洼地",
        "seed": 42005,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-6",
        "frameIndex": 6,
        "prompt": "他的破球鞋带下一块碎石砸进溪水，“咚”的一声之后，整个山谷的动作同时定格，所有人木讷地看向他的连帽衫和双肩包",
        "seed": 42006,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-7",
        "frameIndex": 7,
        "prompt": "汉子把短锄插进泥里走过来，用舌根发硬的古怪口音平静地问他是不是外头来的，又看了看他的球鞋，说天快黑了、湿气重，先进屋吃碗热食",
        "seed": 42007,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-8",
        "frameIndex": 8,
        "prompt": "土屋里没有一根电线、找不到一片塑料，空气里只有松木的青蓝烟气；秦家五口默默围坐，秦叔就着瓦罐喝了一口酒，淡淡问了一句“外头，还争吗？”；林舟把这些年的争一件件说给他听，秦叔讲完老祖宗当年逃进来、天子要兵将领要粮的事，把碗底最后一口米酒喝干，才补上一句不高不低的话：“外头的响动，别进娃们的耳朵。”说完叫小石把弟妹带回里屋睡了",
        "seed": 42008,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-9",
        "frameIndex": 9,
        "prompt": "头两天他几乎以为自己掉进了精神疗养院：跟着公鸡醒来、看晨雾拉开、午后睡到夕阳斜照、傍晚在溪边听老人讲对不上年号的旧事；三年焦虑症好像突然自愈，心跳第一次缓得像谷里的死水。但这三天里他每提一句外头的事，秦家人只是听着、谁都不接话；村里的孩子远远跟着他看，不敢走近",
        "seed": 42009,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-10",
        "frameIndex": 10,
        "prompt": "第三天傍晚，他坐在老水井旁帮秦叔削竹篾，十五岁的小石蹲在旁边，眼睛一眨不眨盯着那台早就没电的黑屏手机；他忽然把前三天重新看了一遍——没有电线、没有塑料、整齐得像用尺子量过的田，这些不是清静，是这村子几百年里谁都没见过外面；秦叔留他吃饭、留他住，也不全是待客，是把他放在规矩里看着",
        "seed": 42010,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-11",
        "frameIndex": 11,
        "prompt": "他从书包侧兜摸出最后半管润喉薄荷糖，剥出一粒绿色的递过去；小石怯生生看了父亲一眼，见秦叔背对着在理竹条，飞快地把糖塞进嘴里",
        "seed": 42011,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-12",
        "frameIndex": 12,
        "prompt": "工业提纯的浓烈薄荷脑直冲上来，少年整个人像被电击中一样僵住，声音发着抖问“这是什么果子”；而他从那片黑玻璃里听来的铁鸟、大海和月亮，让那双眼睛里烧起他在每个自习室和招聘会上见过的火",
        "seed": 42012,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-13",
        "frameIndex": 13,
        "prompt": "他笑了笑，顺手拿起那台黑屏手机晃了晃，说在外面这东西想要多少有多少，要是它有电，能看见一万公里外的大海、天上飞的铁鸟，还有月亮其实就是个坑坑洼洼的大石头",
        "seed": 42013,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-14",
        "frameIndex": 14,
        "prompt": "一声极脆的裂响刺破黄昏：秦叔手里的柴刀偏了半寸，把一根厚竹劈得粉碎；他手按在刀柄上，声音平得像结了冰的深潭，只说了一句“小石，后山的羊圈该关了。去。”；那一声之后整座山谷第二次定了格，比 Frame 06 那次更彻底——远处田埂上的动作停在半途，隔壁院的织机声也停了，连狗都不叫",
        "seed": 42014,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-15",
        "frameIndex": 15,
        "prompt": "那夜没风，天幕黑得像扣下来的生铁锅；门轴吱呀一声，秦叔端着菜籽油灯进来，把糖纸和湿纸巾放在他床头，说天亮前出山去，又讲这山谷从来不是什么仙境，是一口枯井——人要活命，就只能把这口井当成天地",
        "seed": 42015,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-16",
        "frameIndex": 16,
        "prompt": "拂晓时分寒雾把山谷浸成惨白；秦叔把他送到石缝前，塞给他两个用晒干的荷叶包着的硬麦饼，说顺着暗水流的方向爬、别回头，等夏至山洪下来这道缝就会被滚石彻底填死",
        "seed": 42016,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-17",
        "frameIndex": 17,
        "prompt": "钻进石缝的最后一瞬，他回过头看了一眼：炊烟照常升起，公鸡照常啼叫，可他眼里再也没有了那种诗意，只看见一群难民的后代用世世代代的封闭给自己修的千年墓穴",
        "seed": 42017,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-18",
        "frameIndex": 18,
        "prompt": "他拨开洞口湿烂的藤蔓滚出后山，上午刺眼的白昼晃得眼睛生疼；山脚下高速货车的轰鸣像海啸撞进耳膜，打桩机的震动顺着地表传上来，震得脚踝发麻",
        "seed": 42018,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-19",
        "frameIndex": 19,
        "prompt": "口袋里的手机突然疯狂震动，未接来电和提示音连成一片；辅导员说明早九点前必须交实习证明，母亲说表哥已经帮他约好了下周二的面试，让他把衣服穿整齐点",
        "seed": 42019,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      },
      {
        "id": "bi-20",
        "frameIndex": 20,
        "prompt": "他站在风口里把那口混着尾气与沥青味的浊气吸进肺里，咬碎冷硬的麦饼，给辅导员回“收到，老师，我周一上午当面交您”，再按下母亲的通话回拨键，然后踩着满是泥的旧球鞋头也不回地走下山",
        "seed": 42020,
        "status": "rendering",
        "progress": 45,
        "renderTime": "38s",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "consistencyScore": 98.5
      }
    ]
  },
  "frameReviews": [
    {
      "frameId": "fr-1",
      "frameIndex": 1,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "曾重试通过",
        "首帧唯一露脸"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-2",
      "frameIndex": 2,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-3",
      "frameIndex": 3,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-4",
      "frameIndex": 4,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-5",
      "frameIndex": 5,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-6",
      "frameIndex": 6,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-7",
      "frameIndex": 7,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-8",
      "frameIndex": 8,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-9",
      "frameIndex": 9,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-10",
      "frameIndex": 10,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-11",
      "frameIndex": 11,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-12",
      "frameIndex": 12,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-13",
      "frameIndex": 13,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-14",
      "frameIndex": 14,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-15",
      "frameIndex": 15,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-16",
      "frameIndex": 16,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-17",
      "frameIndex": 17,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-18",
      "frameIndex": 18,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-19",
      "frameIndex": 19,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    },
    {
      "frameId": "fr-20",
      "frameIndex": 20,
      "timestamp": "2026-09-22T04:49:25",
      "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "shotType": "4:5 叙事画幅",
      "facialScore": 98.6,
      "lightConsistency": 97.9,
      "anatomyScore": 99.2,
      "verdict": "PASS",
      "issueTags": [
        "面容锁定",
        "无塑料感",
        "画幅严格4:5"
      ],
      "reviewer": "semantic-critic-worker",
      "comment": "符合真实性与光影一致性标准。"
    }
  ],
  "preflightChecks": [
    {
      "id": "pf-1",
      "title": "画幅规范审查 (4:5 1080×1350)",
      "category": "资产合规",
      "status": "passed",
      "detail": "全部 20 帧尺寸严格为 1080×1350，Lanczos 重采样无拉伸无黑边。",
      "automated": true
    },
    {
      "id": "pf-2",
      "title": "主角面容一致性锁定 (P01)",
      "category": "视觉一致性",
      "status": "passed",
      "detail": "P01 跨帧一致性评分 98.8%，无未授权发型或骨相漂移。",
      "automated": true
    },
    {
      "id": "pf-3",
      "title": "字幕人话化与布局审查",
      "category": "音画同步",
      "status": "passed",
      "detail": "逐帧台词断句完整，字幕安全区校验通过，无文字与视觉主体冲突。",
      "automated": true
    },
    {
      "id": "pf-4",
      "title": "AI 治理与真实性门禁",
      "category": "审查与分发",
      "status": "passed",
      "detail": "通过 Anti-Plasticity 审查，自然皮肤纹理可见，无过度平滑塑料假面。",
      "automated": true
    }
  ],
  "performance": {
    "6h": {
      "timeframe": "6h",
      "label": "发布后 6 小时",
      "completionRate": "84.2%",
      "completionDelta": "+12.4%",
      "views": "28,420",
      "viewsDelta": "+45%",
      "shareVelocity": "142次/小时",
      "retentionSpikeBeat": "第 11 帧（车内反转点）",
      "retentionDropBeat": "无明显流失",
      "viralityIndex": "8.92",
      "audienceSentiment": "97.2% 悬疑好评",
      "trendData": [
        {
          "time": "0h",
          "value": 1200
        },
        {
          "time": "2h",
          "value": 8900
        },
        {
          "time": "4h",
          "value": 18400
        },
        {
          "time": "6h",
          "value": 28420
        }
      ]
    },
    "24h": {
      "timeframe": "24h",
      "label": "发布后 24 小时",
      "completionRate": "81.6%",
      "completionDelta": "+9.1%",
      "views": "142,600",
      "viewsDelta": "+88%",
      "shareVelocity": "380次/小时",
      "retentionSpikeBeat": "第 13 帧（货车铁栏揭露）",
      "retentionDropBeat": "第 17 帧微降",
      "viralityIndex": "9.31",
      "audienceSentiment": "96.8% 好评",
      "trendData": [
        {
          "time": "0h",
          "value": 2000
        },
        {
          "time": "6h",
          "value": 28420
        },
        {
          "time": "12h",
          "value": 74200
        },
        {
          "time": "24h",
          "value": 142600
        }
      ]
    },
    "48h": {
      "timeframe": "48h",
      "label": "发布后 48 小时",
      "completionRate": "79.8%",
      "completionDelta": "+6.5%",
      "views": "320,500",
      "viewsDelta": "+34%",
      "shareVelocity": "210次/小时",
      "retentionSpikeBeat": "第 11 帧 / 第 19 帧",
      "retentionDropBeat": "尾声轻度自然脱落",
      "viralityIndex": "9.18",
      "audienceSentiment": "96.4% 好评",
      "trendData": [
        {
          "time": "0h",
          "value": 5000
        },
        {
          "time": "12h",
          "value": 74200
        },
        {
          "time": "24h",
          "value": 142600
        },
        {
          "time": "48h",
          "value": 320500
        }
      ]
    },
    "7d": {
      "timeframe": "7d",
      "label": "发布后 7 天复盘",
      "completionRate": "78.5%",
      "completionDelta": "+5.2%",
      "views": "890,200",
      "viewsDelta": "+18%",
      "shareVelocity": "95次/小时",
      "retentionSpikeBeat": "全剧长尾完播稳定",
      "retentionDropBeat": "首屏 3 秒通过率 88%",
      "viralityIndex": "9.05",
      "audienceSentiment": "96.1% 强推荐",
      "trendData": [
        {
          "time": "1d",
          "value": 142600
        },
        {
          "time": "3d",
          "value": 450000
        },
        {
          "time": "5d",
          "value": 710000
        },
        {
          "time": "7d",
          "value": 890200
        }
      ]
    }
  }
};
