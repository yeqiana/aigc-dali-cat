# Story OS V2.2 Visual Narrative Core

主链：

Story / Storyboard
→ Shot Progression + Capture Grammar
→ Visual Narrative Core
→ Resolved Frame Contract
→ Visual Lock 1+3
→ Production Runtime Request
→ Rolling Review
→ Final / Incremental Frame Review

## 每帧必须回答

1. 谁拍的？
2. 摄影者在哪里？
3. 为什么此刻拍？
4. 正在发生什么？
5. 为什么这张会被保存？
6. 相比上一张新增了什么信息？
7. 是否只是同一个异常换了角度？
8. 摄影缺陷是否有真实物理原因？
9. 屏幕/UI 是否物理成立？
10. 人物/衣服/车/道具/路线/天气/光线/异常证据是否连续？

## Narrative Evidence Diversity

Shot Diversity 不等于 Narrative Diversity。

不同角度反复表达同一个事实，不算叙事推进。

Frame 02 以后默认要求 `new_information=true`；
有意重复观察时必须填写 `continuity_exception_reason`。

硬失败：
- GHOST_CAMERA
- CAMERA_OWNER_UNRESOLVED
- MOMENT_RESULT_ONLY
- NARRATIVE_REDUNDANCY
- SHOT_GRAMMAR_REPEAT
- CAMERA_DEFECT_UNMOTIVATED
- SCREEN_CONTENT_PHYSICS_BROKEN
- VISUAL_MEMORY_BROKEN
