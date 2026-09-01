# Story OS V2.1.2 Visual Profile Selector Upgrade

用途：
为 Story OS 增加可选择视觉风格与质感 Profile 的能力。

支持：
1. 默认画风 DEFAULT
2. 千与千寻真人电影质感 SPIRITED_AWAY_LIVE_ACTION_V1

Codex 自动生产流程：
Episode 配置声明 visual_profile_id
↓
读取 episode chapter lock
↓
加载对应 Visual Profile
↓
生成 Frame Contract
↓
执行 Asset Lock / Visual Lock / Production

安装：
python -X utf8 install.py --repo <仓库路径>
