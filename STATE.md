- H5 工程硬化：新增 `evaluation.py`（独立评估步骤），在 pipeline 末尾对输出做全面质量评估（证据充分性、概率自洽性、链间多样性、综合置信度），`AnalysisResult` 新增 `evaluation` 字段，新增 18 个测试（89 passed） - 完成于 19:50
- OSS 收尾：GitHub Actions CI（Python 3.10/3.11/3.12 + ruff + pytest + Node 20 + npm build） - 完成于 22:55
- OSS 收尾：API V2 响应新增 `evaluation` 字段（PipelineEvaluationV2），前端左侧面板新增 "Analysis Quality" 区域（置信度 + 薄弱点 + 建议） - 完成于 22:55
- OSS 收尾：roadmap 文档标记 P0/P1/P1.5/P1.6/P3/P4 已完成项 - 完成于 22:55

## Done recently (更新 2026-04-07)
- H3 工程硬化：llm.py 所有 5 个 LLM 调用已改为通过 `_call_with_retry` 走指数退避重试（最多 3 次，仅限 RateLimitError / APITimeoutError / APIConnectionError） - 完成于 19:30
- H4 工程硬化：LLMClient 新增 `timeout` 参数；`run_real_analysis()` 现在从 `RetroCauseConfig.from_env()` 读取 `request_timeout_seconds` 并传入 OpenAI 客户端 - 完成于 19:30
- `docs/engineering-audit.md` 已更新：H1-H4 全部标记为 Done - 完成于 19:30

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
- 已新增 `docs/oss-pro-positioning.md`，明确 OSS / Pro 边界、付费逻辑、用户痛点、场景价值、技术壁垒与差异化原则 - 完成于 23:58
- README / roadmap / DECISIONS 已同步更新，将“最小可公开 OSS 发布门槛”与“未来 Pro 价值”正式写入公开文档 - 完成于 23:59
- P0 发布前清单已推进：新增 `.env.example`、`LICENSE`、`.gitignore` 忽略 `.env`，修复 README / CONTRIBUTING / issue template 端口与 console 残留叙事，CLI 现在在无 key 时走 honest demo fallback、有 key 时走真实分析链路 - 完成于 00:08
- `docs/oss-pro-positioning.md` 已补入 evidence-grounded quality / workflow-specific outputs / trust-preserving behavior / reusable domain packs 的公开研究依据，作为后续 moat / Pro 路线参考 - 完成于 00:12
- Browser UI 已接入本地 API key / model 输入并向 `/api/analyze/v2` 发送 `query` / `model` / `api_key`，保持 evidence board 首页方向不变 - 完成于 21:31
- V1 API / V2 API / Streamlit 已统一 `is_demo` / `demo_topic` honesty；Streamlit 首屏与无 key 路径已改为 topic-aware demo 并显示持久 warning - 完成于 21:38
