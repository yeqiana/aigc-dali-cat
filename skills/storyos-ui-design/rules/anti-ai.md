# Anti-AI UI Rulebook

用于 StoryOS 可见界面的生成、改版和视觉审查。

## 1. 首要判断

如果页面换掉 Logo、项目名后，可以无缝变成任意“AI SaaS Dashboard”，则视觉方向不通过。

StoryOS 必须表现出自己的工作对象：Story、Run、Stage、Frame、Queue、Worker、Trace、Artifact、Intervention。

## 2. 常见 AI Slop 信号

以下信号出现 3 个以上时，进入视觉重审：

- 一屏多个等宽 KPI Card
- 彩色图标方块 + 大数字 + 小标签
- 四个或更多等宽底部 Card
- 12px+ 大圆角遍布页面
- 每块都有 border + surface + title + icon
- 紫/蓝/绿渐变或霓虹点缀
- Badge/Pill 过量
- 状态色大面积铺底
- 所有模块同等视觉权重
- 过量说明性副标题
- 为“科技感”加入 glow / blur / glass
- Bento Grid 没有真实信息结构依据
- 空间过松，数据密度与运维场景不匹配
- 每个 hover 都抬升/阴影
- 设计依赖 Card 而不是 typography / spacing / divider

## 3. 去 AI 味处理顺序

不要先换颜色。按顺序处理：

1. 删除无价值模块和说明
2. 确定 Primary Surface
3. 打破等权布局
4. 减少容器层级
5. 建立 typography hierarchy
6. 调整 density / spacing
7. 降低状态色面积
8. 收紧 radius / shadow
9. 最后才调整局部色彩和 motion

## 4. Equal Weight Check

重点检查：

- 底部模块是否全部同宽同高
- KPI 是否全部同面积
- 每个模块标题是否一样显眼
- 主表是否与辅助区视觉权重接近

StoryOS Production Monitor 的主表必须明显强于 Worker / Queue / Trace 等辅助信息。

## 5. Container Budget

一个桌面 viewport 内，不应为了分区给所有区域都增加独立 Card。

优先使用：

- 共享背景
- spacing
- section divider
- column alignment
- typography

Panel 只在以下情况使用：

- 需要明确 containment
- 有独立滚动/交互上下文
- 有明显不同的背景层级
- Inspector / Drawer / Popover 等独立工作区

## 6. Color Budget

默认同时高显著度语义色不超过 3 种。

红色仅用于真正需要处理的问题；绿色不作为普通装饰色。

辅助元数据默认中性色。

## 7. Copy Hygiene

删除不帮助决策的文案：

- 视觉风格自我说明
- 重复标题
- 解释显而易见的控件
- “Console v1.0”“高密度生产调度”一类装饰文案（除非真实版本管理需要）

## 8. Dashboard Specific

StoryOS Dashboard / Monitor 默认：

- status strip，不做 KPI card wall
- toolbar 尽量单行
- primary data grid 最大化
- secondary area 非均质布局
- event/trace 允许窄栏化
- Inspector 优先 Drawer，不再开多层 Modal

## 9. Distinctiveness Test

视觉完成后问：

- 它是否体现 StoryOS 的 Story → Run → Stage → Frame 模型？
- 是否体现“生产”和“介入”语义？
- 是否一眼知道什么需要人工处理？
- 如果截图去掉 Logo，是否仍能看出这是生产控制台而非普通 SaaS Dashboard？

若全部不能回答，视觉方向需要重做，而不是继续 polish。
