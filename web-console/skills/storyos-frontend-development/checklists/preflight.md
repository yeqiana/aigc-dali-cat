# Checklist: Preflight

在正式修改代码前，必须形成简短 Preflight。

## 规范格式：
```text
Task Type:
BUGFIX / CREATE / EXTEND / REVIEW / POLISH / PERFORMANCE / ACCESSIBILITY / REFACTOR

Target:
本次修改的具体业务目标。

Scope:
涉及的业务模块 / 页面。

Expected Files:
预计修改的文件清单与数量（通常 ≤ 3 个）。

Existing Components:
预计复用的公共组件与设计令牌。

Contract Impact:
NONE / READ_ONLY / CHANGE_REQUIRED

Risk:
LOW / MEDIUM / HIGH

Verification:
计划执行的验证方式（如 Targeted Unit Test、typecheck、browser state verification）。
```

## 范围漂移检测：
如果实际修改明显超过 Preflight：
- 预计 2 文件，实际需要修改 15 文件；
- 或原判断 Contract Impact = NONE，实际需要修改 API Schema；
**必须立刻重新评估任务，不得静默扩大范围。**
