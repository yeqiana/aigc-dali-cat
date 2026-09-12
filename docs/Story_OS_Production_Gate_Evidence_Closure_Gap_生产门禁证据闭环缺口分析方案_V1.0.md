# Story OS Production Gate Evidence Closure Gap 生产门禁证据闭环缺口分析方案 V1.0

更新时间：
2026-09-12

Episode：
天界普通人的一天

---

# 一、问题背景

本次生产中：

- 图片资产 20/20 已完成
- approved 资产已生成
- 大部分 Frame 已通过生产审核

但是推进：

```
VISUAL_CALIBRATED
        ↓
PRODUCTION_PASSED
```

时被 machine gate 阻塞。

---

# 二、实际阻塞原因

## 1. Story Semantic Trace 缺失

Machine Gate 报错：

```
story_semantic_trace_missing
```

涉及 Frame：

```
03
04
05
08
09
10
11
12
13
14
15
```

原因：

Frame 生产完成，但是：

```
Frame Contract
      ↓
Image Asset
      ↓
Review
      ↓
Story Semantic Trace
```

中间 Trace 没有自动闭环。

---

## 2. Frame03 人工接受未进入机器状态

当前：

```
Frame03
status=NEEDS_USER
```

用户已确认：

- 问题已知
- 接受当前结果
- 不继续消耗返修额度

但是系统没有对应状态：

```
HUMAN_ACCEPT_PENDING
```

导致 Gate 仍认为：

```
production_status != PASSED
```

---

# 三、根因分析

## 根因1

生产事实和门禁证据生成解耦。

当前：

```
Image Production

完成

但

Evidence Closure

未自动执行
```

---

## 根因2

人工决策没有标准状态模型。

当前：

```
NEEDS_USER
```

同时承担：

- 真正等待用户处理
- 用户已经确认

两个含义。

---

# 四、治理方向

## Story Semantic Trace 自动闭环

生产完成后：

自动生成：

```
frame_semantic_trace.json
```

来源：

- frame contract
- storyboard
- review
- asset manifest

---

## Frame 人工接受状态

新增语义：

```
HUMAN_ACCEPTED
```

生命周期：

```
NEEDS_USER
      ↓
USER_ACCEPT
      ↓
HUMAN_ACCEPTED
      ↓
PRODUCTION_PASSED
```

---

# 五、本次实例

作为 V3 真实生产案例：

```
天界普通人的一天

20 Frame

19 自动通过

1 Frame 人工接受

Evidence Closure 缺失

Production Gate 阻塞
```

---

# 六、后续实施

1. 补齐 Semantic Trace 生成链
2. 增加 Human Accept 状态
3. Gate 支持人工确认后的 Frame
4. 增加回归测试

原则：

> 生产完成不代表门禁完成，生产证据必须自动闭环。
