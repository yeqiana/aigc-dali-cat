# Story OS 配置目录

- `storyos.yaml`：唯一人工可编辑的当前生产配置；所有流程先读取并校验。
- `index.yaml`：仓库和阶段最小读取集索引，避免递归扫描。
- `profiles/`：可复用的机器 Profile；JSON 仅作为结构化机器合同，不作为人工总入口。

校验：

```bash
python episodes/_system/story_os.py config validate
```

查看当前生效配置：

```bash
python episodes/_system/story_os.py config show
```

Episode 的 `meta/*.json` 是状态、证据和派生缓存，不能搬进本目录，也不能反向覆盖配置或创作权威。

