# External Skill References

StoryOS 不直接依赖外部 Skill 的运行时行为，仅作为 **REFERENCE KNOWLEDGE** 沉淀。
StoryOS 本地 Skill（`storyos-frontend-development`）才是唯一 **STABLE PROJECT CONTRACT**。

## 外部资产吸收清单

### 1. Impeccable
- **Repository**: `pbakaus/impeccable`
- **Reviewed**: 2026-09-16
- **Absorbed**:
  - Operate product mode（生产运维模式优先）
  - Visual QA loop（视觉与布局验收闭环）
  - UI hardening & Progressive disclosure（渐进式信息披露）
  - 反 AI 模板化规则
- **Not absorbed**:
  - 激进的营销式视觉冲击
  - 牺牲扫描效率的艺术化特效

---

### 2. Vercel React Best Practices
- **Repository**: `vercel-labs/agent-skills/skills/react-best-practices`
- **Reviewed**: 2026-09-16
- **Absorbed**:
  - Waterfall prevention（请求瀑布流消除）
  - Bundle size control（大模块与抽屉按需懒加载）
  - Rerender rules（高频心跳与状态局部下沉）
  - Client fetching 稳定性
- **Not absorbed**:
  - 与 Next.js 深度绑定的服务端特定路由语法（当前为 Vite SPA 生产控制台）

---

### 3. Vercel Web Design Guidelines
- **Repository**: `vercel-labs/agent-skills/skills/web-design-guidelines`
- **Reviewed**: 2026-09-16
- **Absorbed**:
  - 无障碍基础规则（真 button、focus-visible、aria 标注）
  - 键盘导航（Tab、Escape 关闭抽屉）
  - 视口防截断与横向滚动禁令

---

### 4. Jakub Better Interface
- **Repository**: `jakubkrehel/skills`
- **Reviewed**: 2026-09-16
- **Absorbed**:
  - 严格读取项目已有 Token（先查已有规范再动工）
  - 间距数学比例（外边距 ≥ 内边距，按钮水平 = 2x 垂直）
  - 嵌套圆角计算规则（外圆角 - 内边距）

---

### 5. Microsoft Frontend Design Review
- **Repository**: `microsoft/skills/.github/skills/frontend-design-review`
- **Reviewed**: 2026-09-16
- **Absorbed**:
  - 状态完整性检查（Loading/Empty/Error/Boundary）
  - 破坏性操作二次确认门禁
  - 桌面端主流视口多端测试
