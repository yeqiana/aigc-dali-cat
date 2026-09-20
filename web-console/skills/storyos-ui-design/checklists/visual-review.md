# Visual Review Checklist (visual-review.md)

本文件是 StoryOS UI 视觉验收的核查清单。任何界面迭代或代码提交前，必须对照本清单逐项自检。

---

## 核心打分与风险定级 (Scores & Gate)

| 评估维度 | 目标要求 | 含义说明 |
| :--- | :--- | :--- |
| **AI Slop Risk** | **LOW** (严禁 MEDIUM / HIGH) | 衡量界面是否存在 AI 生成的模版味、均质卡片与浮华装饰 |
| **Visual Distinctiveness** | $\ge \mathbf{8}$ / 10 | 界面是否具备专业工业工控台的独特沉浸感与硬核质感 |
| **Operational Scanability** | $\ge \mathbf{8}$ / 10 | 运维人员是否能在 3 秒内扫出一屏内的运行态、瓶颈与阻断项 |

---

## 1. 视觉层级审查 (Visual Hierarchy)
- [ ] 运维人员是否能在 **3 秒内** 找到页面的核心主任务？
- [ ] Primary (任务名称/核心指标) 与 Secondary (字段标签) 是否形成鲜明对比？
- [ ] 技术元数据 (Run ID, 时间戳, Trace Hash) 是否已退居次席（Monospace 弱化），不抢占 Story Name？
- [ ] 主数据网格 (Data Grid) 是否作为绝对视觉主轴，而不是被周边的附属面板瓜分？

## 2. 密度与节奏审查 (Density & Cadence)
- [ ] 界面是否避免了过松的虚假留白？
- [ ] 界面是否避免了文字拥挤粘连、不可辨识的过密情况？
- [ ] 是否严格遵循 4px 基础网格系统（8px/12px 内边距，16px 控件间距，24px 区块间距）？
- [ ] 控件高度是否统一为紧凑标准的 32px（输入框、选择器、默认按钮）？

## 3. 布局与主次审查 (Layout & Structure)
- [ ] 是否彻底杜绝了等宽平铺的四宫格（`1fr 1fr 1fr 1fr`）？
- [ ] 是否体现出非对称布局（如主要运行区占据主导、Trace 占据辅助侧轨）？
- [ ] 顶栏是否采用单条贯穿的 56px **Operational Status Strip**，而非散乱平铺的 6 个独立 KPI 卡片？
- [ ] 次级技术详情是否通过右侧 **440px Inspector Drawer** 渐进式披露？

## 4. 容器与卡片取舍审查 (Cards & Containment)
- [ ] 现有的 Card 是否真的需要全包围 containment？
- [ ] 是否存在可以用 1px 细分割线（`#232830`）或合理 spacing 替代的无意义外边框？
- [ ] 严禁出现 Card 套 Card（Card inside Card）的嵌套冗余；
- [ ] 容器圆角是否严格控制在 3px ~ 6px 之间，彻底消除了 12px~24px 大圆角？

## 5. 文字排版与等宽数字审查 (Typography & Tabular Numbers)
- [ ] Story 剧集标题是否字体鲜明、层级最高？
- [ ] 所有状态代码、毫秒延迟、百分比、倒计时是否启用 `font-mono` 与 `tabular numbers`？
- [ ] 心跳刷新（高频 5 秒轮询）时，数字变化是否平稳、不发生水平宽度抽搐抖动？

## 6. 色彩与语义契约审查 (Color & Semantic Status)
- [ ] 90% 以上的界面是否由中性深灰实体表面（`#0B0D10`、`#13161B`、`#232830`）构成？
- [ ] 状态颜色是否严格限制在 **6px 实心微点 + 12px 状态文字**？
- [ ] 是否杜绝了大面积浓艳的彩色背景底色？
- [ ] 红色警示（`#E05252`）是否仅保留给真正的 BLOCKED 阻塞与 FAILED 致命报错？
- [ ] 绿色（`#3FB950`）是否仅代表健康与完成，而未被滥用为通用主题色？

## 7. 最终去 AI 化判定 (Anti-AI Slop Gate)
- [ ] 是否彻底摆脱了 Generic SaaS Dashboard 模版味？
- [ ] 是否彻底摆脱了 Shadcn 默认黑白灰 Demo 感？
- [ ] 是否消除了任何紫蓝渐变、霓虹流光与毛玻璃投影？
- [ ] 是否删除了所有没有信息增量的营销副标题和套话说明？
