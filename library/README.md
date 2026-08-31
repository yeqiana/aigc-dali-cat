# Story OS Shared Resource Library

`library/` 是跨 Episode 的共享**参考资源库**，不是成片库。

默认可复用：
- 年代人物描述与衣着锚点
- 场景参考
- 道具年代参考
- Capture DNA
- 天气物理表现
- 简介开头模板
- 经审核后注册的参考图片

默认禁止：
- 把上一集最终成片直接作为新故事底图
- 把资源库内容当成 Story Lock
- 绕过 Recent-5 / Character / Environment / Frame Contract

真实图片资源可后续放进 `library/...` 并通过 `resource_library.py register` 写入 catalog。
