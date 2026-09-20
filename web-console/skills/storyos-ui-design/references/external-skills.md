# External Skill References & Intake Log (external-skills.md)

本文件系统记录 StoryOS UI 设计体系从外部开源优质技能中吸收的核心思想、排除的内容及其背后的工程权衡。

**核心原则**：
> 外部技能仅作为参考知识库（Reference Knowledge）。
> StoryOS 仓库根目录下的 **`DESIGN.md`** 与 **`skills/storyos-ui-design/`** 才是系统唯一的持久化设计契约。
> 严禁外部技能在未来的更新自动或静默改变 StoryOS 的既有行为与界面契约。

---

## 1. `rwcod/anti-ai-slop-ui`

- **来源**: [https://github.com/rwcod/anti-ai-slop-ui](https://github.com/rwcod/anti-ai-slop-ui)
- **审查日期 (Reviewed Date)**: 2026-09-17
- **吸收内容**:
  1. **Anti-AI Slop Audit 机制**：将“去 AI 味”转化为具体的 20 项工程门禁清单；
  2. **Equal-weight card 审查**：识别并禁止均等平铺的四宫格卡片；
  3. **Visual Direction 定位**：确立了 `Enterprise Control Plane` 与 `Security Operations Console` 的工业底色；
  4. **指标化评估**：引入 `AI Slop Risk (LOW/MED/HIGH)` 与 `Distinctiveness Score (1~10)`。
- **未吸收内容**:
  1. 外部原版针对通用 Web 营销页面的部分色彩建议与文本字距；
  2. 针对普通 C 端产品的丰富插图或动态图表建议。
- **StoryOS 取舍原因**:
  StoryOS 是严肃的自动化流水线调度中枢，用户是故事制作人与运维工程师，界面需要极高信息密度与快速排障能力，任何多余的艺术化装饰都会降低扫描效率。

---

## 2. `mblode/agent-skills → ui-design`

- **来源**: [https://github.com/mblode/agent-skills/tree/main/skills/ui-design](https://github.com/mblode/agent-skills/tree/main/skills/ui-design)
- **审查日期 (Reviewed Date)**: 2026-09-17
- **吸收内容**:
  1. **标准五阶段工作流**：确立了 `DIRECTION` → `EXTRACT` → `AUDIT` → `BUILD` → `POLISH` 职责解耦闭环；
  2. **Extract-First 铁律**：严禁在未读取已有 Token 与设计系统前盲目重构页面；
  3. **Audit-Before-Build**：任何视觉修改必须先定位坏味道并分级（Blocker / Major / Minor），禁止全盘推翻。
- **未吸收内容**:
  1. 泛化的设计系统脚手架初始化代码（Scaffold）；
  2. 多套不同的主题切换逻辑（Light/Dark 切换）。
- **StoryOS 取舍原因**:
  StoryOS 必须始终专注于工业级 Dark Neutral 暗调控制台，保持单一定义深度打磨，避免引入无意义的主题分叉。

---

## 3. `gnurio/refactoring-ui-plugin` (Refactoring UI)

- **来源**: [https://github.com/gnurio/refactoring-ui-plugin](https://github.com/gnurio/refactoring-ui-plugin)
- **审查日期 (Reviewed Date)**: 2026-09-17
- **吸收内容**:
  1. **原子化视觉阶梯**：从 Hierarchy、Typography、Spacing、Color、Depth 分步攻坚；
  2. **依靠间距与分割线代替边框**：减少冗余全包裹卡片，依靠表面明度差与 1px 细线划分层级；
  3. **单色主导与克制语义色**：90% 中性深灰，彩色仅作为微小信号点（6px dot）。
- **未吸收内容**:
  1. 面向 SaaS 营销页面的高饱和对比度强调色块；
  2. 偏向传统桌面文档排版的大字距与宽松行高。
- **StoryOS 取舍原因**:
  高密度控制台必须压缩垂直空间以在单屏展示全流程，行高严格控制在 1.3~1.4，以提高一屏多任务可视行数。

---

## 4. `nolly-studio/design-md`

- **来源**: [https://github.com/nolly-studio/agent-skills/tree/main/skills/design-md](https://github.com/nolly-studio/agent-skills/tree/main/skills/design-md)
- **审查日期 (Reviewed Date)**: 2026-09-17
- **吸收内容**:
  1. **持久化设计语言契约**：在仓库根目录设立单一权威事实源 `DESIGN.md`；
  2. **防风格漂移机制**：后续所有 Agent（无论是何种底层模型）修改前端前必须强制先读取契约；
  3. **量化参数落地**：把颜色、圆角、高度、行高、间距网格全部显式数值化。
- **未吸收内容**:
  1. 动态生成设计提案的交互问答流。
- **StoryOS 取舍原因**:
  StoryOS 已经拥有明确的工业控制台定位，直接把成熟的参数规则写进契约，杜绝后续反复猜测与沟通成本。
