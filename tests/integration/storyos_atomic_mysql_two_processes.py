"""Opt-in real MySQL two-OS-process Episode identity integration test.

Runs ONLY against the dedicated localhost:33417 test container, creates a
random schema and destroys it; never loads runtime.env or touches production.
"""
import os,sys,json,uuid,time,datetime,tempfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"episodes"/"_system"),str(ROOT)]
PORT=33417

def connection(schema=None):
 import pymysql
 if os.environ.get("STORYOS_ATOMIC_TEST_CONTAINER")!="storyos-test-only-mysql-authority":
  raise RuntimeError("TEST_ONLY_CONTAINER_NOT_ACKNOWLEDGED")
 if not os.environ.get("STORYOS_ATOMIC_TEST_PASSWORD"):
  raise RuntimeError("TEST_PASSWORD_REQUIRED")
 return pymysql.connect(host="127.0.0.1",port=PORT,user="root",
  password=os.environ["STORYOS_ATOMIC_TEST_PASSWORD"],database=schema,
  autocommit=True,charset="utf8mb4",connect_timeout=5)

def child(schema,base,title,action):
 import episode_state_persistence as state,story_creator
 from platform.repository.mysql.mysql_connection import MySqlConnection
 from platform.repository.mysql.mysql_episode_repository import MySqlEpisodeRepository
 from platform.repository.mysql.mysql_episode_state_repository import MySqlEpisodeStateRepository
 base=Path(base).resolve()
 db=MySqlConnection(host="127.0.0.1",port=PORT,user="root",
   password=os.environ["STORYOS_ATOMIC_TEST_PASSWORD"],database=schema)
 episodes=MySqlEpisodeRepository(db)
 states=MySqlEpisodeStateRepository(db)
 state.DATABASE_NAME=schema
 state._mode=lambda:"mysql"
 state._repositories=lambda:(db,episodes,states)
 state.episode_namespace=lambda ep:Path(ep).resolve().relative_to(base/"episodes").as_posix()
 def actual_bootstrap(root,title,visual_profile=None,*,_episode_override,_reserved_storage_id,**kw):
  if action=="crash":os._exit(37)
  ep=Path(_episode_override)
  ep.mkdir(parents=True,exist_ok=False)
  business,series=story_creator._canonical_identity_for_path(root,ep,title)
  at=datetime.datetime.now(datetime.timezone.utc).isoformat()
  state.save_initial(ep,{"episode_id":business,"series":series,"title":title,
    "storage_episode_id":_reserved_storage_id,"current_state":"IDEA_LOCKED",
    "updated_at":at,"history":[{"state":"IDEA_LOCKED","at":at,"note":"isolated test"}]},
    source="ISOLATED_TEST")
  return ep
 story_creator._create_episode_impl=actual_bootstrap
 if action=="concurrent":
  (base/("ready_"+title)).write_text("1",encoding="utf-8")
  deadline=time.monotonic()+25
  while not (base/"GO").exists() and time.monotonic()<deadline:time.sleep(.02)
  if not (base/"GO").exists():raise RuntimeError("BARRIER_TIMEOUT")
 ep=story_creator.create_episode(base,title)
 print(json.dumps({"id":story_creator._canonical_identity_for_path(base,ep,title)[0],
                   "name":ep.name,"exists":ep.is_dir()},ensure_ascii=False),flush=True)

def launch(schema,base,title,action):
 return subprocess.Popen([sys.executable,str(Path(__file__).resolve()),
   "--child",schema,str(base),title,action],cwd=ROOT,env=dict(os.environ),
   stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding="utf-8",errors="replace")

def result(proc,expected=0):
 out,err=proc.communicate(timeout=45)
 if proc.returncode!=expected:
  raise AssertionError("child exit %s, expected %s, stderr=%s"%(proc.returncode,expected,err[-2000:]))
 return json.loads(out.strip()) if expected==0 else {"exit":proc.returncode}

def main():
 from platform.repository.mysql.schema_v2 import DDL_STEPS
 import pymysql
 schema="STORYOS_ISO_EPCLAIM_"+uuid.uuid4().hex[:12].upper()
 assert schema.startswith("STORYOS_ISO_EPCLAIM_")
 db=connection()
 report={"schema":schema,"container":"storyos-test-only-mysql-authority",
   "isolated_sql_writes":True,"production_sql_writes":0,"model_calls":0}
 try:
  with db.cursor() as c:
   c.execute("CREATE DATABASE "+schema+" CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
   c.execute("USE "+schema)
   for name,sql in DDL_STEPS:
    if name in ("create_episode","create_episode_state","create_episode_state_his"):
     c.execute(sql)
   c.execute("INSERT INTO TB_EPISODE (EPISODE_ID,BUSINESS_EPISODE_ID,EPISODE_NAMESPACE,SERIES_ID,TITLE,DISPOSITION) VALUES (%s,%s,%s,%s,%s,%s)",
    ("EPU_TEST_OLD_05","00-05","00_独立篇/05_旧作品","00_独立篇","旧作品","ABANDONED"))
  with tempfile.TemporaryDirectory(prefix="storyos_atomic_mysql_") as dirname:
   base=Path(dirname);(base/"episodes"/"00_独立篇").mkdir(parents=True)
   a=launch(schema,base,"作品甲","concurrent")
   b=launch(schema,base,"作品乙","concurrent")
   deadline=time.monotonic()+35
   while time.monotonic()<deadline:
    if (base/"ready_作品甲").exists() and (base/"ready_作品乙").exists():break
    if a.poll() is not None or b.poll() is not None:
     raise RuntimeError("CHILD_FAILED_BEFORE_START")
    time.sleep(.04)
   else:raise RuntimeError("BARRIER_NOT_REACHED")
   (base/"GO").write_text("GO")
   pair=[result(a),result(b)]
   ids=sorted(x["id"] for x in pair)
   assert ids==["00-06","00-07"],pair
   report["two_independent_processes"]=ids
   result(launch(schema,base,"崩溃作品","crash"),expected=37)
   next_id=result(launch(schema,base,"下一部作品","normal"))["id"]
   assert next_id=="00-09",next_id
   report["abandoned_after_crash"]="00-08"
   report["next_after_crash"]=next_id
  with db.cursor() as c:
   c.execute("USE "+schema)
   c.execute("SELECT EPISODE_ID,BUSINESS_EPISODE_ID,DISPOSITION FROM TB_EPISODE ORDER BY BUSINESS_EPISODE_ID")
   rows=c.fetchall()
   expected=[("00-05","ABANDONED"),("00-06","ACTIVE"),("00-07","ACTIVE"),("00-08","ABANDONED"),("00-09","ACTIVE")]
   assert [(r[1],r[2]) for r in rows]==expected,rows
   c.execute("SELECT COUNT(*) FROM TB_EPISODE_STATE")
   assert c.fetchone()[0]==3
   report["database_rows"]=[{"id":r[1],"disposition":r[2]} for r in rows]
   report["state_rows"]=3
   try:
    c.execute("INSERT INTO TB_EPISODE (EPISODE_ID,BUSINESS_EPISODE_ID,EPISODE_NAMESPACE,SERIES_ID,TITLE,DISPOSITION) VALUES (%s,%s,%s,%s,%s,%s)",
       (rows[1][0],"00-06","00_独立篇/06_重复","00_独立篇","重复","ABANDONED"))
   except pymysql.err.IntegrityError as e:
    assert e.args[0]==1062
    report["lost_lock_primary_key_fence"]="PASS"
   else:raise AssertionError("PRIMARY_KEY_NOT_UNIQUE")
  report["result"]="PASS"
 finally:
  if schema.startswith("STORYOS_ISO_EPCLAIM_"):
   with db.cursor() as c:c.execute("DROP DATABASE IF EXISTS "+schema)
   report["temporary_database_deleted"]=True
  db.close()
 print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
 if len(sys.argv)>1 and sys.argv[1]=="--child":
  child(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])
 else:main()
