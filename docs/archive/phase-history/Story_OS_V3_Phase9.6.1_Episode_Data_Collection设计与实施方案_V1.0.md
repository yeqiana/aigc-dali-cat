# Story OS V3 Phase9.6.1 Episode Data Collection 设计与实施方案 V1.0

## 目标

建立真实内容生产数据采集规范，为 Phase9.6 Growth Validation 提供输入。

核心：

```text
Episode生产
    ↓
发布数据
    ↓
统一反馈模型
    ↓
Memory学习
```

## 数据来源

第一阶段采用人工录入：

- EP001
- EP002
- EP003+

后续可接入平台接口。

## Episode Feedback 数据

统一字段：

```text
episode_id
platform
publish_time
view_count
like_count
comment_count
share_count
favorite_count
completion_rate
follower_growth
content_pattern
learning_notes
```

## 数据流程

```text
Episode Feedback

        ↓

ProductionFeedback

        ↓

PerformanceAnalyzer

        ↓

ExperienceStore

        ↓

PatternLearning
```

## 验收标准

输入真实 Episode 数据后，系统能够：

1. 保存作品表现数据
2. 生成学习信号
3. 提取内容规律
4. 输出下一次生产建议
