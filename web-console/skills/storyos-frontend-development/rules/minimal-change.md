# Rule: Minimal Change & Project Context

- **PRESERVE 优先**：已有已验证页面与业务逻辑默认 PRESERVE，新增模块 EXTEND；
- **禁止单向重构**：严禁借修复一个按钮顺带破坏重构整个页面；
- **目录结构与设计系统**：严格遵守 `/src` 下现有组件结构（`components/views/`、`components/layout/`），复用公共组件；
- **依赖库收敛**：不得未沟通擅自引入新依赖包，优先使用已有标准工具（`lucide-react`, `motion/react`）与 CSS/现有组件；简单图表不得为单一视图重新引入重量级图表运行时。
