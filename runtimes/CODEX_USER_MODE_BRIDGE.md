# Story OS V2.7 Codex User-Mode Execution Bridge

状态：运行期适配层（runtime adapter），非第二权威。

唯一 episode 阶段事实源仍是 <episode>/meta/episode-state.json；唯一创作权威仍是
standards/制作规范_正式版.md。本文件只说明「Codex 进程由谁启动」，不改变任何
Stage、Gate、Provenance 或 Repair Budget 规则。

## 1. 问题

Windows 下 DevSpace 以 NT AUTHORITY\SYSTEM 运行，而本机 Codex 登录态、配置与模型缓存
属于交互用户（例如 RENRP\yeqian / C:\Users\79873\.codex）。

SYSTEM 直接执行 codex exec 时会去读用户 profile 下的 Codex 文件（例如
models_cache.json），随即失败：

    Access Denied / os error 5

这不是 Codex 安装问题，也不是 Story OS 逻辑问题，而是「执行身份边界」问题。

## 2. 方案：用户态 Runner + 本机回环桥

    Story OS / DevSpace (SYSTEM)
        -> codex_user_runner.run_codex(...)      客户端（唯一调用契约）
        -> 127.0.0.1 loopback HTTP
        -> Codex User Runner（交互用户 RENRP\yeqian）
        -> codex exec
        -> <用户 profile>\.codex

- DevSpace 服务身份保持不变，仍以 SYSTEM 运行。
- Codex 始终由交互用户身份启动，credential 不离开用户态。
- 没有第二套 Runtime、Scheduler 或状态机：Runner 只是 Codex 进程执行适配器，
  不持有 Stage、Ledger、Gate、Episode State 或 Repair Budget。

## 3. 文件与启动

模块（唯一新增模块，Runner 与 Client 同体）：

    episodes/_system/codex_user_runner.py

本地通道目录（已 .gitignore，不入库）：

    runtime/codex-user-runner/endpoint.json     loopback host/port + 本地 nonce + pid + user
    runtime/codex-user-runner/token             本地 nonce（非 Codex 凭证）
    runtime/codex-user-runner/runner-log.jsonl  Runner 侧执行事实
    runtime/codex-user-runner/tmp/              跨身份共享的任务暂存目录

用户态启动（必须在交互用户会话中执行）：

    pwsh -File scripts/start_codex_user_runner.ps1
    pwsh -File scripts/start_codex_user_runner.ps1 -Foreground

若当前身份是 SYSTEM / LOCAL SERVICE / NETWORK SERVICE，脚本直接拒绝并输出：

    CODEX_USER_RUNNER_REQUIRES_INTERACTIVE_USER

可选的开机（登录）自启动，脚本默认只打印计划、不注册：

    pwsh -File scripts/install_codex_user_runner_task.ps1            # dry run
    pwsh -File scripts/install_codex_user_runner_task.ps1 -Register  # 显式注册
    pwsh -File scripts/install_codex_user_runner_task.ps1 -Unregister

任务使用 LogonType Interactive（仅登录时运行），不写入任何密码。

## 4. 接口

    GET  /v1/health        Runner 身份、Codex 可用性、Codex Home 可读性
    POST /v1/codex/exec    一个声明式 Codex Task

认证：请求头 X-StoryOS-Codex-Runner-Token，值为本地 nonce。
监听地址固定 127.0.0.1（拒绝 0.0.0.0 等非回环地址）。

Task 只描述「跑哪一次 codex」，不描述「跑什么程序」：

    schema_version, request_id, task_type, argv, working_directory,
    stdin_base64, timeout_seconds, env, codex_home_mode, client

- argv 的可执行部分必须是 Codex CLI 名称（codex/codex.exe/codex.cmd/codex.bat/
  codex.py/codex.ps1）；cmd.exe /d /c codex.cmd 这类包装会被拆开校验，其他任何
  可执行文件一律拒绝。
- 请求方传入的 PATH、CODEX_HOME 等环境变量不会生效；只有 PYTHONUTF8、
  PYTHONIOENCODING 与 STORY_OS_* 前缀键会被传递。
- codex_home_mode=inherit 使用 Runner 用户真实的 Codex Home；
  codex_home_mode=isolated 使用该用户 profile 下的临时 Home（并发图片 worker 用），
  任务结束后立即删除，并把 generated_images 产物镜像到调用方 workdir。

## 5. 错误分类（技术失败，不消耗内容返修预算）

    CODEX_USER_RUNNER_UNAVAILABLE            Runner 未启动 / 端点失效 / pid 已死
    CODEX_USER_RUNNER_WRONG_IDENTITY         Runner 身份不是交互用户（例如 SYSTEM）
    CODEX_USER_RUNNER_AUTH_FAILED            本地 nonce 校验失败
    CODEX_USER_RUNNER_TIMEOUT                任务超时
    CODEX_USER_RUNNER_TASK_REJECTED          非法可执行文件 / 非法 task_type 等
    CODEX_USER_RUNNER_WORKSPACE_UNAVAILABLE  Runner 无法使用 workdir
    CODEX_EXEC_FAILED                        Codex 进程本身失败

Story OS 侧一律按 infrastructure/technical failure 处理：runtime_failure_classifier
把它们归入 TECH_FAILED（可重试），critic_runtime_v211 把它们归入技术码，
不会把候选标记成 content failed。

## 6. 安全边界

- 不复制 .codex/auth.json 到仓库；仓库内不落任何 Codex credential。
- Runner 只在用户态读取自己的 Codex 登录态；DevSpace 不读取用户 .codex。
- 不给 SYSTEM 授予 .codex FullControl，不使用 Everyone，不改任何用户密码。
- 只监听 127.0.0.1，不开公网端口；本地 nonce 只用于本机校验。
- 不允许任意 exe / cmd / powershell 命令执行：可执行文件恒为 codex。
- health 只返回状态与路径，不返回 token、cookie 或 session。

## 7. 自检

    python episodes/_system/codex_user_runner.py self-test
    python episodes/_system/codex_user_runner.py health --json
    python -m pytest tests/system/test_codex_user_runner.py -q
