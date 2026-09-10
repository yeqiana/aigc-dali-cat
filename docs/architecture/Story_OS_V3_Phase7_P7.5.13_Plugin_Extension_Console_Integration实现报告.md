# Story OS V3 Phase7-P7.5.13 Plugin / Extension Console Integration

状态：完成

目标：将 Phase 6 Plugin Extension 能力接入 Web Console。

## 新增

web-console/src/types/plugin.ts

定义 PluginDefinition 与 ExtensionPoint。

web-console/src/api/plugin.ts

提供 Plugin Registry 与 Extension API Adapter。

web-console/src/pages/PluginConsole.tsx

提供插件管理入口。

## 架构

Tenant
 ↓
Project
 ↓
Plugin Registry
 ↓
Extension Point
 ↓
Skill / MCP / Agent Runtime

## 后续

接入真实 Plugin Service、MCP Registry、Skill Registry。
