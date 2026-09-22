# Story OS Learning Calibration Dataset

Phase9.5 Real Data Calibration.

用于存放真实 Episode 发布效果数据，作为 Production Learning Loop 的输入。

数据流：

```
Episode Feedback
        ↓
Learning Calibration Loader
        ↓
Production Feedback
        ↓
Experience Store
        ↓
Pattern Learning
```

当前阶段使用人工录入数据，后续可接入平台数据。
