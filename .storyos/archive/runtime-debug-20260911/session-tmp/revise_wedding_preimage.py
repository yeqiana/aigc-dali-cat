from pathlib import Path
import json, re, shutil, hashlib, sys
from datetime import datetime
import yaml

ROOT=Path.cwd()
EP=ROOT/'episodes/09_旧物怪谈/05_婚礼前夜_记忆麻醉'
REV='20260909_reveal_order_v2'
ARCH=EP/'meta/preimage-revisions'/REV
assert not ARCH.exists(), 'revision already exists'
ARCH.mkdir(parents=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[p for p in EP.rglob('*') if p.is_file() and (p.suffix.lower() in {'.png','.jpg','.jpeg','.zip','.mp4'} or p.name in {'episode-state.json','release-manifest.json','production-ledger.json','production-queue.json','runtime-request.json','final-candidate-snapshot.json','story-gates.json'})]
before={str(p.relative_to(EP)):sha(p) for p in protected}
changed=[]
def write(rel,text):
    p=EP/rel
    if p.exists():
        b=ARCH/'before'/rel; b.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,b)
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding='utf-8'); changed.append(rel)
def jwrite(rel,obj): write(rel,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
for rel in ['meta/runtime/contracts','meta/runtime/prompt-packages']:
    if (EP/rel).exists(): shutil.copytree(EP/rel,ARCH/'before'/rel)

caps=[
'明天就要结婚了，我却想不起他求婚的样子。',
'他说这药能让我睡好。那晚忙乱，我漏吃了一次。',
'梦里，我一抬脚，床底就响了一声。',
'有人按住我的手，叫我别动。我看不清他的脸。',
'醒来，脚踝还红着。我把被角拉了下来。',
'婚礼彩排，他要我把恋爱六年背下来。',
'亲戚都喊我新娘子，没一个叫我名字。',
'镜子里的妈，我不认识。',
'婚鞋好沉。翻过来，鞋底焊着铁环。',
'金镯里头有一道合缝，尽头是个小锁孔。',
'我掀开窗上的红布，里面是一排封死的铁栏。',
'车厢里还有几个穿嫁衣的女孩，脚上都带着铁。',
'他又递来药：“吃完，明天就什么都不用想了。”',
'他一转身，我把含着的药吐进了花盆。',
'我举起还没扣上的金镯：“你是要拿这个锁我？”',
'他伸手抢镯子。我推倒凳子，撞开后门就跑。',
'我背得出恋爱六年的每一个细节，却想不起自己的名字。',
'窗外有人喊了个名字，我没想就回了头。',
'后来我又梦见自己试婚鞋。鞋底干干净净。',
'']
titles=['婚礼前夜','漏掉的一次药','床底的响声','看不清的人','醒后的红痕','背六年','没人叫名字','陌生的妈','翻转婚鞋','未扣上的金镯','红布后的铁栏','车厢里的人','再次递药','吐进花盆','举镯逼问','自己制造逃跑机会','获救却失名','身体先认出名字','另一个试鞋梦','醒后的天花板']
scenes=[
'P01站在婚房门口向内看，左手扶门框，男人侧后身铺红被，亲友整理搪瓷盆与红绸。土墙可见，窗上红布完整遮住结构。无药瓶、药片、铁栏或锁链。',
'P01坐在床边，左手正在收拾针线，桌角有普通水杯、纸巾和一粒未动的药。小白瓶放在桌角远侧，男人在背景搬被褥；没有递瓶、盯视或按住她。',
'梦境主观向下看自己的深色裤脚和旧布鞋：脚边一截短铁链被扯直伸入床底，链条两端都在画外。链与床脚接触处清晰，无法判断连着什么。无脚镣全貌、无药、无看守脸。',
'同一梦境，P01俯视碎花袖口，一只陌生成年人的手压住她的左手，木床沿可见；来者全身与脸均在画外，袖口也不露。没有瓶杯、嘴部、灌药或完整锁链。',
'现实醒来，P01坐在床沿低头，左手掀开一角被子，自己裸露脚踝上有一圈浅红压痕；同一深色裤脚，旧布鞋在床边。门口男人背影在忙，无药无铁环，不做梦中动作匹配。',
'P01从座位向前看，左手拿着纸，男人在桌对面侧身指向纸张，纸面只有失焦笔迹；婚房布置连续。不能从背后拍女主，也不出现她的脸。',
'P01坐在梳妆镜前，左右亲友整理发绳与喜被，交谈各做各事；镜子只带到女主碎花肩袖与发尾。她的姓名不在画面中，禁止生成人物对话文字。',
'从P01眼位看梳妆镜，陌生中年女人站在身后梳头，镜中可辨女人脸与梳子；P01自己的脸被镜面上缘裁出，仅见同一碎花肩袖、红绳黑发。',
'P01坐在床边左手翻转红绣鞋，使鞋底两道铁环朝向镜头；右手持机不入画，碎花袖、深色裤和自己的旧布鞋连续。铁环只在鞋上，不套在她脚上。',
'P01左掌托着一只尚未扣合的金色手镯，内侧合缝与小锁孔清晰，另一只放桌上；碎花袖口可见。不是已锁在手腕上的镯子，不展示开锁步骤。',
'P01左手掀起窗上的红布一角，布后露出横贯窗洞、固定在窗框内的铁栏，栏与窗框连接关系清晰；完整红布在其余区域仍遮挡。一次发现动作，无回头蒙太奇，不以土墙为新证据。',
'P01站在屋内门缝后向院里看，前景只有门框和一点碎花袖。男人在货车后门旁，车厢内几个成年女孩穿红嫁衣，脚踝铁环能看清；女主始终在屋里，不坐车厢，不穿红嫁衣。',
'P01站在屋内床侧，男人的手把一粒药与水杯递近，小白瓶在他另一手里；他侧身挡住前门方向。此时才把药与控制关系明确并置，不做仰头强灌。',
'P01从自己的眼位俯向床头旧花盆，左手扶盆沿，刚吐出的药落在湿土表面；背景男人侧后身转向前门。女主嘴脸不入画，不画手指把药丢进盆里。',
'P01左手举起那只未扣合金镯对着男人，镯口与锁孔可见；男人停下并伸手来抢，身后前门被挡住，左侧通后门的窄道和矮凳清楚。无女主正脸，无凭空解锁。',
'P01从后门门槛向田路冲出，画面下缘同一深色裤脚与旧布鞋沾泥，碎花袖左手推门，回侧余光见翻倒的矮凳挡在追来的男人脚前。无第三人称跑步全身，无换装、无突然赤脚、无救场女孩。',
'P01坐在检查站桌边，从自己眼位看记录人员和桌面，低处可见同一沾泥旧布鞋与深色裤脚，碎花袖左手停在桌沿。无白婚纱，无脚镣，无女主面部。',
'检查站同一座位，P01转向窗外，自己碎花左袖扶窗沿，花白头发女人被人搀着走来，神情急切；无女主脸，无白婚纱，不声称她已完整恢复记忆。',
'另一梦境，P01坐在明亮普通卧室的凳子上，第一人称俯视左手翻起红绣鞋鞋底，没有铁环。低位镜子仅反射同一坐姿的深色裤腿、碎花袖与红鞋，左右按镜面对应，脸和持机手在镜框外。',
'P01躺在床上主观仰视斑驳天花板，侧下缘一点碎花袖和红被；与先前婚房相同的墙角裂痕和红布窗边可辨。小白瓶在远侧床头桌边，无标签，静默；不新增锁链、不替观众断言获救全是假。']
knowledge=[
'只建立婚前记忆缺口，不能指向药物控制。',
'交代日常服药理由与漏服；药物作用尚未确认。',
'首次明确视觉异常是被扯直的铁链；来源、连接对象与梦的真假未知。',
'只确认梦里被阻止行动，不确认强灌或男人身份。',
'梦与现实有压痕呼应，也可能是睡姿；不替观众下结论。',
'关系叙述需要排练，恋爱记忆开始可疑。',
'亲密关系缺少真实称呼。','所谓母亲陌生，身份疑点累积。',
'第一次在清醒现实看见婚礼物件的束缚证据。','第二件物证互证，婚礼饰物具有锁的功能。',
'首次确认房间是囚禁空间；新增的是隐藏铁栏，不是土墙。','囚禁从自己扩展到车厢内多人。',
'男人主动递药并堵住出路，控制关系至此坐实；具体记忆机制仍不讲解。',
'主动拒绝下一剂，保持行动能力；不能倒写成此前发现的原因。',
'举证逼问引发男人抢夺，为下一张逃跑提供直接触发。',
'女主制造障碍并逃出；无巧合救援。','逃生获得外部确认，失名代价留下。',
'身体对名字有反应但记忆尚未恢复。','明确另一梦境，婚鞋物理状态反转。','旧房间细节返回，保留获救真实或仍被困的竞争解释。']
common='2007中国西北农村，CP03旧卡片机，4:5竖幅，现场光与自然杂物。P01第一人称；浅色碎花长袖、深色裤、旧布鞋，黑发红绳不变。禁止女主正脸、第三人称、白婚纱、电影灯、HDR、文字水印。'
board='# 《婚礼前夜·记忆麻醉》20张正式分镜｜揭露顺序修订 V2\n\n> 2026-09-09 用户授权修改前期依据；本轮禁止生图。新输入尚未完成独立评审和像素验收，旧发布版本不代表本修订通过。\n> 画幅4:5 / 1080×1350，无裁切标准化；M00 / CP03。\n> 四帧准入沿用角色分配01/11/03/15，旧准入证据须因源变更重新核验。\n\n## 连续性与揭露约束\n\n'+common+'\n\n- 01—18为同一婚前夜到凌晨，无换装。鞋在09只是拿起检查，未穿上；金镯10—15尚未扣合，因此能举起而无需开锁。16—18穿原布鞋沾泥，无凭空脚镣。\n- 03—04是未解释的梦境，19是明确第二梦境；梦也保留同一身体衣着。03铁链不能遮糊，但两端不见；04陌生手不能用袖口或脸提前匹配男人。\n- 药瓶01禁入；02首次作为日常桌角物件，瓶高不超过画高6%、面积不超过画面1%，不居中不高光；03—12禁入；13可清楚显示但瓶高不超过画高15%，动作主体是递药并挡路；14药落土中不摆瓶；15—19禁入；20瓶高不超过画高5%、面积不超过0.5%，作为回看细节。药统一未命名口服药片，不从瓶口灌液体。\n- 01—10窗上红布完整，不能提前露铁栏；土墙可以正常可见。11掀布才第一次看见封死的铁栏。\n- 第一人称涉及操作时左手操作、右手持机；03—04与19—20允许主观梦/醒视觉，不宣称熟睡时相机仍在拍。镜面只取身体局部，姿态、衣服、物件必须真实对应。\n\n'
for n in range(1,21):
    bottle=('按总约束保留小白瓶。' if n in [2,13,20] else '药瓶禁止入画。')
    board+=f'### {n:02d}｜{titles[n-1]}\n\n- 画面：{scenes[n-1]}\n- 字幕：{caps[n-1] or "无字幕。"}\n- 本帧允许知道：{knowledge[n-1]}\n- 逐帧硬约束：{bottle} P01仅手脚肩袖局部；同一碎花袖、深色裤。画面动作单一，证据不被字幕遮挡。\n- Scene Prompt：{scenes[n-1]}\n\n'
board+='## 节奏与回收\n\nS1=01—02日常与漏药；S2=03—04梦中异常；S3=05现实压痕；S4=06—08关系裂缝；S5=09—11主动验证与囚禁确认；S6=12—13多人受困与堵路；S7=14—18拒药、逼问、逃离、获救与名字反应；S8=19—20第二梦与静默重读。\n\n漏药02→梦03/04→压痕05；铁链03→鞋环09→锁孔10→铁栏11；背六年06→失名17；没人叫名07→回头18；鞋环09→无环鞋底19；桌角瓶02→递药13→吐药14→远侧瓶20。\n'
write('docs/03_婚礼前夜_20张正式分镜_V2.0.md',board)
sub=yaml.safe_load((EP/'meta/subtitles.yaml').read_text(encoding='utf-8'))
sub['frames']={n:caps[n-1] for n in range(1,21)}
write('meta/subtitles.yaml',yaml.safe_dump(sub,allow_unicode=True,sort_keys=False))
story='''# 《婚礼前夜·记忆麻醉》Story Lock｜揭露顺序修订 V2

> 2026-09-09：用户明确授权修改信息揭露、字幕分镜、画面合同与提示词；先不生图。
> 本文件为修订后的创作输入，旧批准仅证明旧SHA；尚未取得本版独立Story/Visual/Release PASS。
> 原版本已保存在meta/preimage-revisions/20260909_reveal_order_v2/before/。虚构创作，不指向真实案件。

## 一句话故事
婚礼前夜，我漏吃了一次被说成助眠的药，开始梦见床底铁链；醒来查验婚鞋、金镯和红布后的窗户，才发现婚礼正在把我变成被运走的人。我拒绝下一剂药，逼问并制造机会逃到检查站，却连名字都想不起来；另一个试婚鞋的梦之后，旧房间的细节又出现在眼前。

## 故事正文与S1—S8

### S1｜01—02
明天就要结婚，我却想不起他求婚的样子。婚房里的人忙着整理被褥。他说药能让我睡好，平时总会提醒我吃。那晚忙乱，桌上的药留着，我漏吃了一次。药只是日常细节，开场不把药瓶举到观众面前。

### S2｜03—04
睡着后，我梦见自己抬脚，床底响了一声。一截铁链扯直，两端都藏在视野外。有人按住我的手，叫我别动；我看不清脸，也看不见他拿什么。不给强灌画面，不用袖口把陌生手与现实男人提前配对。

### S3｜05
醒来时脚踝有圈浅红印。我把被角拉下来，没有告诉门口忙碌的男人。梦似乎留下了痕迹，却还不能证明什么；也不宣称药劲退尽或男人身份已经被认出。

### S4｜06—08
他把纸递来，让我排练婚礼上要讲的六年恋爱。亲戚一直叫我新娘子，没人叫名字。镜里替我梳头的妈，我根本不认识。我不敢直接问，开始自己查那些已经摆好的婚礼物件。

### S5｜09—11
婚鞋重得不对，我把鞋翻过来，底下焊着铁环。桌上的金镯还没扣上，内侧却有合缝与锁孔。我想到窗户，掀开一直盖着的红布，布后是封死窗洞的铁栏。此时才确定：这些物件和房间都在限制人的行动。土墙始终是普通环境，不能把发现土墙当作反转。

### S6｜12—13
我从屋内门缝看出去。院里的货车打开后门，里面还有几个穿红嫁衣的成年女孩，脚上带着铁。男人回来，递药和水，身体挡着前门：吃完，明天就什么都不用想了。直到这里，药、男人的控制和被运走的危险才清楚连接起来。

### S7｜14—18
我把药含住，趁他转身吐进床头花盆。此前的发现来自漏药后的疑点和主动检查；这次拒药是为了保持清醒行动，不能倒写成前面发现的原因。我举起尚未扣合的金镯问他，是不是要拿它锁我。他伸手抢，我推倒身边矮凳挡住他，撞开后门，穿原来的布鞋跑进田里。到省道检查站获救时，衣袖和鞋上都是泥。我能背出六年恋爱的细节，却说不出名字。窗外女人喊了一个名字，我没想就回了头，仍记不起她是谁。

### S8｜19—20
后来我又梦见自己在明亮的普通卧室试婚鞋。我坐着翻起红鞋，鞋底干干净净，没有铁环。低位镜子映出的还是我相同的坐姿、碎花袖和深色裤腿。再睁眼，斑驳天花板、红布窗边和远处桌角的小白瓶又回到眼前。最后不配字幕，不替观众确定获救是否真实。

## 人物、空间与因果合同

- P01：23岁普通女性，2007年中国西北农村婚前夜，第一人称。浅色碎花长袖、深色长裤、旧布鞋，齐肩黑发红绳；01—18没有穿婚纱或红嫁衣的换装事件。19梦境沿用这些锚点，20仍见碎花袖。
- 药物与排练干扰记忆是本作虚构机制，不给真实药名、剂量或医学解释；人物字幕只说自己的见闻。
- 主动链：漏服产生疑点→主动翻鞋/查镯/掀布→确认限制→看到多人被控制→含药吐出→举证逼问→对方抢夺→推凳逃走。
- 第一重大异常03保留铁链的直接视觉证据；09—10现实物证逐步确认，11首次确认房间囚禁功能，13确认眼前男人的控制行为。延迟答案，不延迟可见异常。
- 鞋09拿起但没穿；镯10—15未扣合。17不出现来源不明的脚镣。16逃跑保持原布鞋，泥污延续17—18。
- 任务闭环：逃出、检查站获救。身份代价：会背安排好的经历，仍想不起名字；18只恢复本能反应，不把认出名字等同完整记忆恢复。
- 双解释：获救是真实，20是创伤与残余梦境；或19才接近原本生活，所谓获救仍在被安排的层中。最终像素可矛盾，人物镜像物理不能出错。

## 修订边界与后续验收

婚礼、记忆干扰、失名和梦境结尾保留。既有选题历史与分数不重新编造。本版尚需独立故事评审、逐帧图文语义与连续性复核；修改源文件后旧SHA批准不能复用为本版批准。当前禁止生图、发布、Git提交或推送。
'''
write('docs/02_婚礼前夜_StoryLock_V2.0.md',story)
write('docs/04_婚礼前夜_视觉规范_V2.0.md','# 《婚礼前夜》视觉规范｜揭露顺序修订 V2\n\n'+board.split('## 连续性与揭露约束\n\n',1)[1].split('### 01',1)[0]+'\n01普通基线；03链条首异常；11红布后铁栏最差条件；15举镯对抗高冲击。旧四帧批准需重新核验。场景与逐帧禁止项见正式分镜；19必须镜内外同人同衣同姿势；20只给残留不解释。\n')
progress=json.loads((EP/'meta/shot-progression-review.json').read_text(encoding='utf-8'))
progress['status']='DRAFT'
progress['revision_note']='用户授权前期修订；旧评审失效待重审，本轮不生图。'
for f in progress['frames']:
    n=int(f['frame']); f['action']=scenes[n-1]; f['visual_function']=knowledge[n-1]; f['primary_subject']=titles[n-1]
    f['pov_mode']='P01主观眼位；仅手脚肩袖局部'
    f['anomaly_concealment']={'carrier':'direct_visible','purpose':knowledge[n-1],'physical_anchor':titles[n-1],'adds_information':n>1}
    f['continuity_exception_reason']='明确梦境，人物衣着与镜像物理仍连续' if n in [3,4,19] else ''
    f['camera_position']='P01坐姿俯视，低位镜面仅反射腿手' if n==19 else ('P01主观眼位，单手操作另一手持机')
jwrite('meta/shot-progression-review.json',progress)
for n in range(1,21):
    prompt=common+'\n'+scenes[n-1]+'\n'+knowledge[n-1]
    # Detailed reveal limits are in the compiled frame excerpt; compact scene below.
    short=scenes[n-1]+' '+('小白瓶仅桌角远侧，瓶高≤画高6%，面积≤1%。' if n==2 else '小白瓶仅远桌角，瓶高≤画高5%，面积≤0.5%。' if n==20 else '药瓶高≤画高15%。' if n==13 else '无药瓶。')+' CP03现场光，4:5，P01主观视角；碎花袖、深色裤，禁白婚纱、第三人称、文字水印、电影灯。'
    assert len(short)<=260 and len(short.encode())<=900, (n,len(short))
    write(f'docs/prompts/reveal-order-v2/{n:02d}.txt',short+'\n')

sys.path.insert(0,str(ROOT/'episodes/_system'))
import frame_contract, prompt_package
frame_contract.compile_all(EP)
for n in range(1,21): prompt_package.compile_frame(EP,n,EP/f'docs/prompts/reveal-order-v2/{n:02d}.txt')
errors=frame_contract.verify_all(EP)
assert not errors, errors
after={str(p.relative_to(EP)):sha(p) for p in protected}
assert before==after, 'protected asset changed'
jwrite('meta/preimage-revisions/'+REV+'/revision.json',{'schema_version':1,'revision_id':REV,'created_at':datetime.now().astimezone().isoformat(),'user_scope':'处理1-3，先不跑图','image_generation_allowed':False,'not_episode_stage':True,'new_inputs_review':'PENDING_INDEPENDENT_REVIEW','old_evidence_policy':'Historical source-SHA approvals remain unchanged and must not certify revised inputs. All 20 contracts drift after Story SHA change; re-review does not imply regenerating all images.','old_queue_policy':'Historical generated queue and prompt files remain unchanged. Do not resume old queue as revised production. Build new queue against docs/prompts/reveal-order-v2 only after user authorizes images and current gates pass.','modified_source_files':changed.copy(),'preserved_files_sha256':before,'frame_contract_verification_errors':errors,'recompiled_frames':list(range(1,21))})
print(json.dumps({'changed_sources':changed,'compiled_contracts':20,'compiled_packages':20,'protected_files_unchanged':len(before),'errors':errors},ensure_ascii=False))
