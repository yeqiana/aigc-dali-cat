# Story OS V2.6.0｜Performance Runtime 设计说明

## 1. 为什么升大版本

V2.5.1 / V2.5.1.1 已堵住重复恢复、盲审误返修和无限单帧候选，但仍有三类成本：
- 并发 Runtime JSON 读改写竞争；
- 生图与 Scout 异常耦合；
- Caption 改动导致 Visual Critic 被重新拉起；
- Agent 在 Windows 中尝试 Bash heredoc、PowerShell here-string、复杂转义后失败再重试。

V2.6.0 把这些收敛为一个统一 Runtime Contract。

## 2. Cross-Shell Golden Rule

禁止：
- Bash heredoc：`<<EOF`
- PowerShell here-string 用于生成代码/JSON
- `powershell -Command` 嵌套 JSON / Python
- `shell=True`
- 手工给 subprocess argv 拼引号

允许：
- Python argv list
- UTF-8 request file
- subprocess stdin
- repo 的 file edit/write API
- `.cmd` 只做很薄的一键入口

## 3. Candidate Lifecycle

`CLAIMED → GENERATING → COMMITTED → REVIEW_PENDING → REVIEWED`

只有 `COMMITTED` 之前的技术失败才能 release 候选额度。
Fast Scout / Rolling Review / Final Review 的技术失败只能延期审核，不能把已成功图片变回“没生成”。

## 4. Visual / Caption 解耦

Visual Final Freeze 只绑定：
- Image SHA
- Frame Contract SHA
- Visual context SHA

不绑定 Caption SHA。

Caption Image Audit 只绑定：
- Image SHA
- Caption SHA

字幕改 6 张，只审 6 张字幕，不再把 20 张图片送回 FULL Visual Critic。
