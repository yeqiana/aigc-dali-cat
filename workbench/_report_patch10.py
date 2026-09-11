import sys
sys.stdout.reconfigure(encoding='utf-8')
BT = chr(96)
P = 'reports/09-05婚礼前夜生产问题复盘_20260910.md'
t = open(P, encoding='utf-8', newline='').read()
orig = t
def bt(s):
    return s.replace('@BT@', BT)
def rep(old, new):
    global t
    o, n = bt(old), bt(new)
    c = t.count(o)
    if c != 1:
        raise SystemExit('MATCH_FAIL %d :: %s' % (c, o[:60]))
    t = t.replace(o, n, 1)

A_OLD = '> 触发：本篇收尾（PUBLISH_READY，快照 86af4964809518ebf70ab5031e6edb595c91783e46a47ecaf230e20890853efd，交付包 05_婚礼前夜_记忆麻醉_DELEGATED_AUTO_F01FACE.zip）后回看全流程。'
A_NEW = A_OLD + '\n> 补充（第 10 节）：2026-09-10 17:02–17:05 有外部会话在收尾冻结期重出帧01，失败后按官方路径作废；由于 production-ledger.json 是快照的绑定证据，快照与交付包一并重建——快照 86af4964… → aaabac0968c9536ecda346fe7478da9a14ed8930595062e4a31e9f5cab69cedf，交付包同名覆盖为 41,111,299 B / 468899f7f37390fb2b0b6f425469c9f1c7a9a3e3bfb4e8e77c2aaa9f4a5d926b。'

B_OLD = '工程层 7 类；根子是失效传播与证据绑定不完整'
B_NEW = '工程层 8 类（第 8 类是冻结期并发写入、缺作废出口，见第 10 节）；根子是失效传播与证据绑定不完整'

C_OLD = '- 探针脚本：@BT@workbench/_retro_probe.py@BT@、@BT@_retro_probe2.py@BT@、@BT@_retro_probe3.py@BT@、@BT@_retro_probe4.py@BT@、@BT@_perf_recompute.py@BT@、@BT@_f01_contract_probe.py@BT@'
C_NEW = C_OLD + '\n- 第 10 节另用到：@BT@meta/production-queue.json@BT@、@BT@meta/image-workers/01-87d54b6a927d-a1.lifecycle.json@BT@ 及同名 jsonl、@BT@meta/runtime/raw-candidate-budget.json@BT@、@BT@meta/runtime/trace-events.jsonl@BT@ 末条、@BT@meta/final-candidate-snapshot.json@BT@、@BT@meta/delegated-release.json@BT@；执行与探针脚本 @BT@workbench/_void_probe.py@BT@、@BT@_void_prompt_find.py@BT@、@BT@_void_apply.py@BT@、@BT@_void_pkg.py@BT@、@BT@_void_snap.py@BT@、@BT@_void_final.py@BT@、@BT@_void_summary.py@BT@、@BT@_retro_void_probe.py@BT@；回滚备份 @BT@workbench/_void_backup/@BT@。'

D_OLD = '- 技术失败 25 次，落在 8 帧；帧01 独占 16 次（64%）。帧01 attempt 21 次，其余帧 2–4 次。'
D_NEW = '- 技术失败 25 次，落在 8 帧；帧01 独占 16 次（64%）。帧01 attempt 21 次，其余帧 2–4 次。（第 10 节那次作废后，账本现计帧01 attempt 22 次、技术失败 17 次，全篇 26 次。）'

SEC10 = '''## 10. 冻结期并发写入：外部会话把帧01 打成 REPAIRING（本次已作废）

本篇已到 PUBLISH_READY、帧01 已锁、发布图已出之后，2026-09-10 17:02–17:05，另一个外部会话直接对帧01 发起近景重出。worker 死在 @BT@BACKEND_INVOKED@BT@，没有产物也没有终态收据，把三处权威记录留在了半成品状态。

- 时间线（逐条可复核）：17:02:45 @BT@docs/prompts/reveal-order-v2/01.txt@BT@ 被改写成近景版（606 B，备份 @BT@workbench/_void_backup/prompt01.20260910_171822.bak@BT@）→ 17:03:25 排队 @BT@dc4beaa1ea5f@BT@ 被拒（BEGIN_REJECTED：repair 需要 @BT@REPAIR_AUTHORIZED / AUTHORITY_REFRESH_AUTHORIZED / EXCEPTION_REPAIR_AUTHORIZED / TECH_FAILED@BT@ 之一）→ 17:04:16 账本写入 @BT@user_exception_authorizations[0]@BT@（approval_basis=direct_user_review_exception）→ 17:04:30 新排队 @BT@87d54b6a927d@BT@、worker pid 49464 启动、额度 claim @BT@authorized_raise=4@BT@、lifecycle 停在 @BT@BACKEND_INVOKED@BT@、trace 只有 @BT@SPAN_START SP_dd639b7e60a5404d@BT@ → 17:05:20 worker 日志停在 @BT@Reconnecting... 2/5 (request timed out)@BT@，进程消失，无产物、无 @BT@SPAN_END@BT@。
- 破坏一（账本）：帧01 从 @BT@LOCKED@BT@ 被写成 @BT@REPAIRING@BT@，锁还在但阶段不可信（备份 @BT@workbench/_void_backup/ledger.20260910_171822.bak@BT@ 里就是这个状态）。
- 破坏二（队列）：@BT@87d54b6a927d@BT@ 永久 @BT@running@BT@，调度器以为这帧还在途。
- 破坏三（证据链）：@BT@--replace@BT@ 把帧01 所有 @BT@generated@BT@ 条目刷成 @BT@superseded@BT@，包括真正产出锁图的 @BT@0d0b9814d146@BT@；baseline 门禁据此判帧01 未生成。
- 官方 reconcile 救不回来：worker 死在 @BT@BACKEND_INVOKED@BT@，只能判 @BT@interrupted_unknown@BT@ → @BT@RECONCILE_PENDING@BT@，没有任何入口把这件事回收成没发生。
- 本次作废（四步，都走官方入口）：① @BT@01.txt@BT@ 回滚到近景改写前（与 @BT@01.txt.bak_pre_face_closeup@BT@ 逐字节一致，707 B / raw sha256 @BT@48d5be97…@BT@；框架口径的 prompt 哈希回到 @BT@3745e670…@BT@，与锁定尝试 @BT@b8b0eb8f10e6@BT@ 的记录一致）；② @BT@production_ledger.py tech-fail --frame 01 --code WORKER_NO_TERMINAL_RECEIPT@BT@ 记技术失败，再用官方 @BT@lock@BT@ 把 @BT@cef5b7b9…@BT@ 补回 @BT@LOCKED@BT@；③ 队列 @BT@87d54b6a927d@BT@ → @BT@tech_failed@BT@、@BT@0d0b9814d146@BT@ → @BT@generated@BT@；④ prompt-package 重编译 → @BT@ab1bd5fb…@BT@，与锁定帧绑定的包哈希一致。
- 连带重建：@BT@production-ledger.json@BT@ 是快照的绑定证据，作废后必须重建快照与交付包 → 快照 86af4964… → @BT@aaabac09…@BT@，交付包同名覆盖为 41,111,299 B / @BT@468899f7…@BT@（作废前那份已被覆盖，无法再逐字节复核）。发布图未动：正文 01 @BT@fb8f99e1…@BT@、封面 @BT@adeea84e…@BT@。
- 代价：这次一个像素都没产出，却吃掉帧01 唯一一次用户例外额度（@BT@user_exception_repairs_used=1@BT@），对应的额度 claim 停在未 commit；授权记录按规矩保留，不删。

根因（四条，都不是手滑）：

1. 双会话没有占用声明：本篇的锁帧、快照和交付包都在本线程，另一个会话却能直接写同一份账本、队列和提示词；框架没有冻结期写入闸或租约。
2. 用户消息的语用被误读：17:04:16 那条授权的 approval_text 引用的是用户“还有一个问题……这个也是问题，记录进去”——那句话的语境是写进复盘，被当成了现在重出。授权文本与真实意图不一致，门禁看不出来。
3. 缺 void / abandon 官方出口：重出失败后没有取消这次尝试的标准动作，只能 @BT@tech-fail@BT@ 加手工 @BT@lock@BT@ 补回；例外额度也不随作废归还。
4. 门禁对已锁帧缺兜底：@BT@generated@BT@ 被刷成 @BT@superseded@BT@ 后 baseline 直接判未生成，没有“账本已有 LOCKED 帧且 SHA 未漂移”的兜底。

现状：本篇已复原并重新验证（@BT@validate_episode --target PUBLISH_READY@BT@ = PASS clean；@BT@final_candidate_snapshot.py verify@BT@ = PASS；账本 20 帧全 @BT@LOCKED@BT@，帧01 为 @BT@cef5b7b9…@BT@）；上面四条均为机制缺口，未修。'''

E_OLD = '## 10. 建议优先级（仅记录，未执行）'
E_NEW = SEC10 + '\n\n## 11. 建议优先级（仅记录，未执行）'

F_OLD = '6. 评审：critic 禁用 @BT@-o@BT@；提供 supersede-review 命令替代手工删文件。'
F_NEW = F_OLD + '\n7. 冻结期写入闸：状态进入 PUBLISH_READY 或已交付后，账本、队列、提示词的写入需要显式重开动作或租约，外部会话不得直接改。\n8. 官方 void-attempt 出口：提供作废在途 attempt 的标准命令，一次回滚提示词、账本阶段、队列状态与额度 claim，不靠手工补 lock。\n9. baseline 门禁兜底：候选条目被 superseded 时，若账本该帧为 LOCKED 且 SHA 未漂移，不得判未生成。\n10. 调度器租约与启动清扫：worker 启动写租约，心跳缺失即判死并回收 running 条目，避免永久悬挂。'

G_OLD = '记录时间：2026-09-10（Asia/Shanghai）。本文件为复盘记录，不构成门禁证据，不改变任何阶段状态。'
G_NEW = '记录时间：2026-09-10（Asia/Shanghai）。第 10 节于当日 17:31 追加（17:18 完成作废、17:22 完成快照与交付包重建）。本文件为复盘记录，不构成门禁证据，不改变任何阶段状态。'

rep(A_OLD, A_NEW)
rep(B_OLD, B_NEW)
rep(C_OLD, C_NEW)
rep(D_OLD, D_NEW)
rep(E_OLD, E_NEW)
rep(F_OLD, F_NEW)
rep(G_OLD, G_NEW)
open(P, 'w', encoding='utf-8', newline='').write(t)
print('WROTE bytes', len(t.encode('utf-8')), 'was', len(orig.encode('utf-8')))
