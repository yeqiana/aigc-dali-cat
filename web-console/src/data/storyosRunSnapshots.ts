// StoryOS 工作区历史证据快照（非实时生产状态）；按消费场景拆包。
import type { StoryRunItem } from '../types';
export const REAL_STORY_RUNS: StoryRunItem[] = [
  {
    "id": "run-09-04",
    "storyName": "瓶中世界",
    "runId": "RUN-09-04-PUBLISH_READY",
    "currentStage": "PUBLISH",
    "stageLabel": "PUBLISH_READY",
    "status": "COMPLETED",
    "progressPercent": 0,
    "completedFrames": 0,
    "totalFrames": 20,
    "currentAction": "Release Preflight PASS · 发布决策 GO",
    "createdAt": "2026-08-28T11:08:20-04:00",
    "duration": "28m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "Auto-Recovered: Frame 01 worker retry passed",
    "exceptionType": "none",
    "storyDescription": "老旧柜顶上的一只透明玻璃瓶，收纳着三十年前一整个村庄失踪前的最后回响与微缩活景。",
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "frames": [
      {
        "frameNo": 1,
        "frameCode": "F01",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-01",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-02",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-03",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-04",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-05",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-06",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-07",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-08",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-09",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-10",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-11",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-12",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-13",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-14",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-15",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-16",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-17",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-18",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-19",
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
        "completedAt": "2026-08-28T21:41:43-04:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-04-20",
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
        "startTime": "2026-08-28T11:08:20-04:00",
        "endTime": "2026-08-28T11:08:20-04:00",
        "attempt": "1/1",
        "description": "2026-08-28 用户授权 Story OS V2.0.3.2 全自动连续执行；重建真实生产闭环",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-09-04"
      },
      {
        "key": "STORY_LOCK",
        "label": "分镜锁定 (Storyboard Lock)",
        "status": "completed",
        "timeCost": "14m",
        "startTime": "2026-08-28T12:49:47-04:00",
        "endTime": "2026-08-28T12:49:47-04:00",
        "attempt": "1/1",
        "description": "第二次独立 Story Critic 通过；delegated_auto_review Story Lock 完成",
        "inputArtifacts": [
          "story-dna-trace.json"
        ],
        "outputArtifacts": [
          "shot-progression-review.json",
          "story-gates.json"
        ],
        "traceId": "TR-STORY-09-04"
      },
      {
        "key": "VISUAL_LOCK",
        "label": "视觉校准 (Visual Calibrate)",
        "status": "completed",
        "timeCost": "1h 05m",
        "startTime": "2026-08-28T13:03:44-04:00",
        "endTime": "2026-08-28T13:03:44-04:00",
        "attempt": "1/1",
        "description": "M00/CP03 visual lock passed by independent isolated critic; calibration 01/03/10 and ending admission 20 locked.",
        "inputArtifacts": [
          "character-contract.json",
          "character-appearance-anchor.json"
        ],
        "outputArtifacts": [
          "visual-lock-admissions.json",
          "visual-final-freeze.json"
        ],
        "traceId": "TR-VISUAL-09-04"
      },
      {
        "key": "PRODUCTION",
        "label": "制作执行 (Production)",
        "status": "completed",
        "timeCost": "1h 01m",
        "startTime": "2026-08-28T21:41:17-04:00",
        "endTime": "2026-08-28T21:41:17-04:00",
        "attempt": "1/1",
        "description": "20张正文、逐帧审核、字幕布局审计与终审全部通过",
        "inputArtifacts": [
          "production-ledger.json",
          "production-queue.json"
        ],
        "outputArtifacts": [
          "frame-semantic-review.json",
          "caption-image-audit.json"
        ],
        "traceId": "TR-PROD-09-04"
      },
      {
        "key": "PUBLISH",
        "label": "成片发布 (Publish Ready)",
        "status": "completed",
        "timeCost": "20m",
        "startTime": "2026-08-28T21:41:43-04:00",
        "endTime": "2026-08-28T21:41:43-04:00",
        "attempt": "1/1",
        "description": "最终ZIP已生成并通过完整性与SHA校验",
        "inputArtifacts": [
          "release-manifest.json"
        ],
        "outputArtifacts": [
          "final-candidate-snapshot.json",
          "release-semantic-review.json"
        ],
        "traceId": "TR-PUB-09-04"
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
  },
  {
    "id": "run-09-05",
    "storyName": "婚礼前夜",
    "runId": "RUN-09-05-PUBLISH_READY",
    "currentStage": "PUBLISH",
    "stageLabel": "PUBLISH_READY",
    "status": "COMPLETED",
    "progressPercent": 15,
    "completedFrames": 3,
    "totalFrames": 20,
    "currentAction": "Release Preflight PASS · 发布决策 GO",
    "createdAt": "2026-09-08T23:30:13+08:00",
    "duration": "56m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "Auto-Recovered: Frame 01 worker retry passed",
    "exceptionType": "none",
    "storyDescription": "漏服被说成助眠的药后，女主从婚礼物件和空间中确认自己正在被限制并可能被运走；她拒绝下一剂药、主动制造机会逃到检查站，却仍失去自己的名字，结尾以另一场试鞋梦和旧房间细节回返保留获救真伪的双解释。",
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
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=1; no_valid_image=true; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\09_旧物怪谈\\05_婚礼前夜_记忆麻醉\\meta\\image-workers\\01-6f20114d6fb9-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-08T23:59:37+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01站在婚房门口对镜头，正面看向相机（持机者为院里男方，用她的卡片机拍婚前夜留影）；黑发红绳、浅色碎花长袖、深色裤、旧布鞋，神情平和微怔。身后婚房红彤彤：红被铺好的木床、桌边亲友整理搪瓷盆与红绸，喜字与红布窗完整，土墙可见。无药瓶、药片、铁栏或锁链。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-01",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '02', 'kind': 'repair', 'used': 0, 'limit': 2, 'episode_used': 35, 'episode_limit': 35, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '2252cfd88e4e'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-09T14:18:52+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01坐在床边，左手正在收拾针线，桌角有普通水杯、纸巾和一粒未动的药。小白瓶放在桌角远侧，男人在背景搬被褥；没有递瓶、盯视或按住她。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-02",
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
        "frameNo": 3,
        "frameCode": "F03",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "ASPECT_RATIO_MISMATCH: ASPECT_RATIO_MISMATCH: raw preserved at D:\\workspace\\YeQianWorkSpace\\yeqian\\storyOS\\episodes\\09_旧物怪谈\\05_婚礼前夜_记忆麻醉\\media\\raw\\03-1789484687.png; provider_receipt=episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/provider-receipts/03-1789484828.json; ASPECT_RATIO_MISMATCH: source=1092x1440, target=1080x1350, ratio_delta=0.052083; inspect Generation Request before deciding whether to regenerate",
        "failureStage": "image_worker",
        "failedAt": "2026-09-15T23:07:08+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "梦境主观向下看自己的深色裤脚和旧布鞋：脚边一截短铁链被扯直伸入床底，链条两端都在画外。链与床脚接触处清晰，无法判断连着什么。无脚镣全貌、无药、无看守脸。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-03",
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
        "frameNo": 4,
        "frameCode": "F04",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "TIMEOUT: image worker timeout after 120s; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\09_旧物怪谈\\05_婚礼前夜_记忆麻醉\\meta\\image-workers\\04-0cedad7e5345-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-09T10:15:20+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "同一梦境，P01俯视碎花袖口，一只陌生成年人的手压住她的左手，木床沿可见；来者全身与脸均在画外，袖口也不露。没有瓶杯、嘴部、灌药或完整锁链。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-04",
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
        "frameNo": 5,
        "frameCode": "F05",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "IMAGE_BACKEND_ERROR: [WinError 32] 另一个程序正在使用此文件，进程无法访问。: 'C:\\\\Users\\\\79873\\\\AppData\\\\Local\\\\Temp\\\\story-os-image-qdqi5wmo'",
        "failureStage": "image_worker",
        "failedAt": "2026-09-09T10:15:20+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "现实醒来，P01坐在床沿低头，左手掀开一角被子，自己裸露脚踝上有一圈浅红压痕；同一深色裤脚，旧布鞋在床边。门口男人背影在忙，无药无铁环，不做梦中动作匹配。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-05",
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
        "frameNo": 6,
        "frameCode": "F06",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "IMAGE_BACKEND_ERROR: [WinError 32] 另一个程序正在使用此文件，进程无法访问。: 'C:\\\\Users\\\\79873\\\\AppData\\\\Local\\\\Temp\\\\story-os-image-fs3q67pc'",
        "failureStage": "image_worker",
        "failedAt": "2026-09-09T10:15:20+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01从座位向前看，左手拿着纸，男人在桌对面侧身指向纸张，纸面只有失焦笔迹；婚房布置连续。不能从背后拍女主，也不出现她的脸。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-06",
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
        "frameNo": 7,
        "frameCode": "F07",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '07', 'kind': 'authority_refresh', 'used': 0, 'limit': 1, 'episode_used': 55, 'episode_limit': 55, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '8b3f44f752a2'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-15T22:09:19+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01坐在梳妆镜前，左右亲友整理发绳与喜被，交谈各做各事；镜子只带到女主碎花肩袖与发尾。她的姓名不在画面中，禁止生成人物对话文字。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-07",
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
        "frameNo": 8,
        "frameCode": "F08",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "从P01眼位看梳妆镜，陌生中年女人站在身后梳头，镜中可辨女人脸与梳子；P01自己的脸被镜面上缘裁出，仅见同一碎花肩袖、红绳黑发。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-08",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01坐在床边左手翻转红绣鞋，使鞋底两道铁环朝向镜头；右手持机不入画，碎花袖、深色裤和自己的旧布鞋连续。铁环只在鞋上，不套在她脚上。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-09",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01左掌托着一只尚未扣合的金色手镯，内侧合缝与小锁孔清晰，另一只放桌上；碎花袖口可见。不是已锁在手腕上的镯子，不展示开锁步骤。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-10",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "ASPECT_RATIO_MISMATCH: ASPECT_RATIO_MISMATCH: raw preserved at D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\09_旧物怪谈\\05_婚礼前夜_记忆麻醉\\media\\raw\\11-1788918043.png; provider_receipt=episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/provider-receipts/11-1788918043.json; ASPECT_RATIO_MISMATCH: source=1086x1448, target=1080x1350, ratio_delta=0.062500; inspect Generation Request before deciding whether to regenerate",
        "failureStage": "image_worker",
        "failedAt": "2026-09-09T09:40:43+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01左手掀起窗上的红布一角，布后露出横贯窗洞、固定在窗框内的铁栏，栏与窗框连接关系清晰；完整红布在其余区域仍遮挡。一次发现动作，无回头蒙太奇，不以土墙为新证据。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-11",
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
        "frameNo": 12,
        "frameCode": "F12",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; no_valid_image=true; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\09_旧物怪谈\\05_婚礼前夜_记忆麻醉\\meta\\image-workers\\12-ef634aef4e89-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-10T11:47:06+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01站在屋内门缝后向院里看，前景只有门框和一点碎花袖。男人在货车后门旁，车厢内几个成年女孩穿红嫁衣，脚踝铁环能看清；女主始终在屋里，不坐车厢，不穿红嫁衣。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-12",
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
        "frameNo": 13,
        "frameCode": "F13",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01站在屋内床侧，男人的手把一粒药与水杯递近，小白瓶在他另一手里；他侧身挡住前门方向。此时才把药与控制关系明确并置，不做仰头强灌。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-13",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '14', 'kind': 'authority_refresh', 'used': 0, 'limit': 1, 'episode_used': 55, 'episode_limit': 55, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '3c10b4a65646'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-15T22:09:21+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01从自己的眼位俯向床头旧花盆，左手扶盆沿，刚吐出的药落在湿土表面；背景男人侧后身转向前门。女主嘴脸不入画，不画手指把药丢进盆里。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-14",
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
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01左手举起那只未扣合金镯对着男人，镯口与锁孔可见；男人停下并伸手来抢，身后前门被挡住，左侧通后门的窄道和矮凳清楚。无女主正脸，无凭空解锁。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-15",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01从后门门槛向田路冲出，画面下缘同一深色裤脚与旧布鞋沾泥，碎花袖左手推门，回侧余光见翻倒的矮凳挡在追来的男人脚前。无第三人称跑步全身，无换装、无突然赤脚、无救场女孩。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-16",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "ASPECT_RATIO_MISMATCH: ASPECT_RATIO_MISMATCH: raw preserved at D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\09_旧物怪谈\\05_婚礼前夜_记忆麻醉\\media\\raw\\17-1788934433.png; provider_receipt=episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉/meta/provider-receipts/17-1788934575.json; ASPECT_RATIO_MISMATCH: source=1092x1440, target=1080x1350, ratio_delta=0.052083; inspect Generation Request before deciding whether to regenerate",
        "failureStage": "image_worker",
        "failedAt": "2026-09-09T14:16:15+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01坐在检查站桌边，从自己眼位看记录人员和桌面，低处可见同一沾泥旧布鞋与深色裤脚，碎花袖左手停在桌沿。无白婚纱，无脚镣，无女主面部。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-17",
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
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '18', 'kind': 'authority_refresh', 'used': 0, 'limit': 1, 'episode_used': 55, 'episode_limit': 55, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '9fd69bf0a8bf'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-15T22:09:20+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "检查站同一座位，P01转向窗外，自己碎花左袖扶窗沿，花白头发女人被人搀着走来，神情急切；无女主脸，无白婚纱，不声称她已完整恢复记忆。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-18",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '19', 'kind': 'authority_refresh', 'used': 0, 'limit': 1, 'episode_used': 55, 'episode_limit': 55, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '407ab497972a'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-15T22:09:20+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "另一梦境，P01坐在明亮普通卧室的凳子上，第一人称俯视左手翻起红绣鞋鞋底，没有铁环。低位镜子仅反射同一坐姿的深色裤腿、碎花袖与红鞋，左右按镜面对应，脸和持机手在镜框外。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-19",
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
        "frameNo": 20,
        "frameCode": "F20",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '20', 'kind': 'authority_refresh', 'used': 0, 'limit': 1, 'episode_used': 55, 'episode_limit': 55, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '737fe5a8663e'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-15T22:09:20+08:00",
        "completedAt": "2026-09-09T11:10:58+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01躺在床上主观仰视斑驳天花板，侧下缘一点碎花袖和红被；与先前婚房相同的墙角裂痕和红布窗边可辨。小白瓶在远侧床头桌边，无标签，静默；不新增锁链、不替观众断言获救全是假。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-09-05-20",
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
      }
    ],
    "pipelineStages": [
      {
        "key": "CREATE",
        "label": "选题锁定 (Idea Lock)",
        "status": "completed",
        "timeCost": "1m",
        "startTime": "2026-09-08T23:30:13+08:00",
        "endTime": "2026-09-08T23:30:13+08:00",
        "attempt": "1/1",
        "description": "候选迁移：2026-09-07_02 story_v1，user_seed 强化重写",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-09-05"
      },
      {
        "key": "STORY_LOCK",
        "label": "分镜锁定 (Storyboard Lock)",
        "status": "completed",
        "timeCost": "14m",
        "startTime": "2026-09-08T23:44:52+08:00",
        "endTime": "2026-09-08T23:44:52+08:00",
        "attempt": "1/1",
        "description": "Story+Storyboard 20帧完成，concept/story/propagation/recent5 gate PASS",
        "inputArtifacts": [
          "story-dna-trace.json"
        ],
        "outputArtifacts": [
          "shot-progression-review.json",
          "story-gates.json"
        ],
        "traceId": "TR-STORY-09-05"
      },
      {
        "key": "VISUAL_LOCK",
        "label": "视觉校准 (Visual Calibrate)",
        "status": "completed",
        "timeCost": "1h 05m",
        "startTime": "2026-09-09T09:49:20+08:00",
        "endTime": "2026-09-09T09:49:20+08:00",
        "attempt": "1/1",
        "description": "Visual Lock 4帧全PASS(ordinary_baseline01/worst_condition11/first_anomaly03/high_impact15); schema_v2 review 18checks; authenticity=passed; visual_spec doc 已生成; delegated_auto_review",
        "inputArtifacts": [
          "character-contract.json",
          "character-appearance-anchor.json"
        ],
        "outputArtifacts": [
          "visual-lock-admissions.json",
          "visual-final-freeze.json"
        ],
        "traceId": "TR-VISUAL-09-05"
      },
      {
        "key": "PRODUCTION",
        "label": "制作执行 (Production)",
        "status": "completed",
        "timeCost": "1h 01m",
        "startTime": "2026-09-09T10:50:38+08:00",
        "endTime": "2026-09-09T10:50:38+08:00",
        "attempt": "1/1",
        "description": "全自动：20帧Production全PASS，逐帧语义审核full-frame-set PASS，continuity/subtitle PASS，终审文档已登记，delegated_auto_review",
        "inputArtifacts": [
          "production-ledger.json",
          "production-queue.json"
        ],
        "outputArtifacts": [
          "frame-semantic-review.json",
          "caption-image-audit.json"
        ],
        "traceId": "TR-PROD-09-05"
      },
      {
        "key": "PUBLISH",
        "label": "成片发布 (Publish Ready)",
        "status": "completed",
        "timeCost": "20m",
        "startTime": "2026-09-09T11:10:58+08:00",
        "endTime": "2026-09-09T11:10:58+08:00",
        "attempt": "1/1",
        "description": "release preflight + snapshot + delegated approval all PASS; snapshot sha 603b3c...; zip sha 33fba5...; publish_decision=go; delegated_auto_review; user not directly approved",
        "inputArtifacts": [
          "release-manifest.json"
        ],
        "outputArtifacts": [
          "final-candidate-snapshot.json",
          "release-semantic-review.json"
        ],
        "traceId": "TR-PUB-09-05"
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
  },
  {
    "id": "run-10-01",
    "storyName": "鳌太线·热汤",
    "runId": "RUN-10-01-PUBLISH_READY",
    "currentStage": "PUBLISH",
    "stageLabel": "PUBLISH_READY",
    "status": "COMPLETED",
    "progressPercent": 0,
    "completedFrames": 0,
    "totalFrames": 20,
    "currentAction": "Release Preflight PASS · 发布决策 GO",
    "createdAt": "2026-08-29T14:39:02+08:00",
    "duration": "28m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "Auto-Recovered: Frame 01 worker retry passed",
    "exceptionType": "none",
    "storyDescription": "鳌太穿越遇险记录，狂风暴雪中一间违背常理的护林员石屋，炉子上煮着滚烫的热汤。",
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "frames": [
      {
        "frameNo": 1,
        "frameCode": "F01",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-01",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-02",
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
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-03",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "cross_session_candidate_collision: parallel workers selected the same global latest generated image; frame04 own generated raw recovered separately",
        "failureStage": "image_worker",
        "failedAt": "2026-08-29T23:32:09+08:00",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-04",
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
        "frameNo": 5,
        "frameCode": "F05",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-05",
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
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-06",
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
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-07",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-08",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-09",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-10",
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
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-11",
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
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-12",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-13",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-14",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-15",
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
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-16",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-17",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-18",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-19",
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
        "completedAt": "2026-08-30T14:00:42+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-01-20",
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
        "startTime": "2026-08-29T14:39:02+08:00",
        "endTime": "2026-08-29T14:39:02+08:00",
        "attempt": "1/1",
        "description": "用户授权 Story OS V2.0.3.4 CODEX runtime 全自动制作，连续执行直到最终交付",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-10-01"
      },
      {
        "key": "STORY_LOCK",
        "label": "分镜锁定 (Storyboard Lock)",
        "status": "completed",
        "timeCost": "14m",
        "startTime": "2026-08-29T15:14:07+08:00",
        "endTime": "2026-08-29T15:14:07+08:00",
        "attempt": "1/1",
        "description": "Story and 20-frame storyboard passed fresh isolated semantic critic attempt 1; delegated_auto_review Story Lock recorded.",
        "inputArtifacts": [
          "story-dna-trace.json"
        ],
        "outputArtifacts": [
          "shot-progression-review.json",
          "story-gates.json"
        ],
        "traceId": "TR-STORY-10-01"
      },
      {
        "key": "VISUAL_LOCK",
        "label": "视觉校准 (Visual Calibrate)",
        "status": "completed",
        "timeCost": "1h 05m",
        "startTime": "2026-08-29T23:18:28+08:00",
        "endTime": "2026-08-29T23:18:28+08:00",
        "attempt": "1/1",
        "description": "M00+CP06 calibrations passed fresh isolated Visual Critic attempt 1; CP01 frame20 visual admission passed; delegated visual lock recorded.",
        "inputArtifacts": [
          "character-contract.json",
          "character-appearance-anchor.json"
        ],
        "outputArtifacts": [
          "visual-lock-admissions.json",
          "visual-final-freeze.json"
        ],
        "traceId": "TR-VISUAL-10-01"
      },
      {
        "key": "PRODUCTION",
        "label": "制作执行 (Production)",
        "status": "completed",
        "timeCost": "1h 01m",
        "startTime": "2026-08-30T13:24:00+08:00",
        "endTime": "2026-08-30T13:24:00+08:00",
        "attempt": "1/1",
        "description": "20帧锁图、SHA-bound incremental full-frame review attempt 2、字幕布局与 text audit 均通过；生产验收记录已归档。",
        "inputArtifacts": [
          "production-ledger.json",
          "production-queue.json"
        ],
        "outputArtifacts": [
          "frame-semantic-review.json",
          "caption-image-audit.json"
        ],
        "traceId": "TR-PROD-10-01"
      },
      {
        "key": "PUBLISH",
        "label": "成片发布 (Publish Ready)",
        "status": "completed",
        "timeCost": "20m",
        "startTime": "2026-08-30T14:00:42+08:00",
        "endTime": "2026-08-30T14:00:42+08:00",
        "attempt": "1/1",
        "description": "Release Guard四项、20张真实发布资产、最终SHA交付ZIP及 delegated_auto_review Release Lock均通过。",
        "inputArtifacts": [
          "release-manifest.json"
        ],
        "outputArtifacts": [
          "final-candidate-snapshot.json",
          "release-semantic-review.json"
        ],
        "traceId": "TR-PUB-10-01"
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
  },
  {
    "id": "run-10-B01",
    "storyName": "不存在的夜行路",
    "runId": "RUN-10-B01-IDEA_LOCKED",
    "currentStage": "CREATE",
    "stageLabel": "IDEA_LOCKED",
    "status": "WAITING",
    "progressPercent": 0,
    "completedFrames": 0,
    "totalFrames": 20,
    "currentAction": "选题与创意大纲已锁定 · 正在准备分镜",
    "createdAt": "2026-09-03T18:28:02+08:00",
    "duration": "28m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "全门禁通过 (All Gates Passed)",
    "exceptionType": "none",
    "storyDescription": "10_彼此的天上 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-01",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-02",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-03",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-04",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-05",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-06",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-07",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-08",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-09",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-10",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-11",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-12",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-13",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-14",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-15",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-16",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-17",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-18",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-19",
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
        "completedAt": "2026-09-03T18:28:02+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-B01-20",
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
        "startTime": "2026-09-03T18:28:02+08:00",
        "endTime": "2026-09-03T18:28:02+08:00",
        "attempt": "1/1",
        "description": "系列包正式接入机器状态：docs DRAFT + 01-20 Photography Regression(非权威测试)已 PASS，本阶段仅定稿故事层，不生成正式图",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-10-B01"
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
        "traceId": "TR-STORY-10-B01"
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
        "traceId": "TR-VISUAL-10-B01"
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
        "traceId": "TR-PROD-10-B01"
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
        "traceId": "TR-PUB-10-B01"
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
  },
  {
    "id": "run-10-02",
    "storyName": "玻璃另一边的手",
    "runId": "RUN-10-02-VISUAL_CALIBRATED",
    "currentStage": "VISUAL_LOCK",
    "stageLabel": "VISUAL_CALIBRATED",
    "status": "RUNNING",
    "progressPercent": 95,
    "completedFrames": 19,
    "totalFrames": 20,
    "currentAction": "Visual Lock 4帧已准入 · 待派发出图队列",
    "createdAt": "2026-09-04T22:17:22+08:00",
    "duration": "28m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "Auto-Recovered: Frame 01 worker retry passed",
    "exceptionType": "none",
    "storyDescription": "读取 story 分支。全自动重新制作一篇题目：玻璃另一边的手。必须保留：\\n- 本篇属于《彼此的天上》EP002，承接EP001，不推翻系列Bible和人物关系弧\\n- 主角仍是二十多岁普通情侣，自驾旅行进入，不使用记者、调查员、研究人员等专业身份\\n- 全系列只保留一套空间局部重叠异常机制，不新增鬼、怪物、裂缝、维度解释或神秘组织\\n- 这集的核心必须从俗套的鬼手贴窗改成双向普通人接触：对面的人也在观察、理解和害怕我们\\n- 女友必须有一个普通、自然、可画的主动动作，对面要有直接回应，形成强动作-回应-后果传播核\\n- 高潮必须保留孩子想靠近，而对面成年人立刻把孩子拉走这一层，让观众意识到在对方视角里我们才是异常\\n- 不要用标准敲两下回两下的老套交流，可重新设计更生活化、更自然的动作回应\\n- 不要用线头等过强实体证据破坏留白，结尾以第二天现实空间复核和人物认知变化收束\\n- 默认20张，第一人称真实手机相册感，前3张必须同时建立旅行生活和直接可见异常\\n- 严格按仓库当前Story OS V2.5.1完成Story/Storyboard/Contracts/Visual Lock/Production/Review/Subtitles/Release/Final Snapshot，一直做到PUBLISH_READY，不要每一步询问我",
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
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\10_彼此的天上\\02_玻璃另一边的手\\meta\\image-workers\\01-e7bf8a9697a2-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-06T02:24:04+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02偏镜头带入P01",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-01",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "WORKER_FAILED: [Errno 22] Invalid argument: 'D:\\\\workspace\\\\YeQianWorkSpace\\\\yeqian\\\\aigc-dali-cat\\\\episodes\\\\10_彼此的天上\\\\02_玻璃另一边的手\\\\meta\\\\runtime\\\\contracts\\\\frames\\\\02.json'",
        "failureStage": "image_worker",
        "failedAt": "2026-09-07T15:30:34+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02搭外套并提醒充电",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-02",
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
        "frameNo": 3,
        "frameCode": "F03",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\10_彼此的天上\\02_玻璃另一边的手\\meta\\image-workers\\03-89c8abc517a3-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-06T10:12:00+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02指出外侧清晰区",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-03",
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
        "frameNo": 4,
        "frameCode": "F04",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "WORKER_FAILED: [Errno 22] Invalid argument: 'D:\\\\workspace\\\\YeQianWorkSpace\\\\yeqian\\\\aigc-dali-cat\\\\episodes\\\\10_彼此的天上\\\\02_玻璃另一边的手\\\\meta\\\\runtime\\\\contracts\\\\frames\\\\04.json'",
        "failureStage": "image_worker",
        "failedAt": "2026-09-07T15:30:34+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01关灯、P02横移",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-04",
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
        "frameNo": 5,
        "frameCode": "F05",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "WORKER_FAILED: [Errno 22] Invalid argument: 'D:\\\\workspace\\\\YeQianWorkSpace\\\\yeqian\\\\aigc-dali-cat\\\\episodes\\\\10_彼此的天上\\\\02_玻璃另一边的手\\\\meta\\\\runtime\\\\contracts\\\\frames\\\\05.json'",
        "failureStage": "image_worker",
        "failedAt": "2026-09-07T15:30:35+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02换位观察错位",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-05",
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
        "frameNo": 6,
        "frameCode": "F06",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "OUTPUT_MISSING: worker returned success without output",
        "failureStage": "image_worker",
        "failedAt": "2026-09-07T15:32:11+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01把手机收回给P02看",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-06",
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
        "frameNo": 7,
        "frameCode": "F07",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "OUTPUT_MISSING: worker returned success without output",
        "failureStage": "image_worker",
        "failedAt": "2026-09-07T15:32:10+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02蹲低观察",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-07",
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
        "frameNo": 8,
        "frameCode": "F08",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "OUTPUT_MISSING: worker returned success without output",
        "failureStage": "image_worker",
        "failedAt": "2026-09-07T15:33:28+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02用袖口擦内雾",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-08",
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
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\10_彼此的天上\\02_玻璃另一边的手\\meta\\image-workers\\09-35216c31b625-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-06T16:43:26+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "对面成年人擦开外侧水膜",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-09",
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
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "双方从遮挡后互相探看",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-10",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "RAW_CANDIDATE_BUDGET_EXHAUSTED: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '11', 'kind': 'repair', 'used': 0, 'limit': 2, 'episode_used': 35, 'episode_limit': 35, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': '5fb2c372d712'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-08T16:10:18+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01抬手机、对面举布",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-11",
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
        "frameNo": 12,
        "frameCode": "F12",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; no_valid_image=true; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\10_彼此的天上\\02_玻璃另一边的手\\meta\\image-workers\\12-dc1b3520bce7-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-08T16:45:58+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02按低P01手腕",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-12",
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
        "frameNo": 13,
        "frameCode": "F13",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; no_valid_image=true; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\10_彼此的天上\\02_玻璃另一边的手\\meta\\image-workers\\13-3979017ac688-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-08T12:55:31+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "孩子从成年人身后探出",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-13",
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
        "lastError": "IMAGE_BACKEND_ERROR: Codex image worker failed rc=0; log=D:\\workspace\\YeQianWorkSpace\\yeqian\\aigc-dali-cat\\episodes\\10_彼此的天上\\02_玻璃另一边的手\\meta\\image-workers\\14-0bed26ad211c-a1.jsonl",
        "failureStage": "image_worker",
        "failedAt": "2026-09-06T10:08:53+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01按灭并压低手机，同时成年人抱离孩子",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-14",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "EPISODE_IMAGE_LOOP_GUARD: RAW_CANDIDATE_BUDGET_EXHAUSTED: {'frame': '15', 'kind': 'repair', 'used': 0, 'limit': 2, 'episode_used': 35, 'episode_limit': 35, 'decision': 'EPISODE_IMAGE_LOOP_GUARD', 'token': 'eaf9deafd5cc'}",
        "failureStage": "image_worker",
        "failedAt": "2026-09-08T16:06:37+08:00",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "成年人护住孩子并盖窗，机位继续下坠",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-15",
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
        "frameNo": 16,
        "frameCode": "F16",
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "录像在机位压低后停止",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-16",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01递水，P02接过，二人低声复盘",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-17",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02在安全处指出昨夜窗位",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-18",
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
        "status": "PASSED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "IMAGE_GENERATION",
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01回看停录前短视频并复核无实体残留",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-19",
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
        "completedAt": "2026-09-06T23:09:03+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02拉门回看，P01拍完普通离店照后删除求证长消息",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-10-02-20",
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
        "startTime": "2026-09-04T22:17:22+08:00",
        "endTime": "2026-09-04T22:17:22+08:00",
        "attempt": "1/1",
        "description": "EP002 V2.5.1正式重制接入：按系列Bible与当前Story OS重写，保留双向普通人接触内核，降低鬼手俗套感",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-10-02"
      },
      {
        "key": "STORY_LOCK",
        "label": "分镜锁定 (Storyboard Lock)",
        "status": "completed",
        "timeCost": "14m",
        "startTime": "2026-09-06T02:00:25+08:00",
        "endTime": "2026-09-06T02:00:25+08:00",
        "attempt": "1/1",
        "description": "Story Critic attempt 2 PASS; character contract locked; delegated approval + Recent-5 PASS",
        "inputArtifacts": [
          "story-dna-trace.json"
        ],
        "outputArtifacts": [
          "shot-progression-review.json",
          "story-gates.json"
        ],
        "traceId": "TR-STORY-10-02"
      },
      {
        "key": "VISUAL_LOCK",
        "label": "视觉校准 (Visual Calibrate)",
        "status": "completed",
        "timeCost": "1h 05m",
        "startTime": "2026-09-06T23:09:03+08:00",
        "endTime": "2026-09-06T23:09:03+08:00",
        "attempt": "1/1",
        "description": "Visual Lock Final Verify PASS, evidence snapshot reconciled",
        "inputArtifacts": [
          "character-contract.json",
          "character-appearance-anchor.json"
        ],
        "outputArtifacts": [
          "visual-lock-admissions.json",
          "visual-final-freeze.json"
        ],
        "traceId": "TR-VISUAL-10-02"
      },
      {
        "key": "PRODUCTION",
        "label": "制作执行 (Production)",
        "status": "completed",
        "timeCost": "1h 01m",
        "startTime": "2026-09-08T22:15:00+08:00",
        "endTime": "2026-09-08T22:15:00+08:00",
        "attempt": "1/1",
        "description": "用户确认已在抖音实际发布。本次仅记录发布事实与最终发布文案；production/subtitle/publish 门禁未闭环，04帧仍为 NEEDS_USER，未伪造通过，未推进机器状态。",
        "inputArtifacts": [
          "production-ledger.json",
          "production-queue.json"
        ],
        "outputArtifacts": [
          "frame-semantic-review.json",
          "caption-image-audit.json"
        ],
        "traceId": "TR-PROD-10-02"
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
        "traceId": "TR-PUB-10-02"
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
  },
  {
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
  },
  {
    "id": "run-11-01-RE",
    "storyName": "仲夏夜惊魂 重制版",
    "runId": "RUN-11-01-RE-IDEA_LOCKED",
    "currentStage": "CREATE",
    "stageLabel": "IDEA_LOCKED",
    "status": "WAITING",
    "progressPercent": 0,
    "completedFrames": 0,
    "totalFrames": 20,
    "currentAction": "选题与创意大纲已锁定 · 正在准备分镜",
    "createdAt": "2026-09-02T20:10:51+08:00",
    "duration": "28m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "全门禁通过 (All Gates Passed)",
    "exceptionType": "none",
    "storyDescription": "11_仲夏夜惊魂 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "到村口停车，妹妹从路灯下小跑过来上车；顺手拍了段村口夜路发家庭群报平安",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-01",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "妹妹坐后座，P01 一手扶把一手拍前方夜路，灯下飞虫从镜头前掠过",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-02",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "停好车后随手拍：门灯亮着，门槛边没收的竹椅，画面下缘带到他自己的鞋与裤脚",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-03",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "妹妹切好西瓜端来，P01 坐着边吃边拍，桌上有冰绿豆汤与烧着的蚊香",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-04",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "两人在门口乘凉说话，妹妹扇蒲扇赶蚊子，P01 把这段拍下来",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-05",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "妹妹说巷口路灯早坏了没人修，P01 走去巷口，发现那盏灯亮着",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-06",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "走近那根旧灯杆，发现它比记忆里更靠墙、歪的方向也不对，杆根地面却干干净净",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-07",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "妹妹出来找 P01，两人说起路灯的事，她确认那盏灯坏了大半年没人修，一起再往巷口看",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-08",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "再走近看：杆是歪的，杆根地面没有撞击痕迹也没有修补痕迹，两人都安静下来",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-09",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "回家路上妹妹突然停住：老槐树本该在院墙右边，现在树和树影都在墙的左边，方向整个反了",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-10",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "到村口小卖部想买水，卷帘门拉着却从门缝透出光，拍门没人应，屋里像有收音机声",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-11",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "两人骑电动车沿村道走，头顶路灯一盏接一盏熄掉，最后整段路黑下来，只剩车灯一小片光",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-12",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "回到自家院门，发现出门前关掉的堂屋灯亮着，窗里挂钟像停摆，两人愣在门口不敢动",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-13",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "两人决定连夜去镇上住一晚；妹妹弯腰锁院门，P01 拿手电帮她照着并拍下来",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-14",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "按原路往镇上骑，却到了从没见过的下坡水泥路，路边并排停着落灰的三轮车，坡底看不到头",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-15",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "掉头往回骑想回村，路口却也对不上，来时的村口灯火消失了，只剩成排延伸的电线杆",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-16",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "前面又是那棵歪脖子老槐树，树下同一只狗趴着不动，这是第三次经过同一处；P01 急刹停住",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-17",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "两人下车推着电动车沿电线杆走，谁都没说话，只听脚步和电瓶车轻微的电流声",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-18",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "远处传来拖拉机声，灯光直直扫过来，两人站到路肩让车；强光过后，路变得认得了",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-19",
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
        "completedAt": "2026-09-02T20:10:51+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "不知怎么就走回了自家院门口；门灯下妹妹回头笑了一下，两人进院坐下，堂屋灯正常亮着",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-11-01-RE-20",
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
        "startTime": "2026-09-02T20:10:51+08:00",
        "endTime": "2026-09-02T20:10:51+08:00",
        "attempt": "1/1",
        "description": "V2.2.1 重制版前期资产重建：Story Lock 已锁定（PASS），Character Contract/World Identity PASS，Visual Narrative LOCKED，Production NOT_READY；PREPRODUCTION_ONLY，未进入生产。",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-11-01-RE"
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
        "traceId": "TR-STORY-11-01-RE"
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
        "traceId": "TR-VISUAL-11-01-RE"
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
        "traceId": "TR-PROD-11-01-RE"
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
        "traceId": "TR-PUB-11-01-RE"
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
  },
  {
    "id": "run-MR-01",
    "storyName": "埋儿那天，娘把我拦住了",
    "runId": "RUN-MR-01-IDEA_LOCKED",
    "currentStage": "CREATE",
    "stageLabel": "IDEA_LOCKED",
    "status": "WAITING",
    "progressPercent": 0,
    "completedFrames": 0,
    "totalFrames": 20,
    "currentAction": "选题与创意大纲已锁定 · 正在准备分镜",
    "createdAt": "2026-09-16T17:35:28+08:00",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #1: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-01",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #2: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-02",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #3: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-03",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #4: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-04",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #5: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-05",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #6: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-06",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #7: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-07",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #8: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-08",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #9: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-09",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #10: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-10",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #11: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-11",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #12: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-12",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #13: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-13",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #14: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-14",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #15: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-15",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #16: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-16",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #17: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-17",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #18: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-18",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #19: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-19",
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
        "completedAt": "2026-09-16T17:35:28+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "分镜 #20: 4:5 1080×1350 叙事画幅，环境光照自然，主体面容保持基准锁定。",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-MR-01-20",
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
        "startTime": "2026-09-16T17:35:28+08:00",
        "endTime": "2026-09-16T17:35:28+08:00",
        "attempt": "1/1",
        "description": "一句话入口创建 Episode；后续阶段只由 canonical state transition 推进",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-MR-01"
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
        "traceId": "TR-STORY-MR-01"
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
        "traceId": "TR-VISUAL-MR-01"
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
        "traceId": "TR-PROD-MR-01"
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
        "traceId": "TR-PUB-MR-01"
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
  },
  {
    "id": "run-TJ-01",
    "storyName": "天界普通女生的一天",
    "runId": "RUN-TJ-01-STORYBOARD_LOCKED",
    "currentStage": "STORYBOARD",
    "stageLabel": "STORYBOARD_LOCKED",
    "status": "WAITING",
    "progressPercent": 10,
    "completedFrames": 2,
    "totalFrames": 20,
    "currentAction": "20帧分镜已锁定 · 等待视觉母本校准",
    "createdAt": "2026-09-13T01:37:29+08:00",
    "duration": "54m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "Auto-Recovered: Frame 01 worker retry passed",
    "exceptionType": "none",
    "storyDescription": "天界生活日常 系列重磅短剧篇章，探索未知禁忌与中式悬疑志怪。",
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
        "lastError": "RECOVERY_MISBOUND_SUCCESS_INVALIDATED: repair worker had no terminal artifact; old original candidate was incorrectly rebound during crash recovery",
        "failureStage": "image_worker",
        "failedAt": "2026-09-13T15:29:10+08:00",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01 刚出门自拍，P02 一边替她压住被晨风吹乱的碎发，P03 端着早餐在后面笑着入镜",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-01",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "三人边说话边下楼，P03 把一份热糕递给 P01",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-02",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01 把热糕掰开，蒸汽贴近镜头，P02 在旁边挑咸口小菜",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-03",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P04 迟到后把自己的纸包点心放桌上赔罪，四个人笑他又睡过头",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-04",
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
        "attempt": "2 / 2",
        "currentSubAction": "IMAGE_GENERATION",
        "lastError": "WORKER_PROCESS_LOST: worker pid=45888 disappeared before terminal receipt and produced no candidate",
        "failureStage": "image_worker",
        "failedAt": "2026-09-13T17:42:28+08:00",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "四人吃完早饭往公共生活区走，P02 指着桥下云层里露出的水渠",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-05",
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
        "frameNo": 6,
        "frameCode": "F06",
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01 把当天几张普通登记纸签按类别放好，顺手喝一口茶",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-06",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P03 敲两下窗框催她下班，P01 把纸签收进木匣",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-07",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "四人挑到靠窗桌，P04 把凳子往里挪给 P02",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-08",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02 把女主爱吃的酥藕夹到她碗里，P04 抢最后一块被 P03 挡住",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-09",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "大家原本准备各自回去，P02 临时提议去旧云市逛发簪摊，另外三人顺势改路线",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-10",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "四人边走边避让挑担人，P01 稍微落后半步拍下街景",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-11",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02 试一根便宜木簪，P01 帮她把散下来的头发重新拢好",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-12",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "两个男生被安排拎东西，故意一人举一包假装很重，女生回头笑他们",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-13",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "大家坐下歇脚，P04 给每个人倒茶，P02 把刚买的木簪放桌上给大家看",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-14",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "四个人边吃边聊各自最近的小事，没有任务或神秘话题",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-15",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "QUEUED",
        "lastError": "WORKER_PROCESS_LOST: worker pid=45888 disappeared before terminal receipt and produced no candidate",
        "failureStage": "image_worker",
        "failedAt": "2026-09-13T17:42:28+08:00",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02 看见天色转暖，提议去西桥坐一会儿再回家",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-16",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "2 / 2",
        "currentSubAction": "QUEUED",
        "lastError": "WORKER_PROCESS_LOST: worker pid=45888 disappeared before terminal receipt and produced no candidate",
        "failureStage": "image_worker",
        "failedAt": "2026-09-13T17:42:28+08:00",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P02临时接过P01的玉牌边走边拍；P01/P03/P04继续看云海或聊天，P04仍趴在栏杆上，三人不为镜头重新排队",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-17",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P03 把最后一块掰成四份，大家坐在桥边分着吃",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-18",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "四人在路口道别，P02 回头挥手，P03/P04 一边走一边还在说话",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-19",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-13T10:38:05+08:00",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "P01 坐下把小木簪放在膝边，拍完最后一张就收起留影玉牌",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-TJ-01-20",
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
        "startTime": "2026-09-13T01:37:29+08:00",
        "endTime": "2026-09-13T01:37:29+08:00",
        "attempt": "1/1",
        "description": "一句话入口创建 Episode；后续阶段只由 canonical state transition 推进",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-TJ-01"
      },
      {
        "key": "STORY_LOCK",
        "label": "分镜锁定 (Storyboard Lock)",
        "status": "completed",
        "timeCost": "14m",
        "startTime": "2026-09-13T10:38:05+08:00",
        "endTime": "2026-09-13T10:38:05+08:00",
        "attempt": "1/1",
        "description": "Story Lock 三层 Gate + delegated_auto_review 通过；Concept/Recent5/Story Semantic 使用诚实 WORK_DEVSPACE_BOUNDED provenance。",
        "inputArtifacts": [
          "story-dna-trace.json"
        ],
        "outputArtifacts": [
          "shot-progression-review.json",
          "story-gates.json"
        ],
        "traceId": "TR-STORY-TJ-01"
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
        "traceId": "TR-VISUAL-TJ-01"
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
        "traceId": "TR-PROD-TJ-01"
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
        "traceId": "TR-PUB-TJ-01"
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
  },
  {
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
  },
  {
    "id": "run-误入桃花源",
    "storyName": "误入桃花源",
    "runId": "RUN-误入桃花源-STORYBOARD_LOCKED",
    "currentStage": "STORYBOARD",
    "stageLabel": "STORYBOARD_LOCKED",
    "status": "WAITING",
    "progressPercent": 0,
    "completedFrames": 0,
    "totalFrames": 20,
    "currentAction": "20帧分镜已锁定 · 等待视觉母本校准",
    "createdAt": "2026-09-22T03:43:09",
    "duration": "28m",
    "lastHeartbeatAgo": "2 秒前",
    "heartbeatSeconds": 2,
    "exceptionSummary": "全门禁通过 (All Gates Passed)",
    "exceptionType": "none",
    "storyDescription": "挂科与实习压力下的林舟误入封闭桃源，发现安宁靠隔绝外界维系，最终返回仍在奔流的现实。",
    "coverImage": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
    "frames": [
      {
        "frameNo": 1,
        "frameCode": "F01",
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "重修考交卷铃砸在头顶，林舟把写满潦草算式的答卷往前一推，冲出阶梯教室时切到手机前置镜头，边走边拍到自己被汗雨打湿的脸和身后的走廊",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "01_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-01",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "林舟没回宿舍也没去食堂，一路拐到学校后勤处背后的荒坡，从半人高的铁丝网缺口钻了进去",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "02_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-02",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "转过一道被雨水冲刷发白的石灰岩梁，林子变成成片野桃林，落花混着雨水砸在后颈上，空气里是花瓣与野草在阴暗处腐烂发酵后泛出的微酸冷甜；一条几乎被杂草淹没的干涸石渠横在面前，两头都被草盖住，可渠底和渠沿却被人踩得发亮——没人维护的渠，还留着当天的脚印；石渠尽头是被密密麻麻的铁线蕨遮住的狭窄石缝，阴冷的穿堂风正从缝隙里直往外冒",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "03_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-03",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "他想起早读课背过的“初极狭，才通人”，明知里面更不会有信号，还是关掉手机页面、打开电筒弯腰钻了进去；在极逼仄的石缝里摸着湿滑岩壁爬了百十来步，水滴在空洞里回响，眼前的岩缝突然裂开一道惨白的光",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "04_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-04",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "林舟跌跌撞撞爬出乱石，抬手挡住刺眼的白光，整个人僵在原地——那不是仙境，而是一块被封在深渊底部的三四百亩洼地",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "05_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-05",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "他的破球鞋带下一块碎石砸进溪水，“咚”的一声之后，整个山谷的动作同时定格，所有人木讷地看向他的连帽衫和双肩包",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "06_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-06",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "汉子把短锄插进泥里走过来，用舌根发硬的古怪口音平静地问他是不是外头来的，又看了看他的球鞋，说天快黑了、湿气重，先进屋吃碗热食",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "07_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-07",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "土屋里没有一根电线、找不到一片塑料，空气里只有松木的青蓝烟气；秦家五口默默围坐，秦叔就着瓦罐喝了一口酒，淡淡问了一句“外头，还争吗？”；林舟把这些年的争一件件说给他听，秦叔讲完老祖宗当年逃进来、天子要兵将领要粮的事，把碗底最后一口米酒喝干，才补上一句不高不低的话：“外头的响动，别进娃们的耳朵。”说完叫小石把弟妹带回里屋睡了",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "08_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-08",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "头两天他几乎以为自己掉进了精神疗养院：跟着公鸡醒来、看晨雾拉开、午后睡到夕阳斜照、傍晚在溪边听老人讲对不上年号的旧事；三年焦虑症好像突然自愈，心跳第一次缓得像谷里的死水。但这三天里他每提一句外头的事，秦家人只是听着、谁都不接话；村里的孩子远远跟着他看，不敢走近",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "09_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-09",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "第三天傍晚，他坐在老水井旁帮秦叔削竹篾，十五岁的小石蹲在旁边，眼睛一眨不眨盯着那台早就没电的黑屏手机；他忽然把前三天重新看了一遍——没有电线、没有塑料、整齐得像用尺子量过的田，这些不是清静，是这村子几百年里谁都没见过外面；秦叔留他吃饭、留他住，也不全是待客，是把他放在规矩里看着",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "10_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-10",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "他从书包侧兜摸出最后半管润喉薄荷糖，剥出一粒绿色的递过去；小石怯生生看了父亲一眼，见秦叔背对着在理竹条，飞快地把糖塞进嘴里",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "11_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-11",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "工业提纯的浓烈薄荷脑直冲上来，少年整个人像被电击中一样僵住，声音发着抖问“这是什么果子”；而他从那片黑玻璃里听来的铁鸟、大海和月亮，让那双眼睛里烧起他在每个自习室和招聘会上见过的火",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "12_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-12",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "他笑了笑，顺手拿起那台黑屏手机晃了晃，说在外面这东西想要多少有多少，要是它有电，能看见一万公里外的大海、天上飞的铁鸟，还有月亮其实就是个坑坑洼洼的大石头",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "13_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-13",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "一声极脆的裂响刺破黄昏：秦叔手里的柴刀偏了半寸，把一根厚竹劈得粉碎；他手按在刀柄上，声音平得像结了冰的深潭，只说了一句“小石，后山的羊圈该关了。去。”；那一声之后整座山谷第二次定了格，比 Frame 06 那次更彻底——远处田埂上的动作停在半途，隔壁院的织机声也停了，连狗都不叫",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "14_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-14",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "那夜没风，天幕黑得像扣下来的生铁锅；门轴吱呀一声，秦叔端着菜籽油灯进来，把糖纸和湿纸巾放在他床头，说天亮前出山去，又讲这山谷从来不是什么仙境，是一口枯井——人要活命，就只能把这口井当成天地",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "15_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-15",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "拂晓时分寒雾把山谷浸成惨白；秦叔把他送到石缝前，塞给他两个用晒干的荷叶包着的硬麦饼，说顺着暗水流的方向爬、别回头，等夏至山洪下来这道缝就会被滚石彻底填死",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "16_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-16",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "钻进石缝的最后一瞬，他回过头看了一眼：炊烟照常升起，公鸡照常啼叫，可他眼里再也没有了那种诗意，只看见一群难民的后代用世世代代的封闭给自己修的千年墓穴",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "17_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-17",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "他拨开洞口湿烂的藤蔓滚出后山，上午刺眼的白昼晃得眼睛生疼；山脚下高速货车的轰鸣像海啸撞进耳膜，打桩机的震动顺着地表传上来，震得脚踝发麻",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "18_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-18",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "口袋里的手机突然疯狂震动，未接来电和提示音连成一片；辅导员说明早九点前必须交实习证明，母亲说表哥已经帮他约好了下周二的面试，让他把衣服穿整齐点",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "19_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-19",
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
        "status": "QUEUED",
        "thumbnail": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "duration": "42s",
        "attempt": "1 / 1",
        "currentSubAction": "QUEUED",
        "completedAt": "2026-09-22T04:49:25",
        "provider": "openai",
        "modelName": "gpt-image-2",
        "prompt": "他站在风口里把那口混着尾气与沥青味的浊气吸进肺里，咬碎冷硬的麦饼，给辅导员回“收到，老师，我周一上午当面交您”，再按下母亲的通话回拨键，然后踩着满是泥的旧球鞋头也不回地走下山",
        "artifactUrl": "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%20800%201000%22%3E%3Crect%20width%3D%22800%22%20height%3D%221000%22%20fill%3D%22%23e4e4e7%22%2F%3E%3Cpath%20d%3D%22M160%20720%20340%20500l120%20140%2090-110%20110%20190H160Z%22%20fill%3D%22%23a1a1aa%22%2F%3E%3Ccircle%20cx%3D%22300%22%20cy%3D%22330%22%20r%3D%2270%22%20fill%3D%22%23a1a1aa%22%2F%3E%3C%2Fsvg%3E",
        "artifactName": "20_final.png",
        "artifactSize": "2.1 MB",
        "traceId": "TR-FRAME-误入桃花源-20",
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
        "startTime": "2026-09-22T03:43:09",
        "endTime": "2026-09-22T03:43:09",
        "attempt": "1/1",
        "description": "用户 2026-09-22 提供完整锁定故事；locked_story 全自动生产",
        "inputArtifacts": [
          "runtime-request.json"
        ],
        "outputArtifacts": [
          "episode-state.json",
          "concept-ambition-review.json"
        ],
        "traceId": "TR-IDEA-误入桃花源"
      },
      {
        "key": "STORY_LOCK",
        "label": "分镜锁定 (Storyboard Lock)",
        "status": "completed",
        "timeCost": "14m",
        "startTime": "2026-09-22T04:49:24",
        "endTime": "2026-09-22T04:49:24",
        "attempt": "1/1",
        "description": "Story Lock 完成：docs 02/03 V1.1 + story semantic review PASS(attempt 2)；Recent-5/Concept Ambition/导演密度/角色/开场锚点门禁通过；delegated_auto_review 记录，非用户亲手审核。locked_story 仅逻辑与结构润色。",
        "inputArtifacts": [
          "story-dna-trace.json"
        ],
        "outputArtifacts": [
          "shot-progression-review.json",
          "story-gates.json"
        ],
        "traceId": "TR-STORY-误入桃花源"
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
        "traceId": "TR-VISUAL-误入桃花源"
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
        "traceId": "TR-PROD-误入桃花源"
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
        "traceId": "TR-PUB-误入桃花源"
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
  }
];
