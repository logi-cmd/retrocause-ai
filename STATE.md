## Done recently (更新 2026-04-04)
- 证据墙首页已支持真实因果红线、图钉锚点、便签拖动、纸张/墙面真实感增强 - 完成于 22:41
- OSS 文档中的前端访问端口已统一更新为 3005 - 完成于 22:42
- 首页进一步完成数据驱动统计、相关节点/红线高亮、入场与绘线动画 - 完成于 22:49
- 中间区域核心组件（ChainView / DebateTreeView / DataTableView / EvidenceList / QueryInput / NodeDetail / ProbabilityBar）已完成新一轮 zh/en 适配，layout metadata 已修复 - 完成于 23:03
- 剩余小组件 i18n 已继续补齐，首页 mock demo 已支持最小双语数据切换（zh/en） - 完成于 23:15
- 首页已接入 `/api/analyze/v2` 的最小 happy path，并在 UI 中区分 real analysis 与 demo fallback - 完成于 23:28
- 首页 `page.tsx` 已修复 API v2 类型映射与顶层语句问题，`frontend npm run build` 恢复通过 - 完成于 23:35
- 首页已补齐链切换联动：切链重算便签布局、重置选中节点与画布偏移，并新增推荐链标识 - 完成于 23:42
- 右侧证据面板已改为优先跟随选中节点/当前链过滤，并补充证据强弱、低置信度、低覆盖、高不确定性提示 - 完成于 23:45
