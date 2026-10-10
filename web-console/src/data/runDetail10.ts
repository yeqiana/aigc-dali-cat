import type { StoryRunItem } from '../types';
// 历史 Run 只读详情，不代表当前 Runtime 心跳或真实可执行操作。
export const RUN_DETAIL: StoryRunItem = {
  "id": "run-JN-01",
  "storyName": "江南卖花姑娘的一天",
  "runId": "RUN-JN-01-IDEA_LOCKED",
  "currentStage": "CREATE",
  "stageLabel": "IDEA_LOCKED",
  "status": "WAITING",
  "progressPercent": 0,
  "completedFrames": 0,
  "totalFrames": 20,
  "currentAction": "选题与创意大纲已锁定 · 正在准备分镜",
  "createdAt": "2026-09-08 23:30",
  "duration": "28m",
  "lastHeartbeatAgo": "2 秒前",
  "heartbeatSeconds": 2,
  "exceptionSummary": "全门禁通过 (All Gates Passed)",
  "exceptionType": "none",
  "storyDescription": ". 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
  "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
  "frames": [
    {
      "frameNo": 1,
      "frameCode": "F01",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "01_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-01",
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
      "frameNo": 2,
      "frameCode": "F02",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "02_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-02",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "03_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-03",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "04_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-04",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "05_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-05",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "06_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-06",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "07_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-07",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "08_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-08",
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
      "frameNo": 9,
      "frameCode": "F09",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "09_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-09",
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
      "frameNo": 10,
      "frameCode": "F10",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "10_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-10",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "11_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-11",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "12_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-12",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "13_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-13",
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
      "frameNo": 14,
      "frameCode": "F14",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "14_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-14",
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
      "frameNo": 15,
      "frameCode": "F15",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "15_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-15",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "16_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-16",
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
      "frameNo": 17,
      "frameCode": "F17",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "17_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-17",
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
      "frameNo": 18,
      "frameCode": "F18",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "18_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-18",
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
      "frameNo": 19,
      "frameCode": "F19",
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "19_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-19",
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
      "status": "NOT_STARTED",
      "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "duration": "42s",
      "attempt": "1 / 1",
      "currentSubAction": "QUEUED",
      "provider": "openai",
      "modelName": "gpt-image-2",
      "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
      "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
      "artifactName": "20_final.png",
      "artifactSize": "2.1 MB",
      "traceId": "TR-FRAME-JN-01-20",
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
      "startTime": "2026-09-08 23:30",
      "endTime": "2026-09-08 23:31",
      "attempt": "1/1",
      "description": "候选迁移与 user_seed 强化重写，生成世界观与基础结构元数据。",
      "inputArtifacts": [
        "runtime-request.json"
      ],
      "outputArtifacts": [
        "episode-state.json",
        "concept-ambition-review.json"
      ],
      "traceId": "TR-IDEA-JN-01"
    },
    {
      "key": "STORY_LOCK",
      "label": "分镜锁定 (Storyboard Lock)",
      "status": "pending",
      "timeCost": "14m",
      "startTime": "2026-09-08 23:31",
      "endTime": "2026-09-08 23:45",
      "attempt": "1/1",
      "description": "20 帧分镜大纲与节拍表锁定，通过 concept/story/propagation/recent5 门禁。",
      "inputArtifacts": [
        "story-dna-trace.json"
      ],
      "outputArtifacts": [
        "shot-progression-review.json",
        "story-gates.json"
      ],
      "traceId": "TR-STORY-JN-01"
    },
    {
      "key": "VISUAL_LOCK",
      "label": "视觉校准 (Visual Calibrate)",
      "status": "pending",
      "timeCost": "1h 05m",
      "startTime": "2026-09-09 08:44",
      "endTime": "2026-09-09 09:49",
      "attempt": "1/1",
      "description": "Visual Lock 4 帧全 PASS (日常01/极限11/初变03/高潮15)，authenticity 合格。",
      "inputArtifacts": [
        "character-contract.json",
        "character-appearance-anchor.json"
      ],
      "outputArtifacts": [
        "visual-lock-admissions.json",
        "visual-final-freeze.json"
      ],
      "traceId": "TR-VISUAL-JN-01"
    },
    {
      "key": "PRODUCTION",
      "label": "制作执行 (Production)",
      "status": "pending",
      "timeCost": "1h 01m",
      "startTime": "2026-09-09 09:49",
      "endTime": "2026-09-09 10:50",
      "attempt": "1/1",
      "description": "全自动 20 帧渲染全 PASS，逐帧语义审核合格，连续性与字幕通过。",
      "inputArtifacts": [
        "production-ledger.json",
        "production-queue.json"
      ],
      "outputArtifacts": [
        "frame-semantic-review.json",
        "caption-image-audit.json"
      ],
      "traceId": "TR-PROD-JN-01"
    },
    {
      "key": "PUBLISH",
      "label": "成片发布 (Publish Ready)",
      "status": "pending",
      "timeCost": "20m",
      "startTime": "2026-09-09 10:50",
      "endTime": "2026-09-09 11:10",
      "attempt": "1/1",
      "description": "release preflight + snapshot + delegated approval all PASS; publish_decision=go。",
      "inputArtifacts": [
        "release-manifest.json"
      ],
      "outputArtifacts": [
        "final-candidate-snapshot.json",
        "release-semantic-review.json"
      ],
      "traceId": "TR-PUB-JN-01"
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
