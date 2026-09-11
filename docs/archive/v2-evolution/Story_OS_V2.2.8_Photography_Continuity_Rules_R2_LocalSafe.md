# V2.2.8 R2 Local-Safe

这个修订版专门解决：

`TARGET_SHA_MISMATCH: episodes/_system/codex_subscription_image.py`

原因：
`codex_subscription_image.py` 是依赖项，不是本升级需要覆盖的目标文件。

R2 行为：

- 不覆盖 `codex_subscription_image.py`
- 不要求它等于某个固定 SHA
- 只验证它仍然依赖 `visual_profile_bridge_v224` / `compile_prompt_contract`
- `visual_profile_bridge_v224.py` 只做两处最小 token patch：
  - `capture_grammar_v226` → `capture_grammar_v228`
- Capture Grammar JSON 使用 deep merge，保留本地未知新增字段
- Photography OS MD 使用 managed marker block，不覆盖已有内容
- 所有修改前备份
- 允许本地 working tree 有未推送修改
- self-test 失败自动回滚
