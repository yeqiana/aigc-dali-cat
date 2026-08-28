# Story OS V1.7 — Production Reliability

V1.7 不改变 V1.6 Golden Path 的七阶段与单一状态源，只补生产可靠性。

## 新增

- `episodes/_system/transport_guard.py`
  - 技术重试 request fingerprint 不可漂移；
  - 网络/超时/后端/限流/无候选/auth 分类；
  - 连续失败熔断；
  - `meta/transport-state.json` 只保存传输证据，不保存剧集 stage。
- `episodes/_system/text_audit.py`
  - 非静默空字幕、48 字上限、声音卡 forbidden terms 为硬失败；
  - AI 腔、连续三图句式/长度、重复字幕、声音卡缺项为警告；
  - 只审计，不自动改写。
- `episodes/_system/text_revision.py`
  - `start → diff → submit → approve/revert`；
  - 文字专修期间保护 approved/publish 图片、reference、release manifest、production ledger、episode state、story gates。
- `episodes/_system/test_production_reliability.py`
  - 覆盖 transport、text audit、text revision 与保护资产阻断。

## Story OS CLI

新增：

```bash
python episodes/_system/story_os.py transport <episode> preflight <frame>
python episodes/_system/story_os.py audit-text <episode> --file <subtitles.yaml>
python episodes/_system/story_os.py text-revision <episode> start --file <path>
```

## 保持不变

- `meta/episode-state.json` 仍是唯一阶段事实源；
- 七阶段不变；
- 每帧最多一次内容返修不变；
- 三张校准 + 四张视觉准入不变；
- 最小修改协议不变；
- 不引入 `skip review`。
