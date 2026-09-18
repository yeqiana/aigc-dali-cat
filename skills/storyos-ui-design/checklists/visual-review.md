# StoryOS Visual Review Checklist

用于 CREATE / DIRECTION / POLISH / AUDIT 的最终视觉验收。

## A. Product Fit

- [ ] 页面首先服务“操作 / 扫描 / 决策”，不是展示视觉效果
- [ ] 能明确说出 Primary Surface
- [ ] 业务对象 Story / Run / Stage / Frame 的层级清楚
- [ ] 人工介入项比自动恢复项更醒目

## B. Hierarchy

- [ ] 第一视觉明确且只有一个主角区域
- [ ] 第二、第三层信息明显退后
- [ ] Story 名称强于 Run ID / Trace ID
- [ ] 当前动作强于创建时间等 metadata
- [ ] 主表/工作区明显强于辅助面板

## C. Anti-AI

- [ ] 没有 KPI Card Wall
- [ ] 没有等权四宫格作为默认辅助布局
- [ ] 没有无意义渐变 / glow / glass
- [ ] 没有大面积状态色铺底
- [ ] 没有大量 pill / badge
- [ ] 没有为了“完整”添加的装饰副标题
- [ ] 容器数量合理，结构不依赖 Card 套 Card

## D. Typography / Density

- [ ] Page / Section / Primary / Metadata 字级有明确差异
- [ ] 长 Story 名称不会破坏布局
- [ ] Runtime ID 使用 mono 或低权重表现
- [ ] 表格行高适合长期扫描
- [ ] spacing 主要来自 4px grid
- [ ] 页面没有过松或过密区域突然跳变

## E. Color / Status

- [ ] 状态颜色与 DESIGN.md 一致
- [ ] 不只依赖颜色表达状态
- [ ] Blocked / Failed 具有足够显著度
- [ ] Running / Completed 不抢占过多视觉注意力
- [ ] secondary metadata 保持中性

## F. Containers / Surfaces

- [ ] Panel 真的需要 containment 才存在
- [ ] 普通 Panel 无阴影
- [ ] 圆角 <= 8px，除非明确例外
- [ ] Drawer 是 Inspector 风格，不是“大弹窗”风格
- [ ] 通过 divider / alignment / spacing 建立主要结构

## G. Interaction

- [ ] Hover/focus 清晰但克制
- [ ] Icon-only control 有可访问名称
- [ ] 危险操作有明确危险语义
- [ ] Frame/Run 操作随状态变化，不出现语义错误按钮
- [ ] 自动刷新不关闭 Drawer、不重置滚动和筛选

## H. Viewport / Boundary

建议至少验收当前目标尺寸，并在高风险改版时覆盖：

- [ ] 1366×768
- [ ] 1440×900
- [ ] 1536×864
- [ ] 1920×1080

边界数据：

- [ ] Queue = 0
- [ ] Queue 大值
- [ ] Worker = 0/N
- [ ] Worker = N/N
- [ ] Heartbeat healthy / stale
- [ ] Story 名称超长
- [ ] 0 Frame / 20 Frame
- [ ] 无异常 / 多异常
- [ ] Empty / Loading / Error

## I. Final Questions

必须能肯定回答：

1. 这个页面不像通用 AI SaaS Dashboard 吗？
2. 页面主次是靠排版而不是盒子建立的吗？
3. 用户能在 5–10 秒找到需要处理的 Story 吗？
4. 删除 StoryOS Logo 后，界面仍像一个生产控制台吗？
5. 是否已经达到“够好可用”，可以停止继续微调？
