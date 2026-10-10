import type { Episode } from '../types';
// 历史 Episode 只读完整证据，按选择再加载，不代表实时 Runtime 状态。
export const EPISODE_DETAIL: Episode = {
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
};
