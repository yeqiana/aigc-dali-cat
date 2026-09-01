# 千寻 EP001 Codex 自动执行规范

Episode:
千与千寻 EP001

章节来源：
必须读取项目中锁定的 EP01 Chapter Lock。

视觉选择：

方案A：
visual_profile_id = DEFAULT

方案B：
visual_profile_id = SPIRITED_AWAY_LIVE_ACTION_V1


Codex执行：

1. 读取 EP01 Story Lock
2. 读取 Character Master
3. 读取 Location Master
4. 读取 visual_profile_id
5. 合并生成 Frame Contract
6. 执行 Visual Lock
7. 执行 Production

禁止：
- 自行改变章节剧情
- 自行切换画风
- 使用动画化脸型
- 使用CG游戏渲染感

推荐配置：

episode.yaml:

visual:
  profile_id: SPIRITED_AWAY_LIVE_ACTION_V1

chapter:
  source: EP01
