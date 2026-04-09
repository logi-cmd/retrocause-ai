## Done recently (更新 2026-04-10)
- Pipeline 性能优化：后端 LLM 调用从 85 次降到 ~19 次（批量证据提取 + 并行搜索 ThreadPoolExecutor + CausalRAG 条件触发 COVERAGE_THRESHOLD=0.5），成本省 ~50%，产品质量不牺牲 - 完成于 14:30
- SSE 实时进度流：新增 `POST /api/analyze/v2/stream` SSE 端点（text/event-stream），pipeline 每步触发 progress 事件，120s 全局超时兜底 - 完成于 14:30
- 前端 SSE 消费：`runAnalysis` 从 fetch POST 改为 ReadableStream SSE 消费，header 区域新增绿色进度条（stepIndex/totalSteps），错误 banner 红色高亮（左border + 红底色） - 完成于 15:00
- 验证全通过：ruff check 0 error / pytest 148 pass / npm build success / E2E 589/589 ALL PASS - 完成于 15:10

## Done recently (更新 2026-04-09)
- 端到端测试：新增 `scripts/e2e_test.py`（589 个检查项），覆盖后端连通性、V2 API 5 个 demo 全字段验证、V1 兼容、证据池完整性、上游图一致性、新能力 schema（uncertainty/citation/conflict）、边界用例（空查询/乱码/错误 key）、前端 HTML 投递、Playwright UI E2E（初始加载/demo 透明度/查询流/节点点击/语言切换/多节点交互/控制台健康）。589/589 ALL PASS, 0 FAIL, 0 SKIP - 完成于 16:30
- OSS 收尾：homepage 现已完整消费 live API 的 uncertainty / citation / conflict 数据，并补齐 evidence filtering（来源/立场/可信度）、链路比较摘要、右侧 edge insight / citation snippet 展示；README / roadmap 已同步更新当前 OSS 能力与测试数量（148） - 完成于 15:20
- Frontier 落地：CausalRAG / structured uncertainty / span-level citation grounding 已接入主 pipeline、API V2 与测试体系；新增 21 个测试，总测试数提升到 148，全量 pytest 通过 - 完成于 14:45
- 架构/文档同步：README、roadmap、OSS/Pro positioning、DECISIONS、私有 Rust 方案文档已统一补充 OSS 当前架构、frontier 技术落点、Pro-first 能力范围，以及 Rust 重写 / Python bridge 的改造边界 - 完成于 00:52
- 文档同步：README / `docs/oss-pro-positioning.md` / `docs-private/retrocause-pro-rust-architecture.md` 已统一写明 OSS/Pro 分层原则：OSS 继续沿用 Python + FastAPI + Next.js，Pro 规划为独立全栈 Rust 产品线 - 完成于 00:35
- 真实分析修复：修复 DuckDuckGo 适配器请求方式与 HTML 解析 bug，ArXiv 切换到 HTTPS，并降低在线模式默认调用规模；有效 OpenRouter key 下 `/api/analyze/v2` 已返回 `is_demo=False` 的真实结果 - 完成于 00:34

## Done recently (更新 2026-04-08)
- API smoke test：新增 `scripts/smoke_test.py`（38 个检查项），覆盖后端 root、V2 API 5 个 demo topic、V1 兼容、边变量完整性、前端 HTML。38/38 PASS - 完成于 02:50
- UI smoke test：新增 `scripts/ui_smoke_test.py`（Playwright/Chromium，21 个检查项），覆盖 Scenario 1-5（初始加载、demo 透明度、查询流、节点点击/多跳、语言切换）。21/21 PASS - 完成于 03:15
- Playwright Chromium 已安装（Chrome 因 Windows 权限不足未安装，Chromium 可正常使用） - 完成于 02:55
- 前端启动端口确认：需通过 `set PORT=3005` 环境变量指定（Next.js 默认 3000） - 完成于 03:00

## Done recently (更新 2026-04-07 晚)
- 全面测试：新增 38 个边界测试（`tests/test_comprehensive.py`），覆盖 demo topic 检测、API V2 schema 转换、Pydantic 序列化 round-trip、evaluation 分数边界、providers 配置完整性、pipeline 空运行/故障捕获、demo 结果完整性与一致性。总测试数 127，全绿 - 完成于 21:30
- 真实数据链路审查确认：ArXiv / Semantic Scholar / DuckDuckGo 三个数据源均为真实 HTTP 实现（非 stub），`run_real_analysis()` 完整接入 engine pipeline。无 API key 时优雅降级到 topic-aware demo - 完成于 21:45
- OSS/Pro 边界规划确认：单轮搜索→Pro 迭代、无 RAG→Pro 向量检索、LLM 依赖证据质量→Pro RAGAS/TruLens 评分、静默回退→Pro 拒绝静默回退 - 完成于 21:45
- OSS 剩余事项盘点：发布前仅差手动 smoke test（必须）和 README 截图/GIF（推荐），P2+ 功能均属后续迭代或 Pro 方向 - 完成于 21:50

## Done recently (更新 2026-04-07)
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
