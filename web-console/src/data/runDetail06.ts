import type { StoryRunItem } from '../types';
// 历史 Run 只读详情，不代表当前 Runtime 心跳或真实可执行操作。
export const RUN_DETAIL: StoryRunItem = {
  "id": "run-11-01",
  "storyName": "仲夏夜惊魂｜停电夜蜕壳",
  "runId": "RUN-11-01-PUBLISH_READY",
  "currentStage": "PUBLISH",
  "stageLabel": "PUBLISH_READY",
  "status": "COMPLETED",
  "progressPercent": 65,
  "completedFrames": 13,
  "totalFrames": 20,
  "currentAction": "Release Preflight PASS · 发布决策 GO",
  "createdAt": "2026-08-31T14:20:00+08:00",
  "duration": "28m",
  "lastHeartbeatAgo": "2 秒前",
  "heartbeatSeconds": 2,
  "exceptionSummary": "Auto-Recovered: Frame 01 worker retry passed",
  "exceptionType": "none",
  "storyDescription": "11_仲夏夜惊魂 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
  "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
  "frames": [
    {
      "frameNo": 1,
      "frameCode": "F01",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: name 'ROOT' is not defined",
      "failureStage": "image_worker",
      "failedAt": "2026-09-03T18:52:42+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "01_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-01",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 2,
      "frameCode": "F02",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "02_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-02",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 3,
      "frameCode": "F03",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "03_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-03",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 4,
      "frameCode": "F04",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "04_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-04",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 5,
      "frameCode": "F05",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "05_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-05",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 6,
      "frameCode": "F06",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "06_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-06",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 7,
      "frameCode": "F07",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "07_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-07",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 8,
      "frameCode": "F08",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\11_仲夏夜惊魂\\01_停电夜蜕壳\\meta\\image-workers\\08-1346498c0270-a1.jsonl",
      "failureStage": "image_worker",
      "failedAt": "2026-09-04T04:50:41+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "08_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-08",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 9,
      "frameCode": "F09",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\11_仲夏夜惊魂\\01_停电夜蜕壳\\meta\\image-workers\\09-8d8d8d93b7ac-a1.jsonl",
      "failureStage": "image_worker",
      "failedAt": "2026-09-04T04:52:39+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "09_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-09",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 10,
      "frameCode": "F10",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "10_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-10",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 11,
      "frameCode": "F11",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "11_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-11",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 12,
      "frameCode": "F12",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "12_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-12",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 13,
      "frameCode": "F13",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\11_仲夏夜惊魂\\01_停电夜蜕壳\\meta\\image-workers\\13-773823bfbaf1-a1.jsonl",
      "failureStage": "image_worker",
      "failedAt": "2026-09-04T01:37:06+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "13_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-13",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 14,
      "frameCode": "F14",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\11_仲夏夜惊魂\\01_停电夜蜕壳\\meta\\image-workers\\14-e2ea318289a5-a1.jsonl",
      "failureStage": "image_worker",
      "failedAt": "2026-09-04T01:38:29+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "14_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-14",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 15,
      "frameCode": "F15",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "15_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-15",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 16,
      "frameCode": "F16",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "BATCH_TRANSPORT_FAILURE: BATCH_RESULT_MAPPING_MISMATCH: missing or invalid out-01.png",
      "failureStage": "image_worker",
      "failedAt": "2026-09-04T00:05:32+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "16_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-16",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 17,
      "frameCode": "F17",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=1; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\11_仲夏夜惊魂\\01_停电夜蜕壳\\meta\\image-workers\\17-966c9f8f2f9f-a1.jsonl",
      "failureStage": "image_worker",
      "failedAt": "2026-09-03T22:26:14+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "17_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-17",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 18,
      "frameCode": "F18",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "2 / 2",
      "currentSubAction": "IMAGE_GENERATION",
      "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\11_仲夏夜惊魂\\01_停电夜蜕壳\\meta\\image-workers\\18-f478434cff0a-a1.jsonl",
      "failureStage": "image_worker",
      "failedAt": "2026-09-04T04:43:24+08:00",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "18_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-18",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Technical Retry Executed",
          "type": "error"
        }
      ]
    },
    {
      "frameNo": 19,
      "frameCode": "F19",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "19_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-19",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    },
    {
      "frameNo": 20,
      "frameCode": "F20",
      "status": "PASSED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "IMAGE_GENERATION",
      "completedAt": "2026-09-04T12:18:17+08:00",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "20_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-11-01-20",
      "recentEvents": [
        {
          "time": "10:20:00",
          "text": "Prompt Directive Compiled",
          "type": "schedule"
        },
        {
          "time": "10:20:15",
          "text": "Worker Dispatched (Codex Pool)",
          "type": "start"
        },
        {
          "time": "10:20:45",
          "text": "Frame Acceptance Passed",
          "type": "success"
        }
      ]
    }
  ],
  "pipelineStages": [
    {
      "key": "CREATE",
      "label": "选题锁定 (Idea Lock)",
      "status": "completed",
      "timeCost": "1m",
      "startTime": "2026-08-31T14:20:00+08:00",
      "endTime": "2026-08-31T14:20:00+08:00",
      "attempt": "1/1",
      "description": "Concept Ambition + Character Contract + Recent-5 + NO-ANOMALY delegated preproduction review PASS",
      "inputArtifacts": [
        "runtime-request.json"
      ],
      "outputArtifacts": [
        "episode-state.json",
        "concept-ambition-review.json"
      ],
      "traceId": "TR-IDEA-11-01"
    },
    {
      "key": "STORY_LOCK",
      "label": "分镜锁定 (Storyboard Lock)",
      "status": "completed",
      "timeCost": "14m",
      "startTime": "2026-08-31T14:20:00+08:00",
      "endTime": "2026-08-31T14:20:00+08:00",
      "attempt": "1/1",
      "description": "Story/Storyboard/Environment/Impact/Resolved Frame Contracts preproduction complete; no image generation",
      "inputArtifacts": [
        "story-dna-trace.json"
      ],
      "outputArtifacts": [
        "shot-progression-review.json",
        "story-gates.json"
      ],
      "traceId": "TR-STORY-11-01"
    },
    {
      "key": "VISUAL_LOCK",
      "label": "视觉校准 (Visual Calibrate)",
      "status": "completed",
      "timeCost": "1h 05m",
      "startTime": "2026-09-04T00:58:35+08:00",
      "endTime": "2026-09-04T00:58:35+08:00",
      "attempt": "1/1",
      "description": "V2.1 四准入帧 1/15/6/17 统一 Critic AVAILABLE_PASS；Visual Lock V2.1 verify PASS；delegated story/visual lock 重锚后证据门禁通过",
      "inputArtifacts": [
        "character-contract.json",
        "character-appearance-anchor.json"
      ],
      "outputArtifacts": [
        "visual-lock-admissions.json",
        "visual-final-freeze.json"
      ],
      "traceId": "TR-VISUAL-11-01"
    },
    {
      "key": "PRODUCTION",
      "label": "制作执行 (Production)",
      "status": "completed",
      "timeCost": "1h 01m",
      "startTime": "2026-09-04T11:25:44+08:00",
      "endTime": "2026-09-04T11:25:44+08:00",
      "attempt": "1/1",
      "description": "直接用户终稿接受（final-acceptance.json）受控例外放行：字幕从最终 approved 重渲染并 layout audit PASS、text audit hard=0；语义/scout FAIL 证据原样保留不伪造",
      "inputArtifacts": [
        "production-ledger.json",
        "production-queue.json"
      ],
      "outputArtifacts": [
        "frame-semantic-review.json",
        "caption-image-audit.json"
      ],
      "traceId": "TR-PROD-11-01"
    },
    {
      "key": "PUBLISH",
      "label": "成片发布 (Publish Ready)",
      "status": "completed",
      "timeCost": "20m",
      "startTime": "2026-09-04T12:18:17+08:00",
      "endTime": "2026-09-04T12:18:17+08:00",
      "attempt": "1/1",
      "description": "用户明确声明接受当前资产为终稿并接受已知缺陷（final-acceptance.json）；FCS build+verify PASS、release-package 直审锁定、validate/machine/evidence 门禁通过后推进 PUBLISH_READY",
      "inputArtifacts": [
        "release-manifest.json"
      ],
      "outputArtifacts": [
        "final-candidate-snapshot.json",
        "release-semantic-review.json"
      ],
      "traceId": "TR-PUB-11-01"
    }
  ],
  "runtimeEnv": {
    "workerId": "worker-codex-isolated-04",
    "gpuNode": "node-rtx4090-sh-02",
    "modelProvider": "openai",
    "imageResolution": "1080×1350 (4:5)",
    "aspectRatio": "4:5",
    "heartbeatInterval": "5s",
    "activeConcurrency": "3 image workers"
  }
};
