# Story OS V2.1｜Character Visual + Scene-Aware Wardrobe V1.0

> 本规范不新增 Episode Stage。

## Camera-Friendly Ordinary Cast
核心人物默认是二十来岁的真实普通年轻人，但略高于普通路人的上镜程度。
核心女主默认可采用 `slim_proportionate_natural`：苗条、匀称、真实自然；核心男主可采用 `lean_proportionate_natural`。
禁止网红脸、明星脸、时尚模特造型、瓷器皮肤、重磨皮和 AI 标准脸。

## Anti-Likeness
真人参考图只能参考年龄感、气质、颜值区间、真人感、摄影方式、服装方向和色彩氛围。
禁止复制精确脸型、眼鼻嘴组合、标志性个人特征、精确发型和明星/网红身份特征。
目标是同一审美区间的原创角色，不是真人换衣复刻。

## Hair Lock
候选阶段可尝试短碎发、稍长刘海、眼镜/无眼镜、马尾、低马尾、披肩发、松散扎发。
Character Visual Contract LOCK 后，脸型身份、haircut、hair length 锁定；只允许湿发、风吹乱、戴帽、扎起/放下等有剧情理由的状态变化。

## Scene-Aware Wardrobe
服装优先顺序：
`地点/海拔 → 温度 → 天气 → 时段 → 活动 → 人物气质 → 画面审美`

### 川藏线 / 高海拔公路旅行
高海拔、阴雨、强风、早晚、寒冷：优先冲锋衣/硬壳/软壳、抓绒/羽绒/保暖中层、厚长裤/徒步裤、漂亮但真实的保暖帽、耐脏或防水鞋。

低海拔、晴热、车内、民宿、县城停留：女主可切换漂亮但日常的吊带、半身裙/连衣裙、薄外搭、休闲鞋。

高海拔景区短暂停车打卡：可以兼顾上镜和保暖。裙装只有在厚裤袜/加绒裤袜 + 保暖外层成立时允许；强风、雨雪、长时间户外优先长裤。

### 冷天气裙装
`裙子 + 裸腿` 在 cold / very_cold 户外直接 FAIL。
允许：裙子 + 厚裤袜/加绒裤袜 + 冲锋衣/呢外套/羽绒等真实保暖外层。

### 吊带
吊带适合夏季、低海拔暖区、车内、民宿、室内或有可随时穿上的外层。
高海拔冷风中只穿吊带直接 FAIL。

### Outfit Change
换装必须有真实原因：海拔/温度/天气变化、车内↔户外、昼夜切换、到民宿、第二天、景区短时打卡、衣服湿透/弄脏。
任何 `look_id` 变化都要记录 `change_reason`。

## Visual Lock
多人旅行故事的 ordinary_baseline 由机器优先读取 `meta/opening-social-anchor.json` 中合法的图 01/02 自拍关系锚点；不存在合法锚点时才回退旧的普通低异常选帧逻辑。

Story/Preimage 阶段只允许锁 `identity_spec_locked=true`，不得伪造图片母版。FOUR-admission Visual Lock 全部 PASS 后，ordinary_baseline 才生成独立的 `meta/character-pixel-master.json`，记录真实图片路径、图片 SHA、Frame Contract SHA 与 Character Visual Spec SHA。Production 优先把该像素母版作为 identity reference。

真人参考始终只能承担 Style Reference，不能成为 Identity Master。
