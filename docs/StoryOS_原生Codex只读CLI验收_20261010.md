# 原生 Codex CLI 只读可用性预检（2026-10-10）

`python scripts/storyos_codex_cli_readiness.py` 只执行 `codex --version` 与 `codex exec --help`；既不调用模型，也不读取 `auth.json`、不发送 Prompt、不生成图片、不得视作有权启动正式生产。

检查 `-C`、`--ephemeral`、`--json`、`--sandbox` 与 CLI 版本。**CLI 参数支持不代表原生 Codex 用户登录、文件可见性、审查产物可写、原生图像提供者或 Review Authority 已验收。**

当前 Windows 的 `codex_critic_runner.default_sandbox()` 返回 `danger-full-access`。因此 `-C <episode>` 是工作目录收敛，**不是执行时的强制访问隔离**；Prompt 中的“只能读取给定文件”也不能作为安全机制。不可在尚未有兼容沙箱方案时擅自把 Sandbox 改为 `workspace-write`，原有 Windows User Runner 会发生 1385 登录错误。

真实接入验收要用正式 Runner 的原生身份，检查能访问已冻结输入与输出候选、不会绕过 Authority/Revision、没有 OpenCodex 代理，并确认必要的执行约束；涉及模型/付费的检查需独立显式授权。
