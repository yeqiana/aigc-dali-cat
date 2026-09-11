# Story OS Asset Boundary

资产隔离入口：

- `assets/placeholders/`：测试占位资产，不属于生产，不消耗图片生产额度。
- `assets/fixtures/`：自动化测试夹具。
- `assets/demo/`：演示素材。

禁止将此目录内容复制到：

- `episodes/**/media/raw`
- `episodes/**/media/candidates`
- `episodes/**/media/approved`
- `episodes/**/media/publish`

生产资产仍遵循：

`Generation → Candidate → Approved → Snapshot → Release`
