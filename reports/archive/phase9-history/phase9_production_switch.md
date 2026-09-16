# Story OS V3 Phase9 Production Switch（P9.34.3）

更新时间：

2026-09-10

## 1. 目标

阻塞项 #7「生产归属切换」此前只有决策证据（Canary 演练产出 SWITCH_TO_V3），归属切换未执行。本批补齐执行与持久化：交付切换执行器，把生产归属从 V2_RUNTIME 切到 V3_RUNTIME 并落盘为 meta/runtime/runtime-primary.json。默认 dry-run，不改变系统状态；授权后 --apply 才落盘。

## 2. 交付内容

- platform/gateway/runtime_primary_persistence.py：RuntimePrimaryRecord 的原子落盘 / 读取
- scripts/phase9_production_switch.py：status / switch 子命令，默认 dry-run
- tests/platform/test_phase9_production_switch.py：离线回归 7 例

安全姿态：

- 默认 dry-run，不改变 meta/runtime/runtime-primary.json
- 只支持 --to V3_RUNTIME（回退由 Canary rollback 负责，不在此处）
- 不删除 V2 runtime、不改 episode state / release 资产、不写凭据
- 文件缺失时返回 V2_RUNTIME initial（诚实默认，不猜测）

## 3. 验证证据

### 离线回归

tests/platform：329 passed（基线 322 + switch 新增 7）

新增 7 例覆盖：

- load 缺文件返回 V2 initial
- save + load roundtrip（含原子写无残留 tmp）
- plan_switch V2 -> V3 产生 previous=V2
- plan_switch V3 -> V3 不变
- CLI status / switch dry-run / switch --apply

### 真机 dry-run（2026-09-10）

- status：读当前 V2_RUNTIME（文件缺失，返回 initial）
- switch（无 --apply）：打印「V2 -> V3」，未落盘 runtime-primary.json

## 4. 边界

- 未执行 switch --apply（生产归属切换需显式授权）。
- 归属文件 meta/runtime/runtime-primary.json 属本地事实证据，已被 .gitignore 忽略。

## 5. 结论

生产归属切换执行器已交付并 dry-run 验证。阻塞项 #7 由「未执行归属切换」收敛为「切换执行器已交付，授权后一条命令即可切换」。
