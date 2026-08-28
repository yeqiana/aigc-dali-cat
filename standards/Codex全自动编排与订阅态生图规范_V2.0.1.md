# Codex 全自动编排与订阅态生图规范 V2.0.1

这是从属执行细则。唯一创作权威仍是 `standards/制作规范_正式版.md`，唯一阶段事实源仍是 `meta/episode-state.json`。

V2.0.1 把 CODEX runtime 从“协议要求”补成可执行入口：`story_os.py run <episode> --full-auto`。orchestrator 使用当前 Codex CLI 登录态启动隔离 worker，worker 继续 Golden Path，不建立第二状态机。

`codex_subscription_image.py` 只负责一次图片生成：prompt/最多2张参考 → 临时 Codex worker → image_generation 一次 → 真实候选落盘。它不需要 OpenAI API Key、不模拟浏览器点击、不拿缓存图冒充。

全自动授权是 `continuous_execution_authorized=true`，允许连续执行、自审和最多一次内容返修。自动审查统一记为 `delegated_auto_review`，不得伪造成 `direct_user_review` 或用户主动点击了 Story/Visual/Release Lock。

外部证据门禁统一使用 `evidence_gate.py`。`v18_gate.py` 作为 V1.8 首次引入证据锁的兼容实现保留；以后不再增加版本命名 gate。
