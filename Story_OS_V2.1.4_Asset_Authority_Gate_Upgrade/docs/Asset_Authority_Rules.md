# Asset Authority Rules

生产前：

Episode Blueprint
        |
        v
Asset Authority Gate
        |
        +-- 当前 story 分支存在锁资产
        |        |
        |        PASS
        |
        +-- 不存在
                 |
                 STOP

禁止：

1. 搜索旧项目目录
2. 搜索其他 Git 仓库
3. 使用废弃资产
4. 自动迁移历史母版

如需迁移：

必须人工创建新的 Asset Lock。
