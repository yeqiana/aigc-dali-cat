import json, os, sys, shutil, hashlib, subprocess, datetime
from pathlib import Path

ROOT = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat")
SYS = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYS))
import scheduler_core, production_recovery

EP = ROOT / "episodes" / "09_旧物怪谈" / "05_婚礼前夜_记忆麻醉"
BK = ROOT / "workbench" / "_void_backup"
BK.mkdir(parents=True, exist_ok=True)
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
EXPECT_PROMPT = "3745e670aa18dadbcb10588ef4b9369ebdd608accdd3f04ba5fac86594e7ab94"
EXPECT_PKG = "ab1bd5fbc58e48bd1a30ed0c5829f31bee3f700b94d83a4602c3b96ee8b2f9f8"
EXPECT_SHA = "cef5b7b929e12b720b6becdbfcded43d3b0f34d0a2f82070741097af5fd812f6"

def fail(msg):
    print("ABORT:", msg); sys.exit(1)

print("=== stage 1: backup ===")
targets = {
    "ledger": EP / "meta" / "production-ledger.json",
    "queue": EP / "meta" / "production-queue.json",
    "prompt01": EP / "docs" / "prompts" / "reveal-order-v2" / "01.txt",
    "package01": EP / "meta" / "runtime" / "prompt-packages" / "01.json",
}
for name, p in targets.items():
    if p.is_file():
        dst = BK / f"{name}.{stamp}.bak"
        shutil.copy2(p, dst)
        print("  backup ->", dst.relative_to(ROOT))

print("=== stage 2: restore frame-01 scene prompt ===")
src = EP / "docs" / "prompts" / "reveal-order-v2" / "01.txt.bak_pre_face_closeup"
dst = EP / "docs" / "prompts" / "reveal-order-v2" / "01.txt"
if not src.is_file():
    fail("prompt backup missing")
body = src.read_text(encoding="utf-8-sig").strip()
dst.write_text(body + "\n", encoding="utf-8", newline="\n")
now_sha = hashlib.sha256(dst.read_text(encoding="utf-8-sig").strip().encode("utf-8")).hexdigest()
print("  prompt01 sha =", now_sha)
if now_sha != EXPECT_PROMPT:
    fail("restored prompt sha mismatch")
print("  OK: matches the scene prompt recorded for the locked frame-01 asset")

print("=== stage 3: ledger tech-fail on the stranded attempt ===")
cp = subprocess.run([sys.executable, str(SYS / "production_ledger.py"), "tech-fail", str(EP),
                     "--frame", "01", "--code", "WORKER_NO_TERMINAL_RECEIPT",
                     "--message", "scheduler worker exited without a terminal receipt (lifecycle BACKEND_INVOKED, no candidate, no SPAN_END); attempt voided by direct user instruction (作废这次尝试)"],
                    cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
print("  rc =", cp.returncode, "|", (cp.stdout or "").strip()[-400:], (cp.stderr or "").strip()[-300:])
if cp.returncode != 0:
    fail("tech-fail failed")

print("=== stage 4: queue repair (void running item, restore generated item) ===")
with scheduler_core.queue_transaction(EP):
    q = scheduler_core.load_queue(EP)
    by_id = {i["id"]: i for i in q.get("items") or []}
    stranded = by_id.get("87d54b6a927d")
    restored = by_id.get("0d0b9814d146")
    if stranded is None or restored is None:
        fail("expected queue items missing")
    if stranded.get("status") != "running":
        fail(f"stranded item status drifted: {stranded.get('status')}")
    executed = stranded.get("execution") or {}
    if executed.get("phase") not in {"WORKER_PENDING", "BACKEND_INVOKED"}:
        fail(f"unexpected transaction phase {executed.get('phase')}")
    msg = ("WORKER_NO_TERMINAL_RECEIPT: worker pid 49464 exited without terminal receipt; "
           "candidate never appeared; attempt voided by direct user instruction (作废这次尝试)")
    production_recovery.mark_terminal(EP, stranded, "TECH_FAILED",
                                     code="WORKER_NO_TERMINAL_RECEIPT", reason=msg)
    stranded["status"] = "tech_failed"
    stranded["completed_at"] = production_recovery.now()
    stranded["last_error"] = msg
    prior = restored.get("status")
    restored["status"] = "generated"
    restored.setdefault("events", []).append({
        "at": production_recovery.now(),
        "event": "STATUS_RESTORED",
        "from": prior,
        "to": "generated",
        "reason": ("the 17:04 replace-admission for the voided frontface-closeup-01e attempt set this "
                   "output-bearing item to superseded; restored because it is the item that produced the "
                   "still-locked frame-01 asset (cef5b7b9) and no replacement ever generated"),
    })
    scheduler_core.save_queue(EP, q)
    print(f"  stranded 87d54b6a927d: running -> tech_failed")
    print(f"  restored 0d0b9814d146: {prior} -> generated (asset sha {EXPECT_SHA[:12]})")

print("=== stage 5: re-lock frame 01 on the unchanged approved asset ===")
reason = ("restored after voiding the stranded frontface-closeup-01e attempt (direct user instruction 作废这次尝试); "
          "approved asset unchanged, original lock was 2026-09-10T11:16:38+08:00 on candidate 0d0b9814d146/cef5b7b9")
cp = subprocess.run([sys.executable, str(SYS / "production_ledger.py"), "lock", str(EP),
                     "--frame", "01", "--reason", reason],
                    cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
print("  rc =", cp.returncode, "|", (cp.stdout or "").strip()[-400:], (cp.stderr or "").strip()[-300:])
if cp.returncode != 0:
    fail("lock failed")

print("=== stage 6: verify ledger state ===")
led = json.loads((EP / "meta" / "production-ledger.json").read_text(encoding="utf-8"))
f = led["frames"]["01"]
print("  status:", f["status"])
print("  lock.sha256:", f["lock"]["sha256"])
print("  approved_asset.sha256:", f["approved_asset"]["sha256"])
print("  current_candidate.sha256:", f["current_candidate"]["sha256"])
print("  content_repairs_used:", f.get("content_repairs_used"), "| user_exception_repairs_used:", f.get("user_exception_repairs_used"))
print("  last attempt:", f["attempts"][-1]["attempt_id"], f["attempts"][-1]["result"], (f["attempts"][-1].get("error") or {}).get("code"))
for k, v in (("lock", f["lock"]["sha256"]), ("approved", f["approved_asset"]["sha256"]), ("current", f["current_candidate"]["sha256"])):
    if v != EXPECT_SHA:
        fail(f"{k} sha drifted: {v}")
if f["status"] != "LOCKED":
    fail("frame 01 not LOCKED")
print("  OK: frame 01 LOCKED, all three SHAs still cef5b7b9")
