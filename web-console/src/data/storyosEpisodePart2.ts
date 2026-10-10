// 只读历史 Episode 证据分组；正式生产状态以 Runtime API 为准。
import type { Episode } from '../types';
export const EPISODE_PART_2: Episode[] = [
  {
    "id": "ep-10-02",
    "code": "10-02",
    "title": "玻璃另一边的手",
    "synopsis": "读取 story 分支。全自动重新制作一篇题目：玻璃另一边的手。必须保留：\\n- 本篇属于《彼此的天上》EP002，承接EP001，不推翻系列Bible和人物关系弧\\n- 主角仍是二十多岁普通情侣，自驾旅行进入，不使用记者、调查员、研究人员等专业身份\\n- 全系列只保留一套空间局部重叠异常机制，不新增鬼、怪物、裂缝、维度解释或神秘组织\\n- 这集的核心必须从俗套的鬼手贴窗改成双向普通人接触：对面的人也在观察、理解和害怕我们\\n- 女友必须有一个普通、自然、可画的主动动作，对面要有直接回应，形成强动作-回应-后果传播核\\n- 高潮必须保留孩子想靠近，而对面成年人立刻把孩子拉走这一层，让观众意识到在对方视角里我们才是异常\\n- 不要用标准敲两下回两下的老套交流，可重新设计更生活化、更自然的动作回应\\n- 不要用线头等过强实体证据破坏留白，结尾以第二天现实空间复核和人物认知变化收束\\n- 默认20张，第一人称真实手机相册感，前3张必须同时建立旅行生活和直接可见异常\\n- 严格按仓库当前Story OS V2.5.1完成Story/Storyboard/Contracts/Visual Lock/Production/Review/Subtitles/Release/Final Snapshot，一直做到PUBLISH_READY，不要每一步询问我",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": "10_彼此的天上",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 19,
    "currentStage": "VISUAL_CALIBRATE",
    "stageProgressPercent": 95,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-09-06T23:09:03+08:00",
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
        "id": "char-10-02-P01",
        "name": "主角 (P01)",
        "role": "第一人称女主角 (POV 主体)",
        "avatar": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "faceEmbeddingId": "CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1",
        "consistencyScore": 98.8,
        "fixedCostume": "灰色连帽卫衣+深灰休闲长裤+普通运动鞋",
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
        "id": "VL-10-02-01",
        "title": "日常基准 (Ordinary Baseline 01)",
        "category": "主角面容基准",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "aspectRatio": "4:5 (1080×1350)",
        "focalLength": "50mm 自然人像视角",
        "colorGrade": "自然暖调纪实色温，胶片质感",
        "consistencyDelta": "0.00% (主参考点)",
        "isLocked": true,
        "version": "v2.6.1-RELEASE",
        "promptSnippet": "P02偏镜头带入P01"
      },
      {
        "id": "VL-10-02-02",
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
        "id": "VL-10-02-03",
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
        "id": "VL-10-02-04",
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
        "narration": "P02偏镜头带入P01",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-2",
        "beatIndex": 2,
        "sceneName": "第 2 镜 · F02",
        "act": "第一幕：建立日常",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "P02搭外套并提醒充电",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-3",
        "beatIndex": 3,
        "sceneName": "第 3 镜 · F03",
        "act": "第一幕：建立日常",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "P02指出外侧清晰区",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-4",
        "beatIndex": 4,
        "sceneName": "第 4 镜 · F04",
        "act": "第一幕：建立日常",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "P01关灯、P02横移",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-5",
        "beatIndex": 5,
        "sceneName": "第 5 镜 · F05",
        "act": "第一幕：建立日常",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "P02换位观察错位",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-6",
        "beatIndex": 6,
        "sceneName": "第 6 镜 · F06",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "P01把手机收回给P02看",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-7",
        "beatIndex": 7,
        "sceneName": "第 7 镜 · F07",
        "act": "第二幕：异常初显",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "P02蹲低观察",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-8",
        "beatIndex": 8,
        "sceneName": "第 8 镜 · F08",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "P02用袖口擦内雾",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-9",
        "beatIndex": 9,
        "sceneName": "第 9 镜 · F09",
        "act": "第二幕：异常初显",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "对面成年人擦开外侧水膜",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-10",
        "beatIndex": 10,
        "sceneName": "第 10 镜 · F10",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "双方从遮挡后互相探看",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-11",
        "beatIndex": 11,
        "sceneName": "第 11 镜 · F11",
        "act": "第二幕：异常初显",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P01抬手机、对面举布",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-12",
        "beatIndex": 12,
        "sceneName": "第 12 镜 · F12",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P02按低P01手腕",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-13",
        "beatIndex": 13,
        "sceneName": "第 13 镜 · F13",
        "act": "第三幕：危机爆发",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "孩子从成年人身后探出",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-14",
        "beatIndex": 14,
        "sceneName": "第 14 镜 · F14",
        "act": "第三幕：危机爆发",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P01按灭并压低手机，同时成年人抱离孩子",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-15",
        "beatIndex": 15,
        "sceneName": "第 15 镜 · F15",
        "act": "第三幕：危机爆发",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "成年人护住孩子并盖窗，机位继续下坠",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-16",
        "beatIndex": 16,
        "sceneName": "第 16 镜 · F16",
        "act": "第三幕：危机爆发",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "录像在机位压低后停止",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-17",
        "beatIndex": 17,
        "sceneName": "第 17 镜 · F17",
        "act": "第三幕：危机爆发",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P01递水，P02接过，二人低声复盘",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-18",
        "beatIndex": 18,
        "sceneName": "第 18 镜 · F18",
        "act": "第三幕：危机爆发",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P02在安全处指出昨夜窗位",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-19",
        "beatIndex": 19,
        "sceneName": "第 19 镜 · F19",
        "act": "终局：反转回响",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P01回看停录前短视频并复核无实体残留",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-20",
        "beatIndex": 20,
        "sceneName": "第 20 镜 · F20",
        "act": "终局：反转回响",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "P02拉门回看，P01拍完普通离店照后删除求证长消息",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      }
    ],
    "currentBatch": {
      "batchId": "batch-10-02-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-09-06T23:09:03+08:00",
      "status": "processing",
      "items": [
        {
          "id": "bi-1",
          "frameIndex": 1,
          "prompt": "P02偏镜头带入P01",
          "seed": 42001,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-2",
          "frameIndex": 2,
          "prompt": "P02搭外套并提醒充电",
          "seed": 42002,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-3",
          "frameIndex": 3,
          "prompt": "P02指出外侧清晰区",
          "seed": 42003,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-4",
          "frameIndex": 4,
          "prompt": "P01关灯、P02横移",
          "seed": 42004,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-5",
          "frameIndex": 5,
          "prompt": "P02换位观察错位",
          "seed": 42005,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-6",
          "frameIndex": 6,
          "prompt": "P01把手机收回给P02看",
          "seed": 42006,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-7",
          "frameIndex": 7,
          "prompt": "P02蹲低观察",
          "seed": 42007,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-8",
          "frameIndex": 8,
          "prompt": "P02用袖口擦内雾",
          "seed": 42008,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-9",
          "frameIndex": 9,
          "prompt": "对面成年人擦开外侧水膜",
          "seed": 42009,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-10",
          "frameIndex": 10,
          "prompt": "双方从遮挡后互相探看",
          "seed": 42010,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-11",
          "frameIndex": 11,
          "prompt": "P01抬手机、对面举布",
          "seed": 42011,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-12",
          "frameIndex": 12,
          "prompt": "P02按低P01手腕",
          "seed": 42012,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-13",
          "frameIndex": 13,
          "prompt": "孩子从成年人身后探出",
          "seed": 42013,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-14",
          "frameIndex": 14,
          "prompt": "P01按灭并压低手机，同时成年人抱离孩子",
          "seed": 42014,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-15",
          "frameIndex": 15,
          "prompt": "成年人护住孩子并盖窗，机位继续下坠",
          "seed": 42015,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-16",
          "frameIndex": 16,
          "prompt": "录像在机位压低后停止",
          "seed": 42016,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-17",
          "frameIndex": 17,
          "prompt": "P01递水，P02接过，二人低声复盘",
          "seed": 42017,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-18",
          "frameIndex": 18,
          "prompt": "P02在安全处指出昨夜窗位",
          "seed": 42018,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-19",
          "frameIndex": 19,
          "prompt": "P01回看停录前短视频并复核无实体残留",
          "seed": 42019,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-20",
          "frameIndex": 20,
          "prompt": "P02拉门回看，P01拍完普通离店照后删除求证长消息",
          "seed": 42020,
          "status": "qa_passed",
          "progress": 100,
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
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-2",
        "frameIndex": 2,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-3",
        "frameIndex": 3,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-4",
        "frameIndex": 4,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-5",
        "frameIndex": 5,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-6",
        "frameIndex": 6,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-7",
        "frameIndex": 7,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-8",
        "frameIndex": 8,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-9",
        "frameIndex": 9,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-10",
        "frameIndex": 10,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-12",
        "frameIndex": 12,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-13",
        "frameIndex": 13,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-14",
        "frameIndex": 14,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-15",
        "frameIndex": 15,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-16",
        "frameIndex": 16,
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "timestamp": "2026-09-06T23:09:03+08:00",
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
        "timestamp": "2026-09-06T23:09:03+08:00",
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
  },
  {
    "id": "ep-11-01",
    "code": "11-01",
    "title": "仲夏夜惊魂｜停电夜蜕壳",
    "synopsis": "11_仲夏夜惊魂 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": "11_仲夏夜惊魂",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 13,
    "currentStage": "READY_TO_PUBLISH",
    "stageProgressPercent": 65,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-09-04T12:18:17+08:00",
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
        "id": "char-11-01-P01",
        "name": "主角 (P01)",
        "role": "第一人称女主角 (POV 主体)",
        "avatar": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "faceEmbeddingId": "CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1",
        "consistencyScore": 98.8,
        "fixedCostume": "浅色碎花长袖上衣+深色长裤+旧布鞋（嫁衣下衬）",
        "lightingAnchor": "写实自然光照，胶片颗粒质感，严禁光滑塑料磨皮",
        "archetype": "普通年轻女性，略瘦，自然肤质可见细微纹理",
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
        "id": "VL-11-01-01",
        "title": "日常基准 (Ordinary Baseline 01)",
        "category": "主角面容基准",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "aspectRatio": "4:5 (1080×1350)",
        "focalLength": "50mm 自然人像视角",
        "colorGrade": "自然暖调纪实色温，胶片质感",
        "consistencyDelta": "0.00% (主参考点)",
        "isLocked": true,
        "version": "v2.6.1-RELEASE",
        "promptSnippet": "门口留影机位：P01在门口面向镜头，黑发红绳，浅色碎花长袖，神情平和微怔。"
      },
      {
        "id": "VL-11-01-02",
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
        "id": "VL-11-01-03",
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
        "id": "VL-11-01-04",
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
        "narration": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-2",
        "beatIndex": 2,
        "sceneName": "第 2 镜 · F02",
        "act": "第一幕：建立日常",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-3",
        "beatIndex": 3,
        "sceneName": "第 3 镜 · F03",
        "act": "第一幕：建立日常",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-4",
        "beatIndex": 4,
        "sceneName": "第 4 镜 · F04",
        "act": "第一幕：建立日常",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-5",
        "beatIndex": 5,
        "sceneName": "第 5 镜 · F05",
        "act": "第一幕：建立日常",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-6",
        "beatIndex": 6,
        "sceneName": "第 6 镜 · F06",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-7",
        "beatIndex": 7,
        "sceneName": "第 7 镜 · F07",
        "act": "第二幕：异常初显",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-8",
        "beatIndex": 8,
        "sceneName": "第 8 镜 · F08",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-9",
        "beatIndex": 9,
        "sceneName": "第 9 镜 · F09",
        "act": "第二幕：异常初显",
        "shotType": "主观 POV 移动镜头",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-10",
        "beatIndex": 10,
        "sceneName": "第 10 镜 · F10",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "纪实室内暖光",
        "narration": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-11",
        "beatIndex": 11,
        "sceneName": "第 11 镜 · F11",
        "act": "第二幕：异常初显",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-12",
        "beatIndex": 12,
        "sceneName": "第 12 镜 · F12",
        "act": "第二幕：异常初显",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-13",
        "beatIndex": 13,
        "sceneName": "第 13 镜 · F13",
        "act": "第三幕：危机爆发",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-14",
        "beatIndex": 14,
        "sceneName": "第 14 镜 · F14",
        "act": "第三幕：危机爆发",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-15",
        "beatIndex": 15,
        "sceneName": "第 15 镜 · F15",
        "act": "第三幕：危机爆发",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-16",
        "beatIndex": 16,
        "sceneName": "第 16 镜 · F16",
        "act": "第三幕：危机爆发",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-17",
        "beatIndex": 17,
        "sceneName": "第 17 镜 · F17",
        "act": "第三幕：危机爆发",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-18",
        "beatIndex": 18,
        "sceneName": "第 18 镜 · F18",
        "act": "第三幕：危机爆发",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-19",
        "beatIndex": 19,
        "sceneName": "第 19 镜 · F19",
        "act": "终局：反转回响",
        "shotType": "主观 POV 移动镜头",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      },
      {
        "id": "beat-20",
        "beatIndex": 20,
        "sceneName": "第 20 镜 · F20",
        "act": "终局：反转回响",
        "shotType": "特写细节",
        "lighting": "低照度环境光 / 雨夜投影",
        "narration": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      }
    ],
    "currentBatch": {
      "batchId": "batch-11-01-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-09-04T12:18:17+08:00",
      "status": "completed",
      "items": [
        {
          "id": "bi-1",
          "frameIndex": 1,
          "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42001,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-2",
          "frameIndex": 2,
          "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42002,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-3",
          "frameIndex": 3,
          "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42003,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-4",
          "frameIndex": 4,
          "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42004,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-5",
          "frameIndex": 5,
          "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42005,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-6",
          "frameIndex": 6,
          "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42006,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-7",
          "frameIndex": 7,
          "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42007,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-8",
          "frameIndex": 8,
          "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42008,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-9",
          "frameIndex": 9,
          "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42009,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-10",
          "frameIndex": 10,
          "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42010,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-11",
          "frameIndex": 11,
          "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42011,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-12",
          "frameIndex": 12,
          "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42012,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-13",
          "frameIndex": 13,
          "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42013,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-14",
          "frameIndex": 14,
          "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42014,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-15",
          "frameIndex": 15,
          "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42015,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-16",
          "frameIndex": 16,
          "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42016,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-17",
          "frameIndex": 17,
          "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42017,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-18",
          "frameIndex": 18,
          "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42018,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-19",
          "frameIndex": 19,
          "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42019,
          "status": "qa_passed",
          "progress": 100,
          "renderTime": "38s",
          "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
          "consistencyScore": 98.5
        },
        {
          "id": "bi-20",
          "frameIndex": 20,
          "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
          "seed": 42020,
          "status": "qa_passed",
          "progress": 100,
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-2",
        "frameIndex": 2,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-9",
        "frameIndex": 9,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-10",
        "frameIndex": 10,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-14",
        "frameIndex": 14,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-15",
        "frameIndex": 15,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-17",
        "frameIndex": 17,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-18",
        "frameIndex": 18,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "comment": "首帧Worker异常已自动重试并通过，面容质感真实自然。"
      },
      {
        "frameId": "fr-19",
        "frameIndex": 19,
        "timestamp": "2026-09-04T12:18:17+08:00",
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
        "timestamp": "2026-09-04T12:18:17+08:00",
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
  },
  {
    "id": "ep-11-01-RE",
    "code": "11-01-RE",
    "title": "仲夏夜惊魂 重制版",
    "synopsis": "11_仲夏夜惊魂 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": "11_仲夏夜惊魂",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 0,
    "currentStage": "IDEA_LOCK",
    "stageProgressPercent": 0,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-09-02T20:10:51+08:00",
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
        "id": "char-11-01-RE-P01",
        "name": "主角 (P01)",
        "role": "第一人称女主角 (POV 主体)",
        "avatar": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "faceEmbeddingId": "CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1",
        "consistencyScore": 98.8,
        "fixedCostume": "白色短袖+浅色牛仔裤+深色运动鞋",
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
        "id": "VL-11-01-RE-01",
        "title": "日常基准 (Ordinary Baseline 01)",
        "category": "主角面容基准",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "aspectRatio": "4:5 (1080×1350)",
        "focalLength": "50mm 自然人像视角",
        "colorGrade": "自然暖调纪实色温，胶片质感",
        "consistencyDelta": "0.00% (主参考点)",
        "isLocked": true,
        "version": "v2.6.1-RELEASE",
        "promptSnippet": "到村口停车，妹妹从路灯下小跑过来上车；顺手拍了段村口夜路发家庭群报平安"
      },
      {
        "id": "VL-11-01-RE-02",
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
        "id": "VL-11-01-RE-03",
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
        "id": "VL-11-01-RE-04",
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
        "narration": "到村口停车，妹妹从路灯下小跑过来上车；顺手拍了段村口夜路发家庭群报平安",
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
        "narration": "妹妹坐后座，P01 一手扶把一手拍前方夜路，灯下飞虫从镜头前掠过",
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
        "narration": "停好车后随手拍：门灯亮着，门槛边没收的竹椅，画面下缘带到他自己的鞋与裤脚",
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
        "narration": "妹妹切好西瓜端来，P01 坐着边吃边拍，桌上有冰绿豆汤与烧着的蚊香",
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
        "narration": "两人在门口乘凉说话，妹妹扇蒲扇赶蚊子，P01 把这段拍下来",
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
        "narration": "妹妹说巷口路灯早坏了没人修，P01 走去巷口，发现那盏灯亮着",
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
        "narration": "走近那根旧灯杆，发现它比记忆里更靠墙、歪的方向也不对，杆根地面却干干净净",
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
        "narration": "妹妹出来找 P01，两人说起路灯的事，她确认那盏灯坏了大半年没人修，一起再往巷口看",
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
        "narration": "再走近看：杆是歪的，杆根地面没有撞击痕迹也没有修补痕迹，两人都安静下来",
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
        "narration": "回家路上妹妹突然停住：老槐树本该在院墙右边，现在树和树影都在墙的左边，方向整个反了",
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
        "narration": "到村口小卖部想买水，卷帘门拉着却从门缝透出光，拍门没人应，屋里像有收音机声",
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
        "narration": "两人骑电动车沿村道走，头顶路灯一盏接一盏熄掉，最后整段路黑下来，只剩车灯一小片光",
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
        "narration": "回到自家院门，发现出门前关掉的堂屋灯亮着，窗里挂钟像停摆，两人愣在门口不敢动",
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
        "narration": "两人决定连夜去镇上住一晚；妹妹弯腰锁院门，P01 拿手电帮她照着并拍下来",
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
        "narration": "按原路往镇上骑，却到了从没见过的下坡水泥路，路边并排停着落灰的三轮车，坡底看不到头",
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
        "narration": "掉头往回骑想回村，路口却也对不上，来时的村口灯火消失了，只剩成排延伸的电线杆",
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
        "narration": "前面又是那棵歪脖子老槐树，树下同一只狗趴着不动，这是第三次经过同一处；P01 急刹停住",
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
        "narration": "两人下车推着电动车沿电线杆走，谁都没说话，只听脚步和电瓶车轻微的电流声",
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
        "narration": "远处传来拖拉机声，灯光直直扫过来，两人站到路肩让车；强光过后，路变得认得了",
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
        "narration": "不知怎么就走回了自家院门口；门灯下妹妹回头笑了一下，两人进院坐下，堂屋灯正常亮着",
        "status": "rendering",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      }
    ],
    "currentBatch": {
      "batchId": "batch-11-01-RE-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-09-02T20:10:51+08:00",
      "status": "processing",
      "items": [
        {
          "id": "bi-1",
          "frameIndex": 1,
          "prompt": "到村口停车，妹妹从路灯下小跑过来上车；顺手拍了段村口夜路发家庭群报平安",
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
          "prompt": "妹妹坐后座，P01 一手扶把一手拍前方夜路，灯下飞虫从镜头前掠过",
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
          "prompt": "停好车后随手拍：门灯亮着，门槛边没收的竹椅，画面下缘带到他自己的鞋与裤脚",
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
          "prompt": "妹妹切好西瓜端来，P01 坐着边吃边拍，桌上有冰绿豆汤与烧着的蚊香",
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
          "prompt": "两人在门口乘凉说话，妹妹扇蒲扇赶蚊子，P01 把这段拍下来",
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
          "prompt": "妹妹说巷口路灯早坏了没人修，P01 走去巷口，发现那盏灯亮着",
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
          "prompt": "走近那根旧灯杆，发现它比记忆里更靠墙、歪的方向也不对，杆根地面却干干净净",
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
          "prompt": "妹妹出来找 P01，两人说起路灯的事，她确认那盏灯坏了大半年没人修，一起再往巷口看",
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
          "prompt": "再走近看：杆是歪的，杆根地面没有撞击痕迹也没有修补痕迹，两人都安静下来",
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
          "prompt": "回家路上妹妹突然停住：老槐树本该在院墙右边，现在树和树影都在墙的左边，方向整个反了",
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
          "prompt": "到村口小卖部想买水，卷帘门拉着却从门缝透出光，拍门没人应，屋里像有收音机声",
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
          "prompt": "两人骑电动车沿村道走，头顶路灯一盏接一盏熄掉，最后整段路黑下来，只剩车灯一小片光",
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
          "prompt": "回到自家院门，发现出门前关掉的堂屋灯亮着，窗里挂钟像停摆，两人愣在门口不敢动",
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
          "prompt": "两人决定连夜去镇上住一晚；妹妹弯腰锁院门，P01 拿手电帮她照着并拍下来",
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
          "prompt": "按原路往镇上骑，却到了从没见过的下坡水泥路，路边并排停着落灰的三轮车，坡底看不到头",
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
          "prompt": "掉头往回骑想回村，路口却也对不上，来时的村口灯火消失了，只剩成排延伸的电线杆",
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
          "prompt": "前面又是那棵歪脖子老槐树，树下同一只狗趴着不动，这是第三次经过同一处；P01 急刹停住",
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
          "prompt": "两人下车推着电动车沿电线杆走，谁都没说话，只听脚步和电瓶车轻微的电流声",
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
          "prompt": "远处传来拖拉机声，灯光直直扫过来，两人站到路肩让车；强光过后，路变得认得了",
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
          "prompt": "不知怎么就走回了自家院门口；门灯下妹妹回头笑了一下，两人进院坐下，堂屋灯正常亮着",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
        "timestamp": "2026-09-02T20:10:51+08:00",
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
  },
  {
    "id": "ep-MR-01",
    "code": "MR-01",
    "title": "埋儿那天，娘把我拦住了",
    "synopsis": ". 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": ".",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 0,
    "currentStage": "IDEA_LOCK",
    "stageProgressPercent": 0,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-09-16T17:35:28+08:00",
    "runtimeRequest": {
      "imageModel": "gpt-image-2.5-flare",
      "quality": "high",
      "aspectRatio": "4:5 1080×1350",
      "batchMode": "5 帧逻辑批次 (DAG 并发调度)",
      "maxConcurrentImages": 3,
      "executionLayer": "StoryOS 2.6.1 Engine",
      "sourceBadge": "已连接生产内核"
    },
    "characters": [
      {
        "id": "char-MR-01-P01",
        "name": "主角 (P01)",
        "role": "第一人称女主角 (POV 主体)",
        "avatar": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "faceEmbeddingId": "CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1",
        "consistencyScore": 98.8,
        "fixedCostume": "浅色碎花长袖上衣+深色长裤+旧布鞋（嫁衣下衬）",
        "lightingAnchor": "写实自然光照，胶片颗粒质感，严禁光滑塑料磨皮",
        "archetype": "普通年轻女性，略瘦，自然肤质可见细微纹理",
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
        "id": "VL-MR-01-01",
        "title": "日常基准 (Ordinary Baseline 01)",
        "category": "主角面容基准",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "aspectRatio": "4:5 (1080×1350)",
        "focalLength": "50mm 自然人像视角",
        "colorGrade": "自然暖调纪实色温，胶片质感",
        "consistencyDelta": "0.00% (主参考点)",
        "isLocked": true,
        "version": "v2.6.1-RELEASE",
        "promptSnippet": "门口留影机位：P01在门口面向镜头，黑发红绳，浅色碎花长袖，神情平和微怔。"
      },
      {
        "id": "VL-MR-01-02",
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
        "id": "VL-MR-01-03",
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
        "id": "VL-MR-01-04",
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
        "narration": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "narration": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "status": "rendering",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      }
    ],
    "currentBatch": {
      "batchId": "batch-MR-01-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-09-16T17:35:28+08:00",
      "status": "processing",
      "items": [
        {
          "id": "bi-1",
          "frameIndex": 1,
          "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
          "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
        "timestamp": "2026-09-16T17:35:28+08:00",
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
  }
];
