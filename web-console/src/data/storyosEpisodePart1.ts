// 只读历史 Episode 证据分组；正式生产状态以 Runtime API 为准。
import type { Episode } from '../types';
export const EPISODE_PART_1: Episode[] = [
  {
    "id": "ep-09-04",
    "code": "09-04",
    "title": "瓶中世界",
    "synopsis": "老旧柜顶上的一只透明玻璃瓶，收纳着三十年前一整个村庄失踪前的最后回响与微缩活景。",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": "09_旧物怪谈",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 0,
    "currentStage": "READY_TO_PUBLISH",
    "stageProgressPercent": 0,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-08-28T21:41:43-04:00",
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
        "id": "char-09-04-P01",
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
        "id": "VL-09-04-01",
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
        "id": "VL-09-04-02",
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
        "id": "VL-09-04-03",
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
        "id": "VL-09-04-04",
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
      "batchId": "batch-09-04-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
        "timestamp": "2026-08-28T21:41:43-04:00",
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
    "id": "ep-09-05",
    "code": "09-05",
    "title": "婚礼前夜",
    "synopsis": "漏服被说成助眠的药后，女主从婚礼物件和空间中确认自己正在被限制并可能被运走；她拒绝下一剂药、主动制造机会逃到检查站，却仍失去自己的名字，结尾以另一场试鞋梦和旧房间细节回返保留获救真伪的双解释。",
    "logline": "从婚前夜的轻微记忆缺口与不安，逐步升级为确认被控制的恐惧和主动反抗；获救后仍以失名与现实不确定性留下余悸。",
    "genre": "09_旧物怪谈",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 3,
    "currentStage": "READY_TO_PUBLISH",
    "stageProgressPercent": 15,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-09-09T11:10:58+08:00",
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
        "id": "char-09-05-P01",
        "name": "新娘 (P01)",
        "role": "第一人称女主角 (POV 主体)",
        "avatar": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "faceEmbeddingId": "CN_MAINLAND_YOUNG_ADULT_DEFAULT_V1",
        "consistencyScore": 98.8,
        "fixedCostume": "浅色碎花长袖上衣+深色长裤+旧布鞋（嫁衣下衬）",
        "lightingAnchor": "写实自然光照，胶片颗粒质感，严禁光滑塑料磨皮",
        "archetype": "普通年轻女性，略瘦",
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
        "id": "VL-09-05-01",
        "title": "日常基准 (Ordinary Baseline 01)",
        "category": "主角面容基准",
        "imageUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "aspectRatio": "4:5 (1080×1350)",
        "focalLength": "50mm 自然人像视角",
        "colorGrade": "自然暖调纪实色温，胶片质感",
        "consistencyDelta": "0.00% (主参考点)",
        "isLocked": true,
        "version": "v2.6.1-RELEASE",
        "promptSnippet": "P01站在婚房门口对镜头，正面看向相机（持机者为院里男方，用她的卡片机拍婚前夜留影）；黑发红绳、浅色碎花长袖、深色裤、旧布鞋，神情平和微怔。身后婚房红彤彤：红被铺好的木床、桌边亲友整理搪瓷盆与红绸，喜字与红布窗完整，土墙可见。无药瓶、药片、铁栏或锁链。"
      },
      {
        "id": "VL-09-05-02",
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
        "id": "VL-09-05-03",
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
        "id": "VL-09-05-04",
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
        "narration": "P01站在婚房门口对镜头，正面看向相机（持机者为院里男方，用她的卡片机拍婚前夜留影）；黑发红绳、浅色碎花长袖、深色裤、旧布鞋，神情平和微怔。身后婚房红彤彤：红被铺好的木床、桌边亲友整理搪瓷盆与红绸，喜字与红布窗完整，土墙可见。无药瓶、药片、铁栏或锁链。",
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
        "narration": "P01坐在床边，左手正在收拾针线，桌角有普通水杯、纸巾和一粒未动的药。小白瓶放在桌角远侧，男人在背景搬被褥；没有递瓶、盯视或按住她。",
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
        "narration": "梦境主观向下看自己的深色裤脚和旧布鞋：脚边一截短铁链被扯直伸入床底，链条两端都在画外。链与床脚接触处清晰，无法判断连着什么。无脚镣全貌、无药、无看守脸。",
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
        "narration": "同一梦境，P01俯视碎花袖口，一只陌生成年人的手压住她的左手，木床沿可见；来者全身与脸均在画外，袖口也不露。没有瓶杯、嘴部、灌药或完整锁链。",
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
        "narration": "现实醒来，P01坐在床沿低头，左手掀开一角被子，自己裸露脚踝上有一圈浅红压痕；同一深色裤脚，旧布鞋在床边。门口男人背影在忙，无药无铁环，不做梦中动作匹配。",
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
        "narration": "P01从座位向前看，左手拿着纸，男人在桌对面侧身指向纸张，纸面只有失焦笔迹；婚房布置连续。不能从背后拍女主，也不出现她的脸。",
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
        "narration": "P01坐在梳妆镜前，左右亲友整理发绳与喜被，交谈各做各事；镜子只带到女主碎花肩袖与发尾。她的姓名不在画面中，禁止生成人物对话文字。",
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
        "narration": "从P01眼位看梳妆镜，陌生中年女人站在身后梳头，镜中可辨女人脸与梳子；P01自己的脸被镜面上缘裁出，仅见同一碎花肩袖、红绳黑发。",
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
        "narration": "P01坐在床边左手翻转红绣鞋，使鞋底两道铁环朝向镜头；右手持机不入画，碎花袖、深色裤和自己的旧布鞋连续。铁环只在鞋上，不套在她脚上。",
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
        "narration": "P01左掌托着一只尚未扣合的金色手镯，内侧合缝与小锁孔清晰，另一只放桌上；碎花袖口可见。不是已锁在手腕上的镯子，不展示开锁步骤。",
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
        "narration": "P01左手掀起窗上的红布一角，布后露出横贯窗洞、固定在窗框内的铁栏，栏与窗框连接关系清晰；完整红布在其余区域仍遮挡。一次发现动作，无回头蒙太奇，不以土墙为新证据。",
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
        "narration": "P01站在屋内门缝后向院里看，前景只有门框和一点碎花袖。男人在货车后门旁，车厢内几个成年女孩穿红嫁衣，脚踝铁环能看清；女主始终在屋里，不坐车厢，不穿红嫁衣。",
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
        "narration": "P01站在屋内床侧，男人的手把一粒药与水杯递近，小白瓶在他另一手里；他侧身挡住前门方向。此时才把药与控制关系明确并置，不做仰头强灌。",
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
        "narration": "P01从自己的眼位俯向床头旧花盆，左手扶盆沿，刚吐出的药落在湿土表面；背景男人侧后身转向前门。女主嘴脸不入画，不画手指把药丢进盆里。",
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
        "narration": "P01左手举起那只未扣合金镯对着男人，镯口与锁孔可见；男人停下并伸手来抢，身后前门被挡住，左侧通后门的窄道和矮凳清楚。无女主正脸，无凭空解锁。",
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
        "narration": "P01从后门门槛向田路冲出，画面下缘同一深色裤脚与旧布鞋沾泥，碎花袖左手推门，回侧余光见翻倒的矮凳挡在追来的男人脚前。无第三人称跑步全身，无换装、无突然赤脚、无救场女孩。",
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
        "narration": "P01坐在检查站桌边，从自己眼位看记录人员和桌面，低处可见同一沾泥旧布鞋与深色裤脚，碎花袖左手停在桌沿。无白婚纱，无脚镣，无女主面部。",
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
        "narration": "检查站同一座位，P01转向窗外，自己碎花左袖扶窗沿，花白头发女人被人搀着走来，神情急切；无女主脸，无白婚纱，不声称她已完整恢复记忆。",
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
        "narration": "另一梦境，P01坐在明亮普通卧室的凳子上，第一人称俯视左手翻起红绣鞋鞋底，没有铁环。低位镜子仅反射同一坐姿的深色裤腿、碎花袖与红鞋，左右按镜面对应，脸和持机手在镜框外。",
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
        "narration": "P01躺在床上主观仰视斑驳天花板，侧下缘一点碎花袖和红被；与先前婚房相同的墙角裂痕和红布窗边可辨。小白瓶在远侧床头桌边，无标签，静默；不新增锁链、不替观众断言获救全是假。",
        "status": "approved",
        "thumbnailUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E"
      }
    ],
    "currentBatch": {
      "batchId": "batch-09-05-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-09-09T11:10:58+08:00",
      "status": "completed",
      "items": [
        {
          "id": "bi-1",
          "frameIndex": 1,
          "prompt": "P01站在婚房门口对镜头，正面看向相机（持机者为院里男方，用她的卡片机拍婚前夜留影）；黑发红绳、浅色碎花长袖、深色裤、旧布鞋，神情平和微怔。身后婚房红彤彤：红被铺好的木床、桌边亲友整理搪瓷盆与红绸，喜字与红布窗完整，土墙可见。无药瓶、药片、铁栏或锁链。",
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
          "prompt": "P01坐在床边，左手正在收拾针线，桌角有普通水杯、纸巾和一粒未动的药。小白瓶放在桌角远侧，男人在背景搬被褥；没有递瓶、盯视或按住她。",
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
          "prompt": "梦境主观向下看自己的深色裤脚和旧布鞋：脚边一截短铁链被扯直伸入床底，链条两端都在画外。链与床脚接触处清晰，无法判断连着什么。无脚镣全貌、无药、无看守脸。",
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
          "prompt": "同一梦境，P01俯视碎花袖口，一只陌生成年人的手压住她的左手，木床沿可见；来者全身与脸均在画外，袖口也不露。没有瓶杯、嘴部、灌药或完整锁链。",
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
          "prompt": "现实醒来，P01坐在床沿低头，左手掀开一角被子，自己裸露脚踝上有一圈浅红压痕；同一深色裤脚，旧布鞋在床边。门口男人背影在忙，无药无铁环，不做梦中动作匹配。",
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
          "prompt": "P01从座位向前看，左手拿着纸，男人在桌对面侧身指向纸张，纸面只有失焦笔迹；婚房布置连续。不能从背后拍女主，也不出现她的脸。",
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
          "prompt": "P01坐在梳妆镜前，左右亲友整理发绳与喜被，交谈各做各事；镜子只带到女主碎花肩袖与发尾。她的姓名不在画面中，禁止生成人物对话文字。",
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
          "prompt": "从P01眼位看梳妆镜，陌生中年女人站在身后梳头，镜中可辨女人脸与梳子；P01自己的脸被镜面上缘裁出，仅见同一碎花肩袖、红绳黑发。",
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
          "prompt": "P01坐在床边左手翻转红绣鞋，使鞋底两道铁环朝向镜头；右手持机不入画，碎花袖、深色裤和自己的旧布鞋连续。铁环只在鞋上，不套在她脚上。",
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
          "prompt": "P01左掌托着一只尚未扣合的金色手镯，内侧合缝与小锁孔清晰，另一只放桌上；碎花袖口可见。不是已锁在手腕上的镯子，不展示开锁步骤。",
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
          "prompt": "P01左手掀起窗上的红布一角，布后露出横贯窗洞、固定在窗框内的铁栏，栏与窗框连接关系清晰；完整红布在其余区域仍遮挡。一次发现动作，无回头蒙太奇，不以土墙为新证据。",
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
          "prompt": "P01站在屋内门缝后向院里看，前景只有门框和一点碎花袖。男人在货车后门旁，车厢内几个成年女孩穿红嫁衣，脚踝铁环能看清；女主始终在屋里，不坐车厢，不穿红嫁衣。",
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
          "prompt": "P01站在屋内床侧，男人的手把一粒药与水杯递近，小白瓶在他另一手里；他侧身挡住前门方向。此时才把药与控制关系明确并置，不做仰头强灌。",
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
          "prompt": "P01从自己的眼位俯向床头旧花盆，左手扶盆沿，刚吐出的药落在湿土表面；背景男人侧后身转向前门。女主嘴脸不入画，不画手指把药丢进盆里。",
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
          "prompt": "P01左手举起那只未扣合金镯对着男人，镯口与锁孔可见；男人停下并伸手来抢，身后前门被挡住，左侧通后门的窄道和矮凳清楚。无女主正脸，无凭空解锁。",
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
          "prompt": "P01从后门门槛向田路冲出，画面下缘同一深色裤脚与旧布鞋沾泥，碎花袖左手推门，回侧余光见翻倒的矮凳挡在追来的男人脚前。无第三人称跑步全身，无换装、无突然赤脚、无救场女孩。",
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
          "prompt": "P01坐在检查站桌边，从自己眼位看记录人员和桌面，低处可见同一沾泥旧布鞋与深色裤脚，碎花袖左手停在桌沿。无白婚纱，无脚镣，无女主面部。",
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
          "prompt": "检查站同一座位，P01转向窗外，自己碎花左袖扶窗沿，花白头发女人被人搀着走来，神情急切；无女主脸，无白婚纱，不声称她已完整恢复记忆。",
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
          "prompt": "另一梦境，P01坐在明亮普通卧室的凳子上，第一人称俯视左手翻起红绣鞋鞋底，没有铁环。低位镜子仅反射同一坐姿的深色裤腿、碎花袖与红鞋，左右按镜面对应，脸和持机手在镜框外。",
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
          "prompt": "P01躺在床上主观仰视斑驳天花板，侧下缘一点碎花袖和红被；与先前婚房相同的墙角裂痕和红布窗边可辨。小白瓶在远侧床头桌边，无标签，静默；不新增锁链、不替观众断言获救全是假。",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "timestamp": "2026-09-09T11:10:58+08:00",
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
        "frameId": "fr-20",
        "frameIndex": 20,
        "timestamp": "2026-09-09T11:10:58+08:00",
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
    "id": "ep-10-01",
    "code": "10-01",
    "title": "鳌太线·热汤",
    "synopsis": "鳌太穿越遇险记录，狂风暴雪中一间违背常理的护林员石屋，炉子上煮着滚烫的热汤。",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": "10_山难伪纪录片",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 0,
    "currentStage": "READY_TO_PUBLISH",
    "stageProgressPercent": 0,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-08-30T14:00:42+08:00",
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
        "id": "char-10-01-P01",
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
        "id": "VL-10-01-01",
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
        "id": "VL-10-01-02",
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
        "id": "VL-10-01-03",
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
        "id": "VL-10-01-04",
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
      "batchId": "batch-10-01-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
        "timestamp": "2026-08-30T14:00:42+08:00",
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
    "id": "ep-10-B01",
    "code": "10-B01",
    "title": "不存在的夜行路",
    "synopsis": "10_彼此的天上 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
    "logline": "在日常与异常的边界徘徊，揭示隐秘冰冷的规则真相。",
    "genre": "10_彼此的天上",
    "targetAudience": "悬疑怪谈爱好者 / 抖音短剧高完播人群",
    "totalFrames": 20,
    "completedFrames": 0,
    "currentStage": "IDEA_LOCK",
    "stageProgressPercent": 0,
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "updatedAt": "2026-09-03T18:28:02+08:00",
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
        "id": "char-10-B01-P01",
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
        "id": "VL-10-B01-01",
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
        "id": "VL-10-B01-02",
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
        "id": "VL-10-B01-03",
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
        "id": "VL-10-B01-04",
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
      "batchId": "batch-10-B01-final",
      "batchNumber": 4,
      "batchName": "全量 20 帧成片批次",
      "targetFrames": "01-20",
      "totalImages": 20,
      "createdAt": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
        "timestamp": "2026-09-03T18:28:02+08:00",
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
