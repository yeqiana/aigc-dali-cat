import type { StoryRunItem } from '../types';
// 历史 Run 只读详情，不代表当前 Runtime 心跳或真实可执行操作。
export const RUN_DETAIL: StoryRunItem = {
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
};
