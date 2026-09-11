# Story OS V2.3 Agent Runtime 升级说明

基线：`61be0c4c4e5a3b08e6ccecd025c2970b5f20ac5f`

本升级把刚才约定的三次改造合并到一个一键安装包：
1. Provider Capability / RAW Receipt
2. Runtime Trace
3. Intent Resolver / Request Router

真实 Smoke 的结论被正式写入契约：
桌面内建图像通道不保证 exact RAW canvas，因此系统测量真实 RAW、记录 receipt，并由 NP01 在安全 ratio 阈值内无裁切 Normalize。

后续再做 Tool Registry、Multi-image Batch Runtime、Batch Planner / Frame Mapper。
