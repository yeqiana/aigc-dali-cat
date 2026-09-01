# Story OS V2.1.1 R3 Runtime Closure 一键升级包

目标：
- Performance Replay 真实化
- Runtime SHA Chain
- Speculative Production 安全收敛
- 精确 Rollback
- Package Manifest 校验
- Critical Path Telemetry

安装：
python -X utf8 install.py --repo <story仓库路径>

默认：
- 自动备份
- SHA校验
- 回归检查
- 失败自动回滚

本包只修改 Runtime，不修改 Story / Character / Frame Contract 内容资产。
