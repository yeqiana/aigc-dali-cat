# Git Pre-Commit Whitelist Audit

**日期**: 2026-09-12  
**任务**: Story OS V3 Production Hardening 提交前白名单整理

---

## 一、保留文件列表（正式代码/文档/测试）

### 1.1 根目录配置
- .gitignore (modified)

### 1.2 文档 (docs/)
- docs/Story_OS_V3_Production_Exposure_Multi_Issue_Repair_Plan_20260912.md
- docs/Story_OS_Incremental_Review_增量复审闭环治理方案_V1.0.md
- docs/Story_OS_Production_Gate_Evidence_Closure_Gap_生产门禁证据闭环缺口分析方案_V1.0.md
- docs/Story_OS_Repair_Budget_Exceeded_返修额度耗尽治理方案_V1.0.md
- docs/Story_OS_Runtime_Projection_Drift_生产状态派生一致性治理方案_V1.0.md
- docs/Story_OS_全自动流程当前卡点分析与恢复改造方案_2026-09-12.md
- docs/Story_OS_天界普通人的一天_Production_Closure_漏洞清单_W23-W29_2026-09-12.md
- docs/Story_OS_天界普通人的一天_全流程生产漏洞治理交接_2026-09-12.md
- docs/Story_OS_生产终审图与Approved闭环缺口分析及修复方案_2026-09-12.md
- docs/Story_OS_生产资产模板化与并发执行优化方案_V1.0.md
- docs/Story_OS_终审结果未回写与旧中断记录污染流程_漏洞分析及修复方案_2026-09-12.md

### 1.3 系统代码 (episodes/_system/)
- pisodes/_system/reference_execution_receipt.py (正式代码)
- pisodes/_system/codex_user_runner.py (V2.7 Codex User Mode Bridge 正式能力)

### 1.4 测试 (tests/system/)
- 	ests/system/test_codex_user_runner.py (正式测试)

### 1.5 脚本 (scripts/)
- scripts/install_codex_user_runner_task.ps1 (V2.7 正式脚本)
- scripts/start_codex_user_runner.ps1 (V2.7 正式脚本)

### 1.6 运行时文档 (runtimes/)
- untimes/CODEX_USER_MODE_BRIDGE.md (V2.7 正式文档)

---

## 二、排除文件列表

### 2.1 临时探针（删除暂存）
- pisodes/_system/_shim_probe.py ❌

### 2.2 Episode 生产资产（单独提交）
以下文件属于「天界普通人的一天」episode 生产资产，不混入代码提交：
- pisodes/天界普通人的一天/docs/** (4 个文档)
- pisodes/天界普通人的一天/meta/** (大量 meta 文件)
- pisodes/天界普通人的一天/prompts/** (production/repairs prompts)
- pisodes/天界普通人的一天/release/** (release 文档)

### 2.3 Runtime 派生产物（已由 .gitignore 排除）
以下目录已被 .gitignore 规则排除，无需手动处理：
- pisodes/**/meta/runtime/**
- pisodes/**/meta/provider-receipts/**
- pisodes/**/meta/frame-scouts/**
- pisodes/**/meta/host-requests/**

### 2.4 临时生成文件（已由 .gitignore 排除）
- .codex-run/
- .codex-write-probe.txt
- .preimage_author_tmp.py
- .probe-tmp.py
- .storyos-tmp/
- .tmp-*

### 2.5 图片和媒体（已由 .gitignore 排除）
- pisodes/**/media/**
- pisodes/**/*.png
- pisodes/**/*.jpg
- pisodes/**/*.webp

---

## 三、Codex User Bridge 判断

经检查：
- pisodes/_system/codex_user_runner.py 包含 STORY_OS_V2_7_CODEX_USER_MODE_BRIDGE 标记
- 配套测试 	ests/system/test_codex_user_runner.py 已就位
- 配套脚本 scripts/*.ps1 和文档 untimes/CODEX_USER_MODE_BRIDGE.md 已就位

**结论**: 属于 Story OS V2.7 正式能力，保留提交。

---

## 四、提交建议

### 第一次提交（代码/文档/测试）
`
feat: V3 Production Hardening E003-E006 修复

- Story DNA Trace 数据结构
- Failure Learning Loop
- Visual Reality Score
- Style Registry
- Codex User Mode Bridge (V2.7)
- 正式测试覆盖
`

### 第二次提交（Episode 生产资产）
`
feat: 天界普通人的一天 episode 生产资产

- Story Lock / Storyboard / Frame Contracts
- Visual Lock / Production / Release 文档
- 20 帧 production prompts
`

---

## 五、当前风险

1. **Runtime 派生产物**: 已由 .gitignore 自动排除，无需手动处理
2. **Episode 资产量大**: 天界普通人的一天有 100+ 文件，建议单独提交
3. **_shim_probe.py**: 需要从暂存区移除

---

## 六、执行状态

- [x] 审计文档生成
- [ ] 移除临时探针暂存
- [ ] 移除 Episode 资产暂存
- [ ] 验证最终暂存范围
- [ ] 执行提交

