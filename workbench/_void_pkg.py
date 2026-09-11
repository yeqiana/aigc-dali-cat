import json, sys, hashlib
from pathlib import Path
ROOT = Path(r"D:\workspace\YeQianWorkSpace\yeqian\aigc-dali-cat")
SYS = ROOT / "episodes" / "_system"
sys.path.insert(0, str(SYS))
import prompt_package, story_json
EP = ROOT / "episodes" / "09_旧物怪谈" / "05_婚礼前夜_记忆麻醉"
EXPECT_PKG = "ab1bd5fbc58e48bd1a30ed0c5829f31bee3f700b94d83a4602c3b96ee8b2f9f8"
EXPECT_CONTRACT = "551c1be47c9686277276019958185a6bce70c1a52232d5dea796c7344f0e1203"
prompt = EP / "docs" / "prompts" / "reveal-order-v2" / "01.txt"
data = prompt_package.compile_frame(EP, 1, prompt, write=False)
print("recompiled scene_prompt_sha256:", data["scene_prompt_sha256"])
print("recompiled package_sha256    :", data["package_sha256"])
print("recompiled contract_sha256   :", data["frame_contract_sha256"])
if data["package_sha256"] != EXPECT_PKG:
    print("MISMATCH: derived cache would not match the recorded admission snapshot; leaving cache untouched")
    sys.exit(2)
if data["frame_contract_sha256"] != EXPECT_CONTRACT:
    print("MISMATCH: frame contract drifted; leaving cache untouched")
    sys.exit(3)
story_json.write_json(EP / "meta" / "runtime" / "prompt-packages" / "01.json", data)
back = story_json.read_json(EP / "meta" / "runtime" / "prompt-packages" / "01.json", default={})
print("written package_sha256:", back.get("package_sha256"))
print("OK: prompt-package 01.json now re-binds the locked asset's scene prompt + frame contract")
q = story_json.read_json(EP / "meta" / "production-queue.json", default={})
item = [i for i in q.get("items") or [] if i.get("id") == "0d0b9814d146"][0]
print("queue item admission snapshot:", json.dumps(item.get("prompt_package"), ensure_ascii=False))
print("queue item status:", item.get("status"), "| output:", item.get("output_path"))
