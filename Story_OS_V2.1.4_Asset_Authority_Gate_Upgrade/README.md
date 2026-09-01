# Story OS V2.1.4 Asset Authority Gate Upgrade

目的：
防止 Story OS 在当前 story 分支缺少锁资产时，
自动搜索外部仓库、旧项目、废弃资产。

核心规则：

Current Story Branch Assets
        |
        PASS -> 继续生产
        |
        FAIL
        |
        STOP ASSET_LOCK_MISSING

禁止：
- 自动扫描工作区
- 自动引用旧仓库
- 自动使用废弃资产
- 跨项目 fallback

安装：

python -X utf8 install.py --repo <story仓库路径>
