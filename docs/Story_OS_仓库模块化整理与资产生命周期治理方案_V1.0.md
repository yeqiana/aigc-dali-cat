# Story OS 仓库模块化整理与资产生命周期治理方案 V1.0

更新时间：2026-09-11

## 一、目标

当前 Story OS 已从个人实验仓库演进为 AI 内容生产操作系统。

当前问题：

- 生产代码、历史文档、测试资产、临时调试文件混杂
- V2 演进资产与 V3 当前能力混合
- 临时运行产物污染根目录
- Pattern、Standard、Runtime 边界不清

目标：

建立：

```
Production Asset

Historical Archive

Pattern Library

Runtime Debug

Core Module
```

五类生命周期隔离。

---

# 二、当前根目录分类

## 1. 核心生产模块（保持根目录）

以下禁止迁移：

```
assets/
episodes/
config/
meta/
platform/
runtime/
runtimes/
scripts/
skills/
tests/
web-console/
```

原因：

- 当前 Runtime 依赖
- EP003 生产链依赖
- 不进行大规模路径重构

---

## 2. 文档体系

当前：

```
docs/
```

目标：

```
docs/
├── architecture/     当前架构
├── product/          产品设计
├── operations/       运维治理
└── archive/          历史文档
```

---

## 3. 标准体系

当前：

```
standards/
```

目标：

```
standards/
├── active/           当前生产规范
├── templates/        模板
├── patterns/         可复用模式
└── _superseded/      废弃规范
```

---

# 三、历史资产整理

## V2 文档

处理：

```
docs/Story_OS_V2.*
```

迁移：

```
docs/archive/v2-evolution/
```

规则：

- 保留 Git 历史
- 不删除
- 不参与生产

---

# 四、Pattern Library 建设

以下属于经验资产，不属于生产规范：

包括：

- 现实侵入式伪纪录片模板
- 导演镜头光影规则
- 环境物理与异常隐藏规则
- 真实性与共享风格锚点
- 设备物理档案

目标：

```
library/
└── visual-patterns/
    └── documentary-realism/
```

用途：

- Prompt Agent
- Visual Agent
- 创作辅助

禁止直接作为生产门禁。

---

# 五、Runtime Debug 资产

以下属于临时运行产物：

```
_tmp*
*.log
runtime-smoke-report.json
workbench 临时日志
.storyos 临时日志
```

统一归档：

```
.storyos/archive/runtime-debug-YYYYMMDD/
```

规则：

- 保留证据
- 不进入产品代码
- 不影响生产

---

# 六、禁止操作

整理期间禁止：

- 删除 episodes
- 修改 EP003 生产资产
- 修改 Runtime 核心逻辑
- 大规模改变 import 路径
- 删除 V2 历史经验

---

# 七、执行顺序

## Phase 1

完成：

- .storyos/backups 归档
- .storyos/smoke 归档

状态：完成

## Phase 2

完成：

- Runtime debug 归档

状态：完成（提交 `e573d86`）

## Phase 3

执行：

- V2 文档归档
- Visual Pattern 整理

状态：部分完成

- V2 文档归档：完成（20 份 `Story_OS_V2*` 迁入 `docs/archive/v2-evolution/`）。
- Visual Pattern：`library/visual-patterns/` 已建立；4 份 `standards/` 视觉经验规范因生产代码硬引用暂停，方案见 `docs/standards_视觉经验规范解耦方案_20260911.md`。

## Phase 4

执行：

- 引用扫描
- 生命周期检查

状态：进行中

---

# 七之二、后续执行顺序（2026-09-11 修订）

```
1. Runtime Debug 剩余日志归档        ✅ 已完成
2. 根目录治理清单                    ✅ docs/仓库根目录治理清单_20260911.md
3. .storyos_tmp / cache 分类          ✅ docs/运行时临时目录与缓存分类_20260911.md
4. standards 解耦方案                ✅ docs/standards_视觉经验规范解耦方案_20260911.md
5. 根目录移动                        ⏸ 待确认
```

第 5 步的候选与建议归档位置见 `docs/仓库根目录治理清单_20260911.md` 第四节。

---

# 八、最终目标结构

```
storyOS/

├── assets/
├── episodes/
├── platform/
├── runtime/
├── runtimes/

├── docs/
├── standards/
├── library/
├── meta/

├── scripts/
├── tests/
├── skills/

└── .storyos/
    └── archive/
```

最终形成：

```
Story OS Product Repository
```

而不是临时实验仓库。
