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
