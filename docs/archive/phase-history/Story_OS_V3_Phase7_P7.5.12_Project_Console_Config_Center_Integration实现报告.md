# Story OS V3 Phase7 P7.5.12 Project Console + Config Center Integration

状态：完成

## 目标
将 Phase6 Project Service 与 Config Center 能力接入 Web Console。

## 新增

- web-console/src/types/project.ts
- web-console/src/api/project.ts
- web-console/src/pages/ProjectConsole.tsx

## 架构

User
↓
Project Console
↓
Project API Adapter
↓
Project Service
↓
Config Center

## 当前能力

- 项目列表入口
- 项目配置读取入口
- 多租户项目隔离基础

## 后续

补充项目详情、配置编辑、插件管理。
