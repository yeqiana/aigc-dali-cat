#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, base64, datetime as dt, getpass, hashlib, json, os, re, shutil, subprocess, tempfile, time, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PLAN=Path("meta/auto-production-plan.json")
STATE=Path("meta/auto-production-state.json")
REPORT=Path("meta/auto-production-report.json")
IMAGE_MODEL=os.getenv("STORY_OS_IMAGE_MODEL","gpt-image-2")
PLAN_MODEL=os.getenv("STORY_OS_PLANNER_MODEL","gpt-5.6-terra")
REVIEW_MODEL=os.getenv("STORY_OS_REVIEW_MODEL","gpt-5.6-terra")

def now(): return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")
def readj(p): return json.loads(p.read_text(encoding="utf-8"))
def writej(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def shat(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def deps():
    try:
        from PIL import Image,ImageOps,ImageDraw,ImageFont
        return Image,ImageOps,ImageDraw,ImageFont
    except Exception as e: raise SystemExit("Pillow missing; rerun INSTALL_V2_0.bat: "+str(e))
def client():
    try:
        from openai import OpenAI
    except Exception as e:
        raise SystemExit("OpenAI SDK missing; rerun INSTALL_V2_0.bat: "+str(e))
    key=os.getenv("OPENAI_API_KEY","").strip() or getpass.getpass("OPENAI_API_KEY (not saved): ").strip()
    if not key: raise SystemExit("OPENAI_API_KEY required for unattended OpenAI backend")
    kw={"api_key":key}
    base=os.getenv("STORY_OS_OPENAI_BASE_URL","").strip()
    if base: kw["base_url"]=base
    return OpenAI(**kw)
def epdir(raw):
    if not raw: raw=input("Episode directory: ").strip().strip('"')
    p=Path(raw).expanduser().resolve()
    if not p.is_dir(): raise SystemExit("episode directory not found")
    try:p.relative_to(ROOT.resolve())
    except:raise SystemExit("episode must be inside repository")
    return p
def frame_count(ep):
    p=ep/"meta"/"release-manifest.json"
    if p.exists():
        n=((readj(p).get("release") or {}).get("body_frame_count"))
        if isinstance(n,int) and n>0:return n
    return 20
def aspect(ep):
    p=ep/"meta"/"release-manifest.json"
    if p.exists():
        a=((readj(p).get("episode") or {}).get("aspect_ratio"))
        if a in ("4:5","9:16"):return a
    return "4:5"
def extract_json(t):
    t=t.strip()
    if t.startswith("```"): t=re.sub(r"^```(?:json)?\s*","",t);t=re.sub(r"\s*```$","",t)
    try:return json.loads(t)
    except:
        a=t.find("{");b=t.rfind("}")
        return json.loads(t[a:b+1])
def context(ep,limit=70000):
    rows=[]
    for ext in ("*.md","*.json","*.yaml","*.yml"):
        for p in ep.rglob(ext):
            if any(x in p.parts for x in ("production","deliveries","frame-reviews","text-revisions")):continue
            if p.name.startswith("auto-production-"):continue
            try:t=p.read_text(encoding="utf-8")
            except:continue
            rel=p.relative_to(ep).as_posix()
            pri=0 if any(k in rel.lower() for k in ("story","storyboard","分镜","故事","字幕","caption","readme")) else 1
            rows.append((pri,rel,t))
    rows.sort()
    out=""; 
    for _,r,t in rows:
        x=f"\n===== {r} =====\n{t}"
        if len(out)+len(x)>limit:x=x[:limit-len(out)]
        out+=x
        if len(out)>=limit:break
    if not out:raise SystemExit("No locked story/storyboard source found")
    return out
def validate_plan(d):
    n=d.get("frame_count")
    if not isinstance(n,int) or n<4:raise ValueError("frame_count invalid")
    if d.get("aspect_ratio") not in ("4:5","9:16"):raise ValueError("aspect invalid")
    fs=d.get("frames")
    if not isinstance(fs,list) or len(fs)!=n:raise ValueError("frames count mismatch")
    if [x.get("number") for x in fs]!=list(range(1,n+1)):raise ValueError("frames must be 1..N")
    for f in fs:
        p=str(f.get("prompt","")).strip()
        if not p:raise ValueError(f"frame {f.get('number')} prompt empty")
        if len(p)>260 or len(p.encode("utf-8"))>900:raise ValueError(f"frame {f.get('number')} prompt exceeds 260 chars/900 bytes")
        if len(str(f.get("caption","")))>60:raise ValueError(f"frame {f.get('number')} caption too long")
    cal=d.get("calibration_frames") or [];vis=d.get("visual_admission_frames") or []
    if len(cal)!=3 or len(set(cal))!=3:raise ValueError("calibration_frames must be 3 distinct")
    if len(vis)!=4 or len(set(vis))!=4 or not set(cal)<=set(vis):raise ValueError("visual_admission_frames invalid")
    return True
def plan_prompt(ep):
    n=frame_count(ep);a=aspect(ep)
    return f"""Compile the EXISTING LOCKED Chinese Douyin photo story into production JSON. Never change plot, ending, relations, era, location or locked causal chain. Return JSON only.
frame_count={n}, aspect_ratio={a}.
Fields: schema_version=2, story_os_version=2.0, episode_id, title, frame_count, aspect_ratio, capture_profile_id CP01..CP08, global_visual_lock, calibration_frames exactly 3, visual_admission_frames exactly 4 including calibration, publish {{title,intro,topics}}, frames.
Each frame: {{number,beat,prompt,caption,review_focus}}.
Numbers exactly 1..{n}. Prompt <=260 chars AND <=900 UTF-8 bytes. Caption natural first-person <=48 Chinese chars or empty.
Image rules: real Chinese private phone/camera album, available light, imperfect composition, no commercial HDR/cinematic lighting, physical first-person viewpoint, no unexplained current camera visible, anomaly embedded in ordinary reality, no publication title/watermark/platform UI in base image.
Calibration roles: ordinary baseline, worst plausible capture condition, first major anomaly. Fourth visual admission should be climax or highest continuity-risk frame.
"""
def build_plan(ep,c=None,force=False):
    p=ep/PLAN
    if p.exists() and not force:
        d=readj(p);validate_plan(d);return d
    c=c or client()
    r=c.responses.create(model=PLAN_MODEL,input=plan_prompt(ep)+"\nLOCKED SOURCE:\n"+context(ep))
    d=extract_json(r.output_text);validate_plan(d);writej(p,d);print("PLAN CREATED",p);return d
def target(a):return (1080,1350) if a=="4:5" else (1080,1920)
def fpaths(ep,n):
    k=f"{n:02d}"
    return {"raw":ep/"production"/"auto"/"raw"/f"{k}.png","cand":ep/"production"/"auto"/"candidates"/f"{k}.png","approved":ep/"production"/"approved"/f"{k}.png","publish":ep/"production"/"publish"/f"{k}.png","prompt":ep/"production"/"auto"/"prompts"/f"{k}.txt"}
def dirs(ep):
    for x in ("production/auto/raw","production/auto/candidates","production/auto/prompts","production/approved","production/publish","deliveries"):(ep/x).mkdir(parents=True,exist_ok=True)
def fit(src,dst,a):
    Image,ImageOps,_,_=deps();w,h=target(a)
    with Image.open(src) as im:
        im=ImageOps.fit(im.convert("RGB"),(w,h),method=Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True,exist_ok=True);im.save(dst,"PNG",optimize=True)
def gen_openai(c,prompt,out,quality,model):
    r=c.images.generate(model=model,prompt=prompt,size="1024x1536",quality=quality)
    item=r.data[0];b=getattr(item,"b64_json",None)
    if b:out.write_bytes(base64.b64decode(b));return
    u=getattr(item,"url",None)
    if u:
        import urllib.request
        with urllib.request.urlopen(u,timeout=180) as z:out.write_bytes(z.read())
        return
    raise RuntimeError("image response missing b64_json/url")
def gen_command(prompt_file,out,n):
    tpl=os.getenv("STORY_OS_IMAGE_COMMAND","").strip()
    if not tpl:raise RuntimeError("STORY_OS_IMAGE_COMMAND not set")
    cmd=tpl.format(prompt_file=str(prompt_file),output=str(out),frame=f"{n:02d}")
    subprocess.run(cmd,shell=True,check=True,cwd=ROOT)
    if not out.exists():raise RuntimeError("command produced no output")
def data_url(p):return "data:image/png;base64,"+base64.b64encode(p.read_bytes()).decode("ascii")
def review(c,img,plan,frame,model,mode):
    if mode=="local":
        Image,_,_,_=deps()
        with Image.open(img) as im: ok=im.size==target(plan["aspect_ratio"])
        return {"decision":"pass" if ok else "repair","score":10 if ok else 0,"issues":[] if ok else ["wrong dimensions"]}
    prompt=f"""Review one frame for a Chinese real-phone-album suspense carousel. Return JSON only: {{"decision":"pass"|"repair","score":0-10,"issues":["..."],"repair_instruction":"..."}}.
Hard fail: impossible first-person viewpoint, unexplained camera/photographer visible, identity/key-prop/location continuity break, cinematic/commercial look, wrong era/device physics, contradiction with locked beat. Judge private album realism, anomaly not over-staged.
Global lock: {plan.get('global_visual_lock','')}
Capture: {plan.get('capture_profile_id','')}
Frame {frame['number']} beat: {frame.get('beat','')}
Requested: {frame.get('prompt','')}
"""
    r=c.responses.create(model=model,input=[{"role":"user","content":[{"type":"input_text","text":prompt},{"type":"input_image","image_url":data_url(img)}]}])
    d=extract_json(r.output_text);dec=str(d.get("decision","")).lower()
    if dec not in ("pass","repair"):raise RuntimeError("invalid review decision")
    d["decision"]=dec;return d
def state0(plan):
    return {"schema_version":1,"story_os_version":"2.0","created_at":now(),"updated_at":now(),"user_requested_unattended_run":True,"human_approval_written":False,"frames":{f"{f['number']:02d}":{"status":"PENDING","attempts":[],"approved_sha256":None} for f in plan["frames"]}}
def load_state(ep,plan):
    p=ep/STATE
    if p.exists():return readj(p)
    d=state0(plan);writej(p,d);return d
def save_state(ep,d):d["updated_at"]=now();writej(ep/STATE,d)
def order(plan):
    o=[]
    for x in plan["calibration_frames"]+plan["visual_admission_frames"]+list(range(1,plan["frame_count"]+1)):
        if x not in o:o.append(x)
    return o
def done(ep,s,n):
    p=fpaths(ep,n)["approved"];r=s["frames"][f"{n:02d}"]
    return r.get("status")=="APPROVED" and p.exists() and r.get("approved_sha256")==sha(p)
def run_frame(ep,plan,s,frame,provider,c,quality,image_model,review_mode,review_model):
    n=frame["number"];k=f"{n:02d}";ps=fpaths(ep,n)
    if done(ep,s,n):print(k,"SKIP approved/hash valid");return
    ps["prompt"].parent.mkdir(parents=True,exist_ok=True);ps["prompt"].write_text(frame["prompt"]+"\n",encoding="utf-8")
    issues=[]
    for attempt in (1,2):
        prompt=frame["prompt"] if not issues else frame["prompt"]+"；返修：只修"+ "、".join(issues)[:120]+"，不改剧情和主体身份。"
        rec={"attempt":attempt,"started_at":now(),"provider":provider,"image_model":image_model,"locked_prompt_sha256":shat(frame["prompt"]),"effective_prompt_sha256":shat(prompt)}
        s["frames"][k]["attempts"].append(rec);s["frames"][k]["status"]="GENERATING";save_state(ep,s)
        print(k,"GENERATE",attempt)
        try:
            if provider=="openai":gen_openai(c,prompt,ps["raw"],quality,image_model)
            elif provider=="command":
                ps["prompt"].write_text(prompt+"\n",encoding="utf-8");gen_command(ps["prompt"],ps["raw"],n)
            elif provider=="mock":
                Image,_,ImageDraw,_=deps();im=Image.new("RGB",target(plan["aspect_ratio"]),(90,100,110));ImageDraw.Draw(im).text((50,50),k,fill="white");im.save(ps["raw"])
            else:raise RuntimeError("unknown provider")
            fit(ps["raw"],ps["cand"],plan["aspect_ratio"])
            rv=review(c,ps["cand"],plan,frame,review_model,"local" if provider=="mock" else review_mode)
            rec["review"]=rv;rec["completed_at"]=now()
            if rv["decision"]=="pass":
                ps["approved"].parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ps["cand"],ps["approved"])
                rec["result"]="pass";s["frames"][k]["status"]="APPROVED";s["frames"][k]["approved_sha256"]=sha(ps["approved"]);save_state(ep,s);print(k,"APPROVED",rv.get("score"));return
            issues=rv.get("issues") or [rv.get("repair_instruction") or "真实性未通过"];rec["result"]="content_failed";s["frames"][k]["status"]="REPAIRING" if attempt==1 else "NEEDS_USER";save_state(ep,s)
        except Exception as e:
            rec["result"]="technical_failure";rec["error"]=str(e);rec["completed_at"]=now();s["frames"][k]["status"]="TECH_FAILED";save_state(ep,s)
            if attempt==1:time.sleep(2);continue
            raise
    raise SystemExit(k+" automatic repair failed; no FINAL ZIP created")
def fonts():
    out=[];env=os.getenv("STORY_OS_FONT","").strip()
    if env:out.append(Path(env))
    if os.name=="nt":
        d=Path(os.environ.get("WINDIR","C:/Windows"))/"Fonts";out += [d/"msyh.ttc",d/"msyhbd.ttc",d/"simhei.ttf"]
    out += [Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    return [x for x in out if x.exists()]
def render(base,out,text):
    Image,_,ImageDraw,ImageFont=deps()
    with Image.open(base) as im:
        im=im.convert("RGB")
        if text:
            fs=50;fl=fonts()
            if not fl:raise RuntimeError("No font found; set STORY_OS_FONT")
            font=ImageFont.truetype(str(fl[0]),fs);d=ImageDraw.Draw(im);maxw=int(im.width*.78);lines=[];cur=""
            for ch in text:
                t=cur+ch;box=d.textbbox((0,0),t,font=font)
                if box[2]-box[0]<=maxw:cur=t
                else:
                    if cur:lines.append(cur)
                    cur=ch
            if cur:lines.append(cur)
            y=int(im.height*.68);x=int(im.width*.07)
            for line in lines[:3]:
                d.text((x,y),line,font=font,fill="white",stroke_width=3,stroke_fill="black");y+=int(fs*1.35)
        out.parent.mkdir(parents=True,exist_ok=True);im.save(out,"PNG",optimize=True)
def make_zip(ep,plan,s,models):
    for f in plan["frames"]:
        n=f["number"]
        if not done(ep,s,n):raise SystemExit(f"{n:02d} not approved")
        render(fpaths(ep,n)["approved"],fpaths(ep,n)["publish"],str(f.get("caption","")).strip())
    rep={"schema_version":1,"story_os_version":"2.0","built_at":now(),"episode_id":plan.get("episode_id"),"title":plan.get("title"),"models":models,"note":"Unattended user-requested production; no fake human Story/Visual/Release approval.","frames":[]}
    for f in plan["frames"]:
        n=f["number"];rep["frames"].append({"number":n,"base_sha256":sha(fpaths(ep,n)["approved"]),"publish_sha256":sha(fpaths(ep,n)["publish"]),"attempts":s["frames"][f"{n:02d}"]["attempts"]})
    writej(ep/REPORT,rep)
    cap=ep/"production"/"auto"/"captions.json";writej(cap,{"frames":[{"number":f["number"],"caption":f.get("caption","")} for f in plan["frames"]]})
    pub=plan.get("publish") or {};copy=ep/"production"/"auto"/"publish_copy.md";copy.write_text(f"# {pub.get('title') or plan.get('title') or ''}\n\n{pub.get('intro','')}\n\n"+" ".join("#"+str(x).lstrip("#") for x in pub.get("topics") or [])+"\n",encoding="utf-8")
    eid=re.sub(r'[\\/:*?"<>|]+',"_",str(plan.get("episode_id") or ep.name));out=ep/"deliveries"/f"{eid}_V2_AUTO_FINAL.zip"
    sums=[]
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for f in plan["frames"]:
            p=fpaths(ep,f["number"])["publish"];arc=f"publish/{f['number']:02d}.png";z.write(p,arc);sums.append(sha(p)+"  "+arc)
        z.write(cap,"captions.json");z.write(copy,"publish_copy.md");z.write(ep/REPORT,"auto-production-report.json");z.writestr("checksums.sha256","\n".join(sums)+"\n")
    print("FINAL ZIP",out);print("SHA256",sha(out));return out
def cmd_plan(a):
    ep=epdir(a.episode);build_plan(ep,client(),a.force);return 0
def cmd_run(a):
    ep=epdir(a.episode);dirs(ep);c=client() if a.provider=="openai" or a.review=="vision" else None;plan=build_plan(ep,c,a.rebuild_plan);s=load_state(ep,plan)
    for n in order(plan):run_frame(ep,plan,s,plan["frames"][n-1],a.provider,c,a.quality,a.image_model,a.review,a.review_model)
    make_zip(ep,plan,s,{"provider":a.provider,"image":a.image_model,"planner":PLAN_MODEL,"review":a.review_model});return 0
def cmd_status(a):
    ep=epdir(a.episode);p=ep/STATE
    if not p.exists():print("NO AUTO STATE");return 1
    for k,v in sorted(readj(p)["frames"].items()):print(k,v["status"],v.get("approved_sha256") or "")
    return 0
def cmd_package(a):
    ep=epdir(a.episode);make_zip(ep,readj(ep/PLAN),readj(ep/STATE),{"provider":"package-only"});return 0
def cmd_self(a):
    deps()
    with tempfile.TemporaryDirectory() as td:
        ep=Path(td)/"ep";(ep/"meta").mkdir(parents=True);dirs(ep)
        p={"schema_version":2,"story_os_version":"2.0","episode_id":"SELFTEST","title":"自检","frame_count":4,"aspect_ratio":"4:5","capture_profile_id":"CP01","global_visual_lock":"test","calibration_frames":[1,2,3],"visual_admission_frames":[1,2,3,4],"publish":{"title":"自检","intro":"","topics":[]},"frames":[{"number":i,"beat":"test","prompt":f"真实手机随手拍自检{i}","caption":f"自检{i}","review_focus":[]} for i in range(1,5)]}
        validate_plan(p);writej(ep/PLAN,p);s=load_state(ep,p)
        for n in order(p):run_frame(ep,p,s,p["frames"][n-1],"mock",None,"medium","mock","local","mock")
        z=make_zip(ep,p,s,{"provider":"mock"})
        with zipfile.ZipFile(z) as zz:
            assert len([x for x in zz.namelist() if x.startswith("publish/")])==4
    print("AUTO PRODUCTION SELF-TEST PASS");return 0
def main():
    ap=argparse.ArgumentParser(description="Story OS V2.0 Auto Production Orchestrator");sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("plan");p.add_argument("episode",nargs="?");p.add_argument("--force",action="store_true");p.set_defaults(fn=cmd_plan)
    p=sub.add_parser("run");p.add_argument("episode",nargs="?");p.add_argument("--provider",choices=["openai","command","mock"],default="openai");p.add_argument("--quality",choices=["low","medium","high"],default="medium");p.add_argument("--image-model",default=IMAGE_MODEL);p.add_argument("--review",choices=["vision","local"],default="vision");p.add_argument("--review-model",default=REVIEW_MODEL);p.add_argument("--rebuild-plan",action="store_true");p.set_defaults(fn=cmd_run)
    p=sub.add_parser("status");p.add_argument("episode",nargs="?");p.set_defaults(fn=cmd_status)
    p=sub.add_parser("package");p.add_argument("episode",nargs="?");p.set_defaults(fn=cmd_package)
    p=sub.add_parser("self-test");p.set_defaults(fn=cmd_self)
    a=ap.parse_args();return a.fn(a)
if __name__=="__main__":raise SystemExit(main())
