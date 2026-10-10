import type { StoryRunItem } from '../types';
// 历史 Run 只读详情，不代表当前 Runtime 心跳或真实可执行操作。
export const RUN_DETAIL: StoryRunItem = {
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
};
