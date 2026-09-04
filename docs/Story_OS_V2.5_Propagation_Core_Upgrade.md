# Story OS V2.5.0｜Propagation Core 升级说明

## 目标

把《彼此的天上》EP001 的有效传播规律从复盘经验升级为 Story OS 正式执行能力，只学习结构，不复制题材皮肤。

核心变化：

1. Story Critic 增加 Propagation Core；
2. STORYBOARD_LOCKED 增加 SHAREABILITY LOCK；
3. 强制 `人物主动动作 → 异常直接回应 → 可见后果`；
4. 强制 10 秒可转述；
5. Trigger 默认不晚于序列 50%，更晚必须解释；
6. Visual Narrative 增加传播核角色问题；
7. 发布后漏斗拆为 L3A 认可 / L3B 传播；
8. 发布后数据增加 `绝对数量 → 阶段增量 → 效率/比例`；
9. EP001 进入结构型 Golden Regression 策略，禁止复制川西山路/灯队/远光灯等表层元素。

## 权威原则

- `standards/制作规范_正式版.md` 仍是唯一创作权威；
- 新规范是 active subordinate；
- `meta/story-semantic-review.json` 是独立 Critic 证据，不是第二剧情权威；
- `propagation_core_gate.py` 只校验，不创建第二 Episode stage；
- 历史 Episode 不自动补造 V2.5 PASS。

## 历史 Episode 显式复验

```bash
python episodes/_system/story_review.py run-critic <episode> --attempt 1
python episodes/_system/propagation_core_gate.py verify <episode> --force
```

## 《仲夏夜惊魂》

升级后建议重新跑一次 Story Critic，再用 `--force` 做传播核复验。
如果失败，只局部强化动作—回应链和 Storyboard，不默认推倒已有 Concept。
