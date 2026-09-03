#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, unicodedata

VALID_INTENTS={"CREATE_EPISODE","RESUME","PREPRODUCTION","IMAGE_CONTINUE","REPAIR","RELEASE","DATA_REVIEW"}
RULES=[
("RESUME",("从断点继续","继续上次断点","resume 模式","resume")),
("IMAGE_CONTINUE",("接管前期资产","从生图开始","从图片开始","image_continue","image continue")),
("PREPRODUCTION",("只做前期","不要生成图片","不生图","preproduction_only","preproduction only")),
("REPAIR",("只修","只返修","repair_only","repair only")),
("RELEASE",("只做发布","只做release","release_only","release only")),
("DATA_REVIEW",("数据复盘","只做复盘","data_review","data review"))]
def normalize(text):
    if not isinstance(text,str):raise ValueError("request must be string")
    text=unicodedata.normalize("NFKC",text).replace("\r\n","\n").replace("\r","\n")
    return "\n".join(re.sub(r"[ \t]+"," ",x).strip() for x in text.split("\n") if x.strip()).strip()
def resolve(text):
    n=normalize(text)
    if not n:raise ValueError("EMPTY_REQUEST")
    low=n.lower();intent="CREATE_EPISODE";reason="DEFAULT_CREATE"
    for candidate,signals in RULES:
        if any(s.lower() in low for s in signals):intent=candidate;reason=f"RULE_{candidate}";break
    return {"intent":intent,"source":"deterministic_rules","confidence":1.0,"reason_codes":[reason],
        "normalized_request_sha256":hashlib.sha256(n.encode()).hexdigest(),"normalized_request":n,
        "requires_llm_rewrite":False,"requires_clarification":False}
def expected_intent_for_mode(mode):
    return {"full_auto":"CREATE_EPISODE","resume":"RESUME","preproduction_only":"PREPRODUCTION",
        "image_continue":"IMAGE_CONTINUE","repair_only":"REPAIR","release_only":"RELEASE","data_review":"DATA_REVIEW"}[mode]
def self_test():
    assert resolve("不要生成图片，只做前期")["intent"]=="PREPRODUCTION"
    assert resolve("接管前期资产，从生图开始")["intent"]=="IMAGE_CONTINUE"
    assert resolve("只返修第13张")["intent"]=="REPAIR"
    assert resolve("全自动做一篇「测试」")["intent"]=="CREATE_EPISODE"
    print("REQUEST INTENT SELF-TEST PASS")
def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("resolve");p.add_argument("text");sub.add_parser("self-test");a=ap.parse_args()
    if a.cmd=="self-test":self_test();return 0
    print(json.dumps(resolve(a.text),ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
