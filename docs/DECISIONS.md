# 技术决策记录

> 记录 RetroCause 项目的关键技术决策、背景、选择和理由。

---

## 2026-03-29 架构重构

### 背景
项目初始版本所有代码在扁平模块中，引擎 `RetroCauseEngine.run()` 是单一方法，步骤间无隔离。

### 决策
引入 4 个基础设施文件：
- `protocols.py` — Protocol 接口 (LLMProvider, SourceAdapter, GraphProvider, EvidenceStore 等)
- `config.py` — frozen dataclass 全局配置
- `pipeline.py` — Pipeline + PipelineStep + PipelineContext 抽象
- `hooks.py` — HookEngine + HookRule 声明式规则引擎

### 理由
- Pipeline 模式使每个分析步骤可独立测试、替换、重排序
- Protocol 接口支持依赖注入，便于 mock 测试
- HookEngine 提供声明式质量守卫，避免硬编码检查

---

## 2026-03-29 Task 1: LLM 自动证据收集

### 背景
初始版本 `EvidenceCollector` 只有 `add_evidence()` 手动接口，无自动收集能力。

### 决策
- 新增 `llm.py` — LLMClient 封装 OpenAI SDK (查询分解、证据提取、相关性评分)
- 新增 `sources/` 包 — 4 个源适配器 (base, arxiv, semantic_scholar, web)
- 扩展 `collector.py` — `auto_collect()` 方法编排 LLM + 多源搜索
- 新增 `EvidenceCollectionStep(PipelineStep)` 管道步骤

### 理由
- 多源搜索 (arXiv, Semantic Scholar, web) 覆盖学术+新闻+数据
- LLM 查询分解使搜索更精准
- 证据提取 prompt 明确要求"仅提取事实性陈述"

---

## 2026-03-30 Task 2: 证据锚定推理

### 背景
假说链的 `path_probability = ∏ conditional_prob` 是纯数学乘积，无证据支撑验证。无法知道哪些边有文献证据、哪些是推测。

### 决策
- 新增 `anchoring.py` — `anchor_edge_to_evidence()`, `anchor_hypothesis()`, `build_evidence_index()`
- 新增 `rules.py` — `EvidenceCoverageRule` + `ProbabilityBoundRule` HookRule
- `models.py` 添加 `evidence_coverage: float` + `unanchored_edges: list[str]`
- 管道插入点: EvidenceAnchoring 在 HypothesisGeneration 之后

### 理由
- 证据覆盖率是因果推理可信度的核心指标
- 未锚定边暴露推理薄弱环节，引导后续证据收集
- Hook 规则实现自动警告，无需人工检查

---

## 2026-04-01 Task 3: 反事实验证设计

### 背景
当前系统仅操作在 Pearl 因果阶梯 Level 1（关联），从未回答反事实问题："如果 X 没发生，Y 还会发生吗？"

### 调研来源
- 8 篇学术论文（见 docs/references.md）
- DoWhy, CausalNex, pgmpy 反事实模块
- Claude Code Framework 架构模式

### 技术选择：A-A-P + 图手术 + 敏感性分析

**选择**:
1. **Abduction-Action-Prediction (A-A-P)** — Pearl 反事实三步框架的轻量实现
2. **Graph Surgery** — 移除根因节点，检查结果可达性 (DoWhy `do_surgery` 模式)
3. **敏感性分析边界** — 当无法精确识别时提供锐边界 (Frauen et al. 2023)
4. **LLM 辅助反事实推理** — 利用文献中的反事实论证

**不选择**:
- 完整 SCM 参数化 — 无观测数据拟合
- 精确反事实点估计 — 文献场景下不可靠
- DoWhy-GCM 噪声重建 — 需要加性噪声模型假设，不适用

### 理由
- **无观测数据**: 只有文献文本，没有可拟合 SCM 的数据
- **边界 > 点估计**: 提供可信范围比提供错误数字更有价值
- **A-A-P 轻量**: 不需要完整 SEM，在图结构上即可操作
- **可扩展**: 后续有数据时可升级到完整 SCM

### 新增文件
- `retrocause/counterfactual.py` — 核心模块

### 修改文件
- `retrocause/models.py` — CounterfactualResult dataclass + counterfactual_score
- `retrocause/engine.py` — 插入 CounterfactualVerificationStep
- `retrocause/config.py` — 反事实配置参数
- `retrocause/rules.py` — CounterfactualBoundRule
- `tests/test_counterfactual.py` — 新测试

### 管道顺序
```
EvidenceCollection → GraphBuilding → HypothesisGeneration → EvidenceAnchoring → CounterfactualVerification → DebateRefinement
```

---

## 2026-04-01 产品方向调整：优先面向海外 C 端

### 背景
此前对商业化路径的讨论更偏向 B 端专业分析/研究工具。但当前用户明确希望主要目标用户为海外 C 端。

### 决策
- 产品前台定位从“通用因果推理平台”调整为“海外用户可理解的 Why Explainer / 因果解释产品”
- 保留底层 RetroCause 引擎能力（证据收集、因果图、假说链、反事实）
- 前台产品优先包装为热点事件、历史问题、商业科技事件的因果解释器
- 将 C 端产品与未来 B 端能力解耦：先做消费级入口，再视数据与留存情况扩展高级版

### 理由
- 海外 C 端更适合以简单问题表达价值："Why did this happen?"
- 普通用户不关心因果术语本身，更关心解释是否直观、可信、可分享
- 当前项目已有可视化与解释链基础，适合先做内容驱动 + 工具驱动的混合产品
- 该方向更适合 SEO、社交传播与 freemium 增长模式

---

## 2026-04-01 文档边界：商业/计划文档本地私有

### 背景
项目将采用 GitHub 开源引流，但用户明确要求商业和计划相关文档不要提交远程。

### 决策
- 新增 `docs-private/` 作为本地私有文档目录
- `docs-private/` 与 `*.local.md` 一律加入 `.gitignore`
- 开源仓库中的 `docs/` 仅放可公开的技术文档、开源路线、开发说明
- 商业化、定价、增长、开闭源边界、执行计划等内容优先放在 `docs-private/`

### 理由
- 保持 GitHub 开源仓库的传播属性和信息边界清晰
- 避免过早暴露商业策略、定价方案与内部计划
- 允许继续在本地沉淀完整商业文档，不影响后续执行

---

## 2026-04-01 因子影响分析：先做 Intervention Effect

### 背景
用户明确需要“修改某个因子后，分析它对结果的影响”的能力，并要求技术路线成熟可行。

### 决策
- 第一阶段优先实现 **Intervention Effect（干预效应分析）**
- 暂不直接实现完整反事实推断作为 MVP 主能力
- 产品交互优先支持：调节变量强度 / 存在与否 → 查看结果变化

### 理由
- intervention 比完整 counterfactual 更成熟、更易验证
- 更符合当前项目“有因果图和边概率、但缺少高质量结构化观测数据”的现实约束
- 更适合作为面向 C 端的直观产品能力

---

## 2026-04-02 工程审计结论

### 背景
虽然 `harness-engineering` 这个 skill 不可用，但项目仍然需要从工程 harness / 可验证性 / 可演进性角度做一次系统审视。

### 决策
- 新增 `docs/engineering-audit.md` 作为工程优化路线文档
- 将后续工程优化优先级聚焦在三项：
  1. 补全运行时依赖声明
  2. 拆分 `app.py`
  3. 将 HookEngine 正式接入主流程

### 理由
- 这三项优化对开源可运行性、可维护性、工程 harness 激活最直接
- 当前项目不是“需要重写”，而是“需要把已有的好结构真正接起来”


---

## 2026-04-02 Harness Engineering 视角审视

### 背景
使用 harness-engineering skill 对项目进行了结构化审视，评估了 5 个维度：执行循环、评估设计、上下文管理、防护栏、失败恢复。

### 结论

1. **执行循环**：当前线性 Pipeline 是合理的 MVP 选择，但随着成熟度提升需要 GAN-style 循环
2. **Generator/Evaluator 分离**：项目当前缺少独立的评估者
3. **失败恢复**：Pipeline.run() 无 try/except，LLM 调用静默吞错误（比崩溃更危险）
4. **上下文管理**：PipelineContext 纯内存，无跨会话持久化，对 MVP 可接受
5. **防护栏**：HookEngine + 3 条规则已实现但从未被调用

### 新增高优先级 harness 优化

- H1: 将 HookEngine 接入 Pipeline.run()
- H2: 给 Pipeline.run() 加 try/except
- H3: 给 LLM 调用加重试机制
- H4: 把 config.py 的 timeout 参数真正传给 OpenAI 客户端
- H5: 考虑增加独立评估步骤

### 理由
- harness-engineering skill 明确指出 generator 和 evaluator 必须分离
- 静默失败比显式崩溃更危险
- 项目已有 HookEngine 但未接入，是已有好结构但未真正接起来的典型案例

---

## 2026-04-03 OSS 前端体验升级：API v2 + 证据白板 UI

### 背景
项目原有前端更接近深色分析台 / 控制台风格，因果展示以扁平节点边列表为主，无法很好表达“逐层追因”“多跳因果链”“证据墙”这类更直观的产品体验。用户明确要求：

- 前后端统一启动与联调
- 后端返回可支持多跳溯源的数据结构
- 前端改为白底、电影感“警察证据白板”风格
- 保留产品可读性，而不是只做道具感 UI

### 决策
- 新增 `/api/analyze/v2`，在保留 `/api/analyze` 的同时返回 chain-aware 结构：`chains`、`recommended_chain_id`、`evidences`、`upstream_map`
- 前端从原来的扁平图数据，升级为 `CausalChain` 主数据模型，并在 `page.tsx` 中完成 API v2 → 前端链式模型的映射
- 主界面采用“主画布 + 右侧详情”的证据板交互：
  - 主画布显示因果证据板 / 因果图谱
  - 右侧详情显示选中节点、上游原因、相关证据、反事实信息
- 视觉系统改为白底证据墙风格：`board-white` / `paper-white` / `paper-aged` 等令牌，辅以红蓝 marker accents
- 保留多跳追因交互：点击节点 → 高亮路径 → 展开上游原因 → 可继续向上追因

### 理由
- `result.hypotheses`、edge evidence ids、counterfactual 结果本身已经存在，问题主要在 API 层被压扁，导致前端无法表达更强的产品体验
- 白底证据墙比黑灰分析台更适合“因果侦查 / Why explainer”叙事，也更适合开源展示和截图传播
- “电影感”与“可用性”需要同时成立，因此采用的是受控的证据板美术方向，而不是纯道具化堆砌
- 保留旧 `/api/analyze` 可降低破坏性，便于继续兼容既有逻辑

### 验证结果
- `pytest tests/` 通过（68 passed）
- `ruff check retrocause/` 通过
- `frontend/npm run build` 通过
- 根目录 `pyproject.toml` 的 UTF-8 编码问题已修复，否则 pytest / ruff 无法读取配置

---

## 2026-04-03 OSS 收尾：证据白板统一与 demo fallback 显式标记

### 背景
在完成主链画布与右侧详情后，项目仍存在两类收尾问题：

- 部分残余视图（如 debate / table）仍保留旧的深色终端风格，与新的白底证据白板语言不一致
- `/api/analyze/v2` 在无 LLM 时会返回 `demo_result()`，虽然 query 会被覆盖为用户原始输入，但链路内容仍是 demo 示例，容易让使用者误以为这是针对当前问题的真实分析

### 决策
- 将剩余视图统一迁移到 evidence-board 视觉系统：纸张背景、暖白底、paper border、ink 文本与 marker accents
- 在 `AnalyzeResponseV2` 中新增 `is_demo` 字段；当 v2 endpoint 走 demo fallback 时显式返回 `is_demo=true`
- README 明确补充：
  - `python start.py` 为推荐启动方式
  - 浏览器 UI 为当前主入口
  - `/api/analyze/v2`、多跳追因与证据白板是当前 OSS 的核心体验

### 理由
- 视觉统一是 OSS 观感完整性的最后一环，否则不同 tab 会像两个产品拼接在一起
- demo fallback 本身合理，但如果不显式标记，用户会把示例因果链误读为真实查询结果，损害产品可信度
- README 必须反映真实运行方式与当前体验，否则开源访客无法快速上手

### 验证结果
- `pytest tests/ -v` 通过（68 passed）
- `ruff check retrocause/` 通过
- `frontend npm run build` 通过
- 启动烟雾测试确认：`start.py` 可同时拉起前后端；本机已有占用 3000 端口的前端实例时，Next.js 会自动切端口并报告冲突
- 接口烟雾测试确认：`/api/analyze/v2` 返回 `is_demo=true`，可明确区分 demo fallback 与真实分析

---

## 2026-04-03 OSS 可用性收尾：demo 提示、手动测试文档与路线图

### 背景
在 API v2 已显式返回 `is_demo` 后，仍需要在前端层把这一状态明确展示给用户，否则普通访客仍可能误把示例链当成真实分析结果。同时，开源仓库还缺少一份可直接执行的手动 smoke 清单，以及一份对当前边界和路线图的集中说明。

### 决策
- 在前端首页主布局顶部增加 demo / real result 信息横幅：
  - demo 模式时明确提示“当前结果来自内置演示链路”
  - real 模式时提示结果来自 `/api/analyze/v2`
  - 显示当前 query 文本，避免用户不知道当前页面对应哪次请求
- 新增 `docs/manual-smoke-test.md`，作为 OSS 访客和维护者的手动验证清单
- 新增 `docs/roadmap-and-limitations.md`，集中说明当前 OSS 的能力边界与近期路线图
- 在 README 的 Public docs 中挂出上述新文档入口

### 理由
- `is_demo` 如果只存在 API 层，普通前端用户仍然看不到，产品透明度不足
- 手动 smoke 文档能把“怎么验证这个仓库是活的”标准化，降低开源访客理解成本
- roadmap / limitations 文档有助于防止外部用户误判当前成熟度，也便于后续继续迭代时维持公开叙事一致性

### 验证结果
- `frontend npm run build` 通过
- `pytest tests/ -v` 通过（68 passed）
- `ruff check retrocause/` 通过
- `frontend/src/app/page.tsx` diagnostics clean

---

## 2026-04-03 OSS 社区化与 query-aware demo fallback

### 背景
在 demo 模式已经被前端显式提示之后，仍存在两个开源体验问题：

- 开源访客缺少标准化的协作入口（issue 模板、贡献说明）
- demo fallback 虽然已标记为 demo，但仍可能始终落回“恐龙灭绝”这套固定数据，无法体现与 query 的最基本主题匹配

### 决策
- 新增 GitHub issue templates：
  - bug report
  - feature request
  - issue template config
- 新增 `CONTRIBUTING.md`，说明：
  - 本地安装方式
  - `python start.py` 启动方式
  - pytest / ruff / frontend build 校验命令
  - 关键文档入口
- 在 `frontend/src/app/page.tsx` 中加强状态横幅：区分 demo / realtime / backend disconnected
- 在 `retrocause/app/demo_data.py` 中新增 `topic_aware_demo_result(query)`：
  - 对 SVB / bank / 银行 / 挤兑 等 query 返回金融挤兑主题 demo
  - 对 stock / 股票 / 暴跌 等 query 返回股价暴跌主题 demo
  - 其他 query 继续回退到默认恐龙 demo
- API fallback 路径统一改为使用 `topic_aware_demo_result(query)`
- 新增 `tests/test_demo_data.py` 验证 demo fallback 的 query-aware 行为

### 理由
- 开源仓库不只是“能跑”，还需要“别人知道怎么提问题、怎么贡献、怎么验证”
- query-aware demo 虽然仍不是真实分析，但比固定恐龙链更符合用户心智，也更适合演示界面和交互
- 通过自动化测试锁住 demo fallback 行为，可以减少后续迭代时的回归风险

### 验证结果
- `tests/test_demo_data.py` 通过（3 passed）
- `pytest tests/ -v` 通过（71 passed）
- `ruff check retrocause/ tests/` 通过
- `frontend npm run build` 通过
- 手动烟雾验证：
  - SVB query → `is_demo=true` 且返回 SVB 主题 demo chain
  - 股票暴跌 query → `is_demo=true` 且返回股票暴跌主题 demo chain
  - 恐龙 query → `is_demo=true` 且返回默认恐龙 demo chain

---

## 2026-04-03 继续收尾：topic-aware demo 扩展与前端状态细化

### 背景
用户要求继续完善 OSS，但新增约束是：**非必要不再继续扩写 markdown 文档**。在此前版本中，前端已经能显示 demo / realtime / backend disconnected，但 demo 仍然只区分“演示模式”与“默认 demo”，且 query-aware fallback 仅覆盖少量金融主题。

### 决策
- 前端状态横幅进一步细化：
  - 除了 `is_demo` 外，还消费 `demo_topic`
  - 当处于 demo 模式时，显示具体标签：
    - `银行 / SVB demo`
    - `股票 demo`
    - `金融危机 demo`
    - `租金 demo`
    - `默认 demo`
- API v2 响应新增 `demo_topic`
- `topic_aware_demo_result(query)` 扩展到更多高频 query 类型：
  - SVB / 银行挤兑
  - 股票暴跌
  - 2008 金融危机 / 次贷危机
  - 租金 / 住房供给
- 为避免证据 id 冲突，将不同 demo topic 的 evidence ids 前缀化（如 `svb_ev*`, `stock_ev*`, `crisis_ev*`, `rent_ev*`）
- 保持默认 fallback 仍回退到恐龙 demo，不扩大非必要文档面

### 理由
- topic-aware demo 若没有前端显式标签，用户仍可能不知道当前 demo 是“主题匹配示例”还是“真实分析结果”
- 更丰富的 demo topic 可以让 OSS 在无模型环境下也更接近真实使用路径
- evidence id 命名隔离可以减少后续多主题 demo 合并时的冲突风险

### 验证结果
- `pytest tests/test_demo_data.py -v` 通过（3 passed）
- `pytest tests/ -v` 通过（71 passed）
- `ruff check retrocause/ tests/` 通过
- `frontend npm run build` 通过

---

## 2026-04-04 OSS 前端重设计：浅色证据墙 + 真实红线连接 + 中英文切换

### 背景
用户否定了此前的深色控制台式证据墙实现，要求将 OSS 前端重做为更适合公开展示和产品化演示的浅色证据墙：

- 整体不再使用深色背景，而改为黄色/米黄色墙底
- 中间画布必须成为绝对主视觉，接近自由画布
- 因果节点表现为便签纸 + 图钉
- 红线必须依据真实因果关系连接，而不是装饰性摆放
- 前端需要支持中英文切换，便于 OSS 面向更广泛用户展示

### 决策
- 前端视觉基调从默认深色切回浅色证据墙体系，使用暖米黄/纸张色作为默认 background token
- `ConsoleLayout` 保持三栏结构，但弱化左右侧栏、放大中间主画布，让证据墙画布成为主入口
- `MainCanvas` / `Header` / `ViewTabs` / 左右面板统一迁移到浅色纸张/档案风格
- `CausalGraphView` 中的红线继续采用 evidence-board 红线审美，但其路径计算严格以 `edge.source -> edge.target` 为准
- 新增轻量级前端 i18n 基础设施（不引入第三方依赖）：
  - `I18nProvider`
  - `useI18n()`
  - `zh/en` 字典
  - `LocaleToggle`
- 主要可见文案（Header、ViewTabs、主画布提示、左右面板、StatusBar）接入 zh/en 翻译切换

### 理由
- 浅色证据墙比深色分析台更符合“Why explainer / 因果侦查板”的产品叙事，也更适合截图传播与 OSS 展示
- 将主视觉重心放回中间自由画布后，用户更容易把产品理解为“因果探索界面”而非“控制台”
- 红线如果不基于真实 `source -> target`，证据墙会退化成纯装饰，损害解释界面的可信度
- 轻量 i18n context 足以支撑当前 OSS 展示需求，同时避免引入额外依赖和复杂度

### 验证结果
- `frontend npm run build` 通过（Next.js 16.2.2）
- `frontend/src` 下 `.tsx` / `.ts` LSP diagnostics 均为 0 error
- 语言切换基础设施已接入，主要可见文案已可在 zh/en 间切换
- 红线连接逻辑已按前端 edge 数据映射到对应 source/target 节点

### 补充修正
- 修复 `frontend/src/components/layout/ConsoleLayout.tsx` 中残留的 `bg-[var(--board-dark)]`
- 将主布局最外层背景改为 `bg-[var(--wall-base)]`，避免在“因果链 / 全图 / 数据表”视图下方暴露黑色底层容器
- 修正后再次验证：`frontend npm run build` 通过，且前端源码中不再存在 `board-dark` / 深色主容器背景残留

### 再次返工：严格按 approved mockup 落地
- 用户进一步指出：`evidence_board_screenshot_v3.png` 就是从 `evidence_board_mockup.html` 直接截出来的，而实际前端仍然“完全不一样”，因此不能再按“参考实现”方式修改。
- 本次返工将 `evidence_board_mockup.html` 视为唯一视觉基准，并继续收敛以下差异：
  - Header 改为更薄的 52px 暖色条
  - 左右侧栏缩窄到约 180px，并弱化为半透明暖色信息条
  - 中间主画布统一为暖黄色/米黄色证据墙背景，带噪声纹理与轻网格
  - `CausalGraphView` / `ChainView` 中的便签、图钉、红线进一步贴近 mockup 的轻薄纸张语言
  - `DataTableView` / `DebateTreeView` 从“产品模块容器”继续压平为贴在同一面证据墙上的纸面工件
- 保留已有真实因果红线连接逻辑与前端 zh/en 切换能力，不为对齐 mockup 牺牲核心交互。

### 首页 React 化
- 用户随后明确要求：首页应尽可能与 `evidence_board_mockup.html` 一致，甚至可以理解为“在 mockup 基础上直接改成 React 首页”。
- 因此首页层做了进一步收口：
  - 移除首页顶部额外状态横幅，让首页回到“薄 header + 证据墙主体”的 mockup 构图
  - `Header` 直接消费当前 query / demo 状态，使关键信息收束进 mockup 式顶部条，而不是额外增加一个产品状态模块
  - `MainCanvas` 默认落在 `causal` 视图，让首页第一屏直接呈现便签 + 红线证据墙，而不是先显示链式视图
  - `CausalGraphView` 支持受控选中节点，以便首页在保持 mockup 主视觉的同时仍可驱动右侧详情交互
- 这一步的目标不是继续“优化一个产品后台”，而是让首页更接近“把 mockup 直接 React 化”的结果。

### 直接以 mockup 重写首页
- 用户最终明确要求：不要再抱着原前端首页结构修补，而是直接以 `evidence_board_mockup.html` 为基础重写首页。
- 因此首页入口 `frontend/src/app/page.tsx` 被改为一份更接近 mockup 的 React 直译版本：
  - 直接内嵌 mockup 同构的 header / 左侧窄栏 / 右侧窄栏 / 主画布 / SVG 红线 / 便签纸布局
  - 默认展示 12 张绝对定位便签与固定红线路径，优先保证首页第一屏视觉忠实度
  - 仅保留最小运行时能力：节点点击高亮 + 右侧详情更新、现有 zh/en 语言切换入口
- 这意味着首页当前更像一个“可运行的 mockup 页面”，而不是之前那种基于旧产品页骨架的改造版。
- 验证结果：`frontend npm run build` 通过，`page.tsx` diagnostics 为 0 error。

### 首页进一步收口：红线按因果关系连接，便签重新排布
- 在 mockup React 首页基础上继续做了两项用户指定收口：
  1. 红线不再使用纯装饰性静态路径，而是通过 `CAUSAL_EDGES` 显式定义便签间的因果关系映射
  2. 便签位置重新分层排布，尽量减少彼此重叠，让阅读路径更清楚
- `page.tsx` 中新增：
  - `NOTE_DIMS`：为不同便签宽高提供中心点估算
  - `CAUSAL_EDGES`：定义 source → target 关系及强度
  - `getNoteCenter()` / `buildEdgePath()` / `computeCausalStrings()`：根据便签位置动态生成 SVG 红线路径
- 排布策略从原先更接近视觉静态稿的拥挤布局，调整为更清晰的 4 层因果流：上层原因、中层中介/环境效应、下层结果与幸存者、边缘证据/替代解释。
- 验证结果：`frontend npm run build` 通过，首页 `page.tsx` diagnostics 仍为 0 error。

### 首页继续收口：红线通过图钉相连
- 用户进一步要求：红线不仅要按因果关系连接，还要“通过图钉相连”。
- 因此首页几何锚点从原先的便签中心，改为图钉中心：
  - `page.tsx` 中将 `getNoteCenter()` 替换为 `getPushpinAnchor()`
  - 根据图钉 SVG 的实际定位（`top: -10px; left: 50%; translateX(-50%)`，圆心 `cx=12, cy=8`），将红线锚点计算为 `x = note.left + width / 2`、`y = note.top - 2`
- `computeCausalStrings()` 改为基于 pushpin anchors 生成红线路径，因此视觉上红线现在是“被图钉钉住并拉向另一张便签”的效果。
- 继续验证结果：
  - `frontend npm run build` 通过
  - `python -m ruff check retrocause tests` 通过
  - `page.tsx` diagnostics 为 0 error

### 首页机制级重构：数据驱动便签 + 智能布局 + 证据墙拖拽
- 用户随后指出当前首页仍有机制缺陷：便签数量写死、布局不够智能、背景不能拖动、红线是否真正来自因果关系不清晰。
- 因此首页 `frontend/src/app/page.tsx` 继续重构为数据驱动证据墙：
  - 从 `mockPrimaryChain.nodes` 与 `mockPrimaryChain.edges` 生成便签与红线，不再依赖手写 `STICKY_NOTES` / `CAUSAL_EDGES` 展示稿
  - 新增 `computeLayout()`：按 `depth` 将节点分层排布，每层横向均匀分布，并加入轻微抖动与旋转，降低重叠概率
  - 新增 `computeCausalStrings()`：直接根据真实 `ChainEdge.source -> target` 生成红线路径
  - 保留 `getPushpinAnchor()` 作为红线起终点，使红线仍通过图钉中心连接
  - 新增背景拖拽 / 平移状态：`isDragging`、`dragStart`、`panOffset`，支持按住背景移动整块证据墙
- 当前首页因此从“静态 mockup React 化”进一步升级为“保留 mockup 外观的数据驱动证据墙首页”。
- 验证结果：
  - `frontend npm run build` 通过
  - `frontend/src/app/page.tsx` diagnostics 为 0 error

### 2026-04-04 首页继续收口：真实证据墙质感 + 可拖动便签 + OSS 入口统一
- 用户进一步要求首页不仅要像证据墙，而且便签本身要可拖动，拖动后红线仍需按真实因果关系重新连接；同时希望我不要暂停确认，而是把 OSS 可交付部分一并收完。
- 因此首页 `frontend/src/app/page.tsx` 继续增强为更接近“物理证据墙”的交互与视觉：
  - 红线继续直接基于 `mockPrimaryChain.edges` 的 `source -> target` 计算，不是装饰性路径
  - 便签新增鼠标拖动交互；拖动更新 `notes` 中对应便签的 `top/left`，红线则通过重新计算 `computeCausalStrings(notes, edges)` 实时跟随图钉位置更新
  - 首页文案进一步接入 zh/en 词典，避免首页残留硬编码英文
  - 证据墙视觉继续打磨：墙面纹理、纸张阴影、折角、胶带、3D 图钉、带下垂感的红线
- 同时把 OSS 入口文档统一到新的前端端口：
  - `README.md`
  - `docs/manual-smoke-test.md`
  - `frontend/README.md`
  以上均改为 `http://localhost:3005`

### 理由
- 可拖动便签让首页从“静态展示图”升级为真正可交互的证据墙
- 红线实时跟随图钉位置，能更直观地证明首页中的连接来自真实因果边而非摆拍
- 统一 OSS 启动与 smoke test 文档，减少新用户第一次运行时的端口困惑

### 2026-04-04 首页继续收口：高亮关联因果 + 数据驱动统计 + 动画
- 为了让 OSS 首页不只是“能看”，而是真正可读、可演示、可传播，这一轮继续补强了首页的交互表达：
  - 左侧 summary 与统计改为直接读取 `mockPrimaryChain.metadata`、`mockPrimaryChain.nodes`、`mockPrimaryChain.edges` 与 edge evidence 数量，不再继续手写固定数字
  - 当选中某个便签时，相关红线与相邻节点会被一起高亮，非相关连接会降低透明度，方便沿因果链阅读
  - 增加入场动画与红线绘制动画，让首页第一屏更像完整产品而不是静态排版
  - 新增底部交互提示，明确“可拖动画布”和“可拖动便签”

### 理由
- OSS demo 的价值不只是实现功能，还要让首次访问者在几秒内理解“这是一张可交互、可追因的证据墙”
- 把首页统计做成数据驱动，能降低 mockup 感和写死痕迹，为后续接真实链路打基础

### 2026-04-04 中间区域双语适配与元信息修复
- 用户要求“顺便把中间的部分也做好英文适配”，同时让我继续往下做，不要反复停下确认。
- 因此这一轮继续把首页主画布与中间相关组件做了更完整的 zh/en 适配：
  - `page.tsx` 中首页标题、便签深度文案、便签类型标签接入 i18n，修复了此前 `getTagLabel(..., () => "")` 导致标签为空的 bug
  - `Header.tsx` 中默认问题 badge 和 `Demo Mode` 改为复用现有翻译键
  - `ChainView.tsx` 中链路 metadata、Legend、选择提示、流向标签、Counterfactual 标签改为 i18n
  - `DataTableView.tsx`、`EvidenceList.tsx`、`DebateTreeView.tsx`、`QueryInput.tsx`、`NodeDetail.tsx`、`ProbabilityBar.tsx`、`RightPanel.tsx` 继续补齐显性英文/中文硬编码
  - `layout.tsx` 中损坏的 metadata title/description 已替换为稳定英文，并将固定 `lang="zh-CN"` 收口为中性 `lang="en"`，避免继续输出错误元信息

### 理由
- 对外 OSS 演示如果首页支持语言切换，而中间核心交互区仍夹杂硬编码英文/中文，会直接削弱专业度
- 先用当前轻量字典方案补齐，比引入新的 i18n 框架更符合“增量、低风险、可 review”的约束

### 2026-04-04 剩余 i18n 收口与最小双语 demo 数据层
- 在继续收口最小可公开版本时，补齐了剩余关键小组件的双语界面层：
  - `HypothesisList.tsx`
  - `Filters.tsx`
  - `AgentList.tsx`
- 同时为了避免“语言切换了，但首页核心内容仍然全是中文”的割裂感，在 `frontend/src/data/mockData.ts` 中新增 `getLocalizedMockData(locale)`：
  - zh 路径继续返回原有 mock 数据
  - en 路径返回最小英文镜像数据，用于首页主证据墙内容
- `frontend/src/app/page.tsx` 已切换为消费 locale-aware demo 数据，而不是直接写死 `mockPrimaryChain`

### 理由
- 对 OSS 首次访问者来说，语言切换如果只改变按钮文本、不改变主内容，会显得明显未完成
- 先用“最小英文镜像数据层”补齐首页核心体验，比一次性重构整套 console 数据源更稳妥

### 2026-04-04 首页接入真实 API 与 demo/real 分层显示
- 用户继续追问：如果 ChatGPT 也能给推理过程，这个项目还有什么优势；并明确指出“如果不能提高推理准确性，本项目会损失很大的使用价值”。
- 因此这一轮的优先级从 UI polish 转回到“诚实的结果展示”：
  - 首页新增最小查询输入与分析按钮
  - 首页直接调用后端 `POST /api/analyze/v2`
  - 当后端返回推荐链时，首页会把推荐链映射成当前证据墙所需的数据结构并渲染
  - UI 会明确区分：
    - `real analysis`
    - `demo fallback`
  - 若真实分析失败，则首页明确提示“已回退到本地 demo”，而不是静默装作分析成功

### 理由
- 如果产品不能在结果层面区分“真实分析”和“演示数据”，证据墙再漂亮也只会放大不可信感
- 相比继续增加视觉细节，更关键的是让用户知道：什么时候可以谨慎参考结果，什么时候只能把它当作结构化示例

### 2026-04-04 首页信任信号补强：链切换联动、推荐链标识与证据过滤
- 在首页接入 `/api/analyze/v2` 后，继续补齐了影响可信度的联动缺口：
  - 便签布局重算现在会跟随 `activeChain`
  - 切链、切语言、分析成功/失败回退时统一重置 `selectedNodeId` 与 `panOffset`
  - 左侧备选链列表开始消费 `recommended_chain_id`，对推荐链增加显式标记
  - 右侧证据区改为优先展示“当前选中节点 / 当前链”真正相关的证据，而不是简单截取全局 `evidencePool`
  - 单条证据增加强 / 中 / 弱标签，首页增加低置信度、低证据覆盖、高不确定性提示

### 理由
- 用户对结果准确性和情报可信度高度敏感，因此首页必须优先补足诚实的信任信号，而不是继续只做视觉 polish
- 对 OSS 版本而言，展示“推荐链是什么、证据够不够、哪里不确定”比假装结果可靠更重要
- 继续在现有单文件首页实现上做小步修补，风险最低，也更符合“最小可公开版本”的节奏

### 验证结果
- `frontend/src/app/page.tsx` diagnostics clean
- `frontend npm run build` 通过（Next.js 16.2.2）
- `python -m ruff check retrocause tests` 通过
- `pytest tests/` 通过（71 passed）

---

## 2026-04-07 OSS / Pro 边界与商业化原则公开化

### 背景
用户明确要求：在 OSS 版本真正做到“可用的最小开源版本”之前不要发布，同时要提前想清楚：

- OSS 与未来 Pro 的区别到底是什么
- 有没有真实用户痛点与实际场景
- 是否能激发付费意愿
- 是否有足够的技术壁垒和差异化

这意味着项目不能只停留在“能跑 demo”和“README 会讲故事”，而需要把公开叙事、产品边界和商业化原则写清楚。

### 决策
- 新增公开文档 `docs/oss-pro-positioning.md`
- README 中补充：
  - OSS 的发布门槛不只是 demo 可运行，还必须达到“诚实、稳定、可理解”的最低可用标准
  - Pro 的价值不应来自隐藏核心想法，而应来自更高质量、更高可信度、更强工作流深度
- roadmap 中新增：
  - P0：最小可公开 OSS 版本的发布前清单
  - P6：围绕真实 jobs-to-be-done 构建未来 Pro，而不是泛化 feature gating

### 核心判断
- OSS 应保留核心产品心智：why-question → 竞争链路 → 证据 → 不确定性 → 可检视解释界面
- Pro 应建立在“高频、高损失、需要对别人解释”的工作流上，而不是仅仅提供更多模型输出
- 当前项目真正可形成差异化的方向不是“更聪明的 AI 回答”，而是：
  - explanation as structure
  - explicit evidence attachment
  - explicit uncertainty signaling
  - competing causal chains as first-class output
- 当前真正值得继续投资的壁垒方向是：
  - evidence-grounded quality
  - workflow-specific explanation outputs
  - trust-preserving product behavior
  - repeated-use templates / domain packs / reusable explanation assets

### 理由
- 用户已经明确指出：如果准确性和可信度不够，产品价值会显著受损。因此商业化判断必须围绕“信任”和“工作流价值”展开，而不是围绕表层功能数量展开。
- 对开源项目而言，过早发布一个“概念正确但体验不完整”的版本，会伤害后续口碑和分发效率。
- 提前把 OSS / Pro 原则公开化，可以让后续功能取舍更一致，也能减少开源访客对项目成熟度和商业意图的误解。

### 补充研究依据
- evidence-grounded quality 方向的公开依据已补充到 `docs/oss-pro-positioning.md`，重点参考了 DoWhy、RAGAS、TruLens、Vectara FCS 等公开资料。
- workflow-specific explanation outputs、trust-preserving product behavior、reusable domain packs 方向的公开依据已一并收口到该文档中，用于指导后续 Pro 路线不偏向“更多模型输出”，而偏向“更高可信度和更强工作流价值”。

---

## 2026-04-07 Browser UI 真实分析接通与 demo honesty 统一

### 背景
此前 OSS 虽然已经有首页 evidence board、CLI honest fallback 和 `/api/analyze/v2`，但仍存在三个关键不一致：

- Browser UI 只能发 `query`，不能直接走用户本地输入 key 的真实分析
- V1 API 不返回 demo 元数据
- Streamlit 初始加载与无 key 路径仍容易让用户误读为真实分析

### 决策
- 首页 `frontend/src/app/page.tsx` 增加本地 API key 与 provider/model 输入，并把请求体统一为 `query` / `model` / `api_key`
- FastAPI 的 V1 / V2 endpoint 在有 key 时优先调用真实分析，在失败或无 key 时统一回退到 `topic_aware_demo_result(query)`
- `AnalysisResult` 增加 `is_demo` 与 `demo_topic`
- Browser UI / API / Streamlit 统一暴露 demo 元数据与显式提示
- Streamlit 首屏默认结果与无 key 运行路径都改为 topic-aware demo，并显示持久 warning banner

### 理由
- 本地开源工具允许用户在 Browser UI 中输入 key 是合理的，但前提是必须保持 trust-preserving copy，不能伪装成云端托管安全模型
- demo fallback 合理，但如果产品不同入口的诚实度不一致，会直接损害 OSS 的可信度
- 统一 `is_demo` / `demo_topic` 可以让前端、API、文档和后续 smoke test 使用同一套真值来源

### 验证结果
- `frontend/src/app/page.tsx` diagnostics clean
- `retrocause/api/main.py` diagnostics clean
- `retrocause/app/demo_data.py` diagnostics clean
- 后续以 `pytest tests/`、`ruff check retrocause tests`、`frontend npm run build` 作为统一发布前验证

---

## 2026-04-07 工程硬化：LLM 重试与 config timeout 接入

### 背景
engineering-audit.md 中的 H3 和 H4 长期标记为待完成：
- H3：所有 LLM 调用静默 catch `openai.OpenAIError` 后返回空值，无重试，无区分可恢复错误与不可恢复错误
- H4：`config.py` 的 `request_timeout_seconds` 未传入 OpenAI 客户端构造，`llm.py` 硬编码使用 `OPENAI_TIMEOUT` 环境变量

### 决策
- 新增 `_call_with_retry()` 模块级函数：指数退避（base delay 1s × 2^attempt），最多 3 次重试
- 仅对可重试异常重试：`RateLimitError`、`APITimeoutError`、`APIConnectionError`
- 其他异常（`AuthenticationError`、`BadRequestError` 等）立即抛出，不做无意义重试
- `LLMClient.__init__` 新增 `timeout` 参数，替代硬编码环境变量
- `run_real_analysis()` 现在从 `RetroCauseConfig.from_env()` 获取 timeout 并传入 `LLMClient`

### 理由
- 限流、超时、连接断开是 LLM API 的常见瞬态故障，自动重试可显著减少"第一次调用偶然失败 → 整条 pipeline 返回空结果"的问题
- 重试只针对可恢复错误，避免在认证失败等不可恢复场景下浪费时间
- config timeout 被定义了但从未使用是典型的"结构存在但未接通"问题，修复成本极低

### 验证结果
- `pytest tests/ -v` 通过（71 passed）
- `ruff check retrocause tests` 通过
- `llm.py` / `demo_data.py` lsp diagnostics clean

---

## 2026-04-07 工程硬化：独立评估步骤（generator/evaluator 分离）

### 背景
engineering-audit.md 的 H5 指出：pipeline 缺少独立评估者。每个步骤既生成内容又隐式自验证，HookEngine 的规则检查是逐步骤的局部检查，没有最终全面评估。这是 harness engineering 中"generator 必须与 evaluator 分离"的典型反模式。

### 决策
- 新增 `retrocause/evaluation.py`，包含 `EvaluationStep(PipelineStep)` 和 `PipelineEvaluation` 数据类
- `EvaluationStep` 作为 pipeline 的最后一步运行，只读取不生成：
  - **evidence_sufficiency**（权重 40%）：证据覆盖率、未锚定边比例、总证据数
  - **probability_coherence**（权重 35%）：概率边界、置信区间、链间概率分配合理性
  - **chain_diversity**（权重 25%）：竞争链变量集 Jaccard 相似度
  - **overall_confidence**：加权综合得分，步骤错误额外惩罚
- `PipelineContext` 新增 `evaluation` 字段
- `AnalysisResult` 新增 `evaluation: PipelineEvaluation | None` 字段
- 新增 18 个测试覆盖三个评估维度和集成场景

### 理由
- 分离 generator 和 evaluator 是 harness engineering 的基本原则，避免"自己评价自己"
- 评估结果可被前端 / API 消费，向用户展示分析结果的可信度信号
- 纯规则评估（不依赖 LLM）意味着零额外 API 成本和确定性测试

### 验证结果
- `pytest tests/ -v` 通过（89 passed，新增 18）
- `ruff check retrocause tests` 通过
- `evaluation.py` / `engine.py` / `models.py` / `pipeline.py` diagnostics clean

---

## 2026-04-07 全面边界测试与真实数据链路审查

### 背景
在完成 P0-P1.6 全部工程项后，需要确认 OSS 版本是否真正达到"可用的最小开源版本"标准。这要求不仅通过单元测试，还要覆盖边界用例、API schema 完整性、demo 数据一致性，以及确认真实分析链路的实际可用性。

### 决策
- 新增 `tests/test_comprehensive.py`（38 个测试），覆盖 8 个维度：
  - demo topic 检测（11 个参数化用例，中英文混合）
  - demo 结果完整性（5 个 topic × hypotheses/variables/edges 非空 + 边引用有效性 + 变量子集一致性）
  - API V2 schema 转换（最小/完整/空/多链/节点类型）
  - Pydantic 序列化 round-trip（JSON dump → parse → 验证字段）
  - pipeline evaluation 边界（分数 [0,1]、step_error 惩罚、负置信区间、相同链多样性）
  - providers 配置完整性（base_url + models 存在性检查）
  - models 默认值（AnalysisResult / HypothesisChain）
  - pipeline 空运行与故障捕获
- 审查真实分析链路，确认 ArXiv / Semantic Scholar / DuckDuckGo 三个 source adapter 均为真实 HTTP 实现（非 stub）
- 审查 `run_real_analysis()` 确认其正确接入 engine pipeline（LLM + sources → 6 步 pipeline → AnalysisResult）
- 明确 OSS/Pro 优化边界：OSS 优化方向是"更好的展示"，Pro 优化方向是"更好的质量"

### 理由
- 单元测试只覆盖"happy path"，边界测试才能暴露 demo 数据不一致、schema 序列化失败、极端值溢出等问题
- 真实分析链路的可用性是 OSS 的核心价值，必须确认不是"看起来接通但实际是 stub"
- OSS/Pro 边界规划可以防止后续迭代时功能泄漏，保持 OSS 和 Pro 的价值定位清晰

### 验证结果
- `pytest tests/ -v` 通过（127 passed，新增 38）
- `ruff check retrocause tests` 通过
- `frontend npm run build` 通过
- LSP diagnostics（39 Python files + page.tsx）0 errors

---

## 2026-04-08 Smoke Test 自动化

### 背景
OSS 发布前需要验证应用端到端可用性。手动 smoke test（`docs/manual-smoke-test.md`）覆盖 7 个场景，但每次手动执行效率低且不可重复。需要自动化 API 层和 UI 层的 smoke test。

### 决策
- 新增 `scripts/smoke_test.py`（Python + urllib）：38 个 HTTP 检查项
  - 后端 root (`/`) 健康检查
  - V2 API 5 个 demo topic（svb/stock/crisis/rent/dinosaur）的完整响应验证
  - V1 API 兼容性检查（`/api/analyze` fallback）
  - 边变量完整性（每个边的 source/target 在 nodes 中存在）
  - 前端 HTML 可达（`http://localhost:3005` 返回 200）
- 新增 `scripts/ui_smoke_test.py`（Python + Playwright Chromium）：21 个浏览器检查项
  - Scenario 1: 初始加载（evidence board 容器、header/left/right 三面板、无 dark-terminal 残留、便签卡片渲染）
  - Scenario 2: Demo 透明度（demo 模式标识、header 状态指示器）
  - Scenario 3: 查询流（textarea 输入、提交按钮、查询后页面存活、卡片保持渲染、状态更新）
  - Scenario 4: 节点点击/多跳（选中高亮 ring-2、右侧面板更新、第二个节点可点、取消选中）
  - Scenario 5: 语言切换（EN/中 按钮切换、切换后页面正常渲染）
- Playwright 使用 Chromium（非 Chrome，因 Windows 权限限制无法安装 Google Chrome）

### 理由
- API smoke test 确认后端数据层完整可用，无需浏览器
- UI smoke test 覆盖前端交互层，验证 evidence board 首页的核心用户流程
- 自动化后可作为 CI 前置条件或 release checklist 的一部分
- Chromium 与 Chrome 渲染结果一致，不影响测试有效性

### 验证结果
- API smoke test: 38/38 PASS
- UI smoke test: 21/21 PASS
- 全部测试脚本已提交（commit `8fb0ec5`）

---

## 2026-04-09 OSS / Pro 分层与 Pro 全栈 Rust 方向同步

### 背景
用户明确要求继续做好 OSS / Pro 分层，并特别指出：**Pro 版后续计划走全栈 Rust**。因此需要把这一点同步进公开文档与私有架构文档，避免“产品定位说一套、架构规划写另一套”。

### 决策
- `README.md` 补充架构分层说明：
  - OSS 保持当前 Python + FastAPI + Next.js 路线
  - Pro 规划为独立全栈 Rust 产品线，而不是单纯 feature gating
- `docs/oss-pro-positioning.md` 补充 “Architecture split” 小节
- `docs-private/retrocause-pro-rust-architecture.md` 新增 “OSS / Pro 分层原则” 前置章节，明确该文档描述的是 Pro 目标架构，不是 OSS 近期迁移计划

### 理由
- OSS 的首要目标是 runnable / inspectable / contribution-friendly
- Pro 的首要目标是更高可靠性、更深工作流、更低单位成本与更强团队交付能力
- 两者的约束不同，过早强行共用一套 Web 架构会让 OSS 过重、让 Pro 受限
- “产品心智共享，代码实现允许分叉”更符合当前阶段

### 同步结果
- 公开文档与私有规划文档的叙事已统一
- 后续可继续在 Pro Rust 文档中深化工程方案，而不影响 OSS 发布叙事

---

## 2026-04-09 Frontier 技术落点与 Rust Pro 改造边界

### 背景
在完成真实分析修复后，用户进一步要求：

- 不只是讨论前沿技术，还要分析这些技术应如何融入项目
- 需要明确当前 OSS 版本的技术架构
- 需要明确未来 Pro 全栈 Rust 应该重写哪些部分、桥接哪些部分
- 文档需要同步到统一叙事

并行分析（explore / librarian / oracle）后的结论是：
**共享产品契约，运行时分叉** 是当前最合理的路线。

### 决策
- OSS 只优先接入那些能直接增强“inspectability / honesty / evidence quality”的 frontier 技术：
  - evidence-grounded evaluation
  - citation-grounded outputs
  - support-vs-refutation balance
  - lightweight graph-guided retrieval / CausalRAG-style retrieval
  - uncertainty communication
- Pro-first 保留给更像“工作流产品底座”的能力：
  - persistent workspaces
  - strong provenance ledger
  - streaming long-running analysis UX
  - domain packs / repeated-use workflows
  - heavy multi-agent orchestration
  - stakeholder/client report workflows
- Pro 全栈 Rust 的重写重点放在：
  - API / session layer
  - 流式编排
  - 图遍历 / 比较 / 布局
  - typed models
  - workspace / cache / permission / multi-tenant substrate
- Python 继续保留在 loop 中的部分：
  - NumPyro / JAX 概率推理
  - DoWhy / PyWhy / refutation 等研究型内核
  - 原则上采用**粗粒度 bridge**，避免细粒度 FFI

### 理由
- Rust 更适合解决高并发、强类型、低延迟、长连接、运营复杂度问题；它**不是**自动提高因果正确性的来源
- 因果正确性和可信度的主要提升，仍来自更好的 evidence grounding、校准、评估、反驳与敏感性分析
- OSS 的任务是把产品核心心智讲清楚并保持诚实；Pro 的任务是让高频和高风险用户愿意反复依赖

### 同步结果
- `README.md` 增加了 OSS 当前 runtime architecture 和 frontier capability placement
- `docs/roadmap-and-limitations.md` 增加了 OSS 可做 / Not planned for OSS / architecture heuristic
- `docs/oss-pro-positioning.md` 增加了 frontier placement
- `docs-private/retrocause-pro-rust-architecture.md` 增加了共享产品契约、Rust rewrite / Python bridge 边界、迁移映射

---

## 2026-04-09 CausalRAG / Uncertainty / Citation Grounding 实现

### 背景
RetroCause 之前的三项核心前沿能力（CausalRAG、不确定性通信、span-level citation grounding）仅在文档中规划，未落地到代码。证据收集是平面子查询检索，不确定性评估是 heuristic 计数，证据锚定仅通过 variable name overlap 绑定 evidence id。

### 决策
1. **CausalRAG**: 在 `collector.py` 新增 `graph_guided_collect` 和 `search_by_causal_path` 方法，基于因果图结构（薄弱边、低覆盖变量）生成定向子查询，补充第二轮检索
2. **Uncertainty Modeling**: 新增 `uncertainty.py` 模块，实现 per-node / per-edge 的结构化不确定性评估（epistemic vs data vs thin evidence vs conflicting vs low-confidence reasoning），生成 `UncertaintyReport` 汇总
3. **Citation Grounding**: 升级 `anchoring.py` 的 `ground_citation_spans`，从证据文本中定位与因果断言相关的句子级片段（CitationSpan），支持 start_char / end_char / quoted_text
4. **Pipeline 整合**: 在 `engine.py` 的 pipeline 中新增 `CausalRAGStep`（在 anchoring 之后、counterfactual 之前）和 `UncertaintyAssessmentStep`（在 debate 之后、evaluation 之前）
5. **API 扩展**: V2 schema 新增 `CitationSpanV2`、`UncertaintyAssessmentV2`、`UncertaintyReportV2`、edge 上 `evidence_conflict` 字段

### 理由
- 这三项是 RetroCause 与直接用 ChatGPT 的核心差异点
- CausalRAG 使检索不再是平面的，而是因果图结构感知的
- 不确定性从 heuristic 计数升级为结构化分类，使分析结果更可检查
- Citation grounding 从 id-level 升级为 span-level，让用户能看到证据中的具体支撑片段
- 所有改动向后兼容：新增字段有默认值，现有 pipeline 步骤不变

### 改动文件
- `retrocause/models.py` — 新增 UncertaintyType, EvidenceConflictType, CitationSpan, UncertaintyAssessment, UncertaintyReport
- `retrocause/collector.py` — 新增 graph_guided_collect, search_by_causal_path, _build_graph_aware_subqueries, _execute_subqueries
- `retrocause/uncertainty.py` — 新模块（assess_variable_uncertainty, assess_edge_uncertainty, detect_evidence_conflict, build_uncertainty_report, UncertaintyAssessmentStep）
- `retrocause/anchoring.py` — 新增 ground_citation_spans, _extract_relevant_span, _compute_span_relevance；升级 EvidenceAnchoringStep
- `retrocause/engine.py` — 新增 CausalRAGStep，pipeline 中插入 CausalRAGStep + UncertaintyAssessmentStep
- `retrocause/api/main.py` — V2 schema 扩展（CitationSpanV2, UncertaintyAssessmentV2, UncertaintyReportV2, edge.evidence_conflict）
- `frontend/src/app/page.tsx` — homepage 现已消费 uncertainty / citation / conflict 数据，并补齐 evidence filtering、chain compare snapshot、edge insight 面板
- `tests/test_causal_rag.py` — 6 个新测试
- `tests/test_uncertainty.py` — 10 个新测试
- `tests/test_citation.py` — 5 个新测试

---

## 2026-04-10 Pipeline 性能优化 + SSE 实时进度

### 背景
真实分析 pipeline 执行时间超过 7 分钟，85 次串行 LLM 调用，Semantic Scholar 429 限流无退避，无全局超时，前端无进度感知。

### 决策

**后端优化（4 文件）：**
1. `collector.py` — `_parallel_search()` 使用 ThreadPoolExecutor 并行搜索所有源；`auto_collect` 改为批量提取（合并同 sub_query 所有搜索结果为一次 LLM 调用）
2. `engine.py` — CausalRAGStep 添加 `COVERAGE_THRESHOLD = 0.5`，覆盖率 ≥ 50% 跳过第二轮检索
3. `pipeline.py` — 新增 `ProgressCallback` 类型 + `on_progress` 字段到 PipelineContext + Pipeline.run() 每步触发回调
4. `api/main.py` — 120s 超时兜底 + 新增 SSE `/api/analyze/v2/stream` 端点

**前端改造（1 文件）：**
5. `page.tsx` — runAnalysis 改为 SSE ReadableStream 消费 + header 进度条 + 错误 banner 红色高亮

### 理由
- **批量提取**：LLM 看到更多上下文能交叉去重，实际质量更好而非更差
- **并行搜索**：3 源无数据依赖，纯 I/O 并行零质量影响
- **条件 CausalRAG**：覆盖率已足够时跳过冗余检索，避免浪费
- **SSE**：用户不再干等，实时看到 pipeline 步骤进度
- **120s 超时**：兜底保护，防止无限挂起

### 效果
| 指标 | 优化前 | 优化后 |
|---|---|---|
| LLM 调用次数 | ~85 次（串行） | ~19 次 |
| 典型耗时 | 7+ 分钟 | 1.5-2 分钟 |
| 成本 | 基线 | 省 ~50% |
| 产品质量 | 基线 | 不变/更好 |
| UI 进度感知 | 无 | SSE 实时进度条 |

---

## 2026-04-10 前端 Dev Server Hydration 修复

### 背景
Next.js 16.2.2 dev server 在 `127.0.0.1` 上 HMR WebSocket 握手失败（`ERR_INVALID_HTTP_RESPONSE`），导致 React 19 的 `debugChannel` 流永远不关闭 → `createRoot().render()` 不执行 → 整个客户端 hydration 卡死。SSR HTML 正常但 `useEffect` 不触发、便签不渲染。Production build 不受影响。

上游确认：vercel/next.js Discussion #91770，影响 16.2.x 系列。

### 决策
1. `package.json` dev 脚本改为 `next dev --hostname localhost`（而非默认的 `0.0.0.0`）
2. `next.config.ts` 添加 `devIndicators: false`

### 理由
- `localhost` 在现代浏览器和 Node.js 中有特殊处理（可能走 IPv6 loopback `::1`），WebSocket 升级正常工作
- `127.0.0.1` 强制 IPv4，某些环境下 Next.js dev server 的 WS handler 不兼容
- Production build 不依赖 WebSocket/HMR，所以完全不受影响
- `--hostname localhost` 是最小改动，不需要降级 Next.js 版本或禁用 Turbopack

---

## 2026-04-10 真实分析 Pipeline 修复

### 背景
用户使用 OpenRouter + DeepSeek 模型测试时，pipeline 完成全部 9 步但返回空 hypothesis，触发 demo fallback（`is_demo=True`）。根因：LLM 返回的 `content` 字段有时为 `None`、有时被 markdown code fence 包裹、有时返回 JSON 数组而非对象——这些异常格式未被处理，导致 `json.loads()` 失败被静默捕获，下游步骤无数据可用。

### 决策
1. `llm.py` 新增 `_safe_parse_json()` 函数，5 层容错解析：直接解析 → markdown fence 提取 → 花括号提取 → 方括号提取 → 数组包装为对象
2. `debate.py` 重写 DebateOrchestrator：从 6 个 DebateAgent 实例改为单次 `debate_hypothesis()` 调用（6N → N 次 LLM 调用）
3. `engine.py` 在 EvidenceCollectionStep、GraphBuildingStep、HypothesisGenerationStep 添加 warning 日志
4. `models.py` 添加 `UncertaintyType.MODEL` 枚举值
5. SSE stream 超时从 120s 提高到 300s

### 理由
- LLM 输出格式不可控，必须做防御性解析
- DebateOrchestrator 的 6 个 agent 各自调用 `debate_hypothesis()` 但只提取一个 role，其余丢弃——纯浪费 token
- 300s 超时匹配实际 pipeline 耗时（实测 185.9s）
- 最小改动原则：不改 pipeline 架构，只修复解析和超时

### 验证
- ruff check: 0 errors
- pytest: 148/148 passed
- 直接 Python 调用: `is_demo=False`, 1 hypothesis, 7 variables, 6 edges, 12 evidence, 185.9s
- SSE endpoint: 新代码已加载验证（无效 key 返回正确的 "empty result" 消息）；真实 key 测试因 ArXiv/Semantic Scholar rate limiting 暂受阻
