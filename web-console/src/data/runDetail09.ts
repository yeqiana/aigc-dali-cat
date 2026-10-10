import type { StoryRunItem } from '../types';
// 历史 Run 只读详情，不代表当前 Runtime 心跳或真实可执行操作。
export const RUN_DETAIL: StoryRunItem = {
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
};
