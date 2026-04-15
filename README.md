# RetroCause

**English:** Ask "why did this happen?" and inspect an evidence-backed causal map.

**中文：** 输入一个“为什么会这样？”的问题，得到带证据、反证、来源轨迹和因果链的可检查解释。

RetroCause is an open-source causal explanation workspace for complex events. It is not a truth oracle and it is not a production causal-inference system. Its goal is to make AI explanations easier to inspect: users can see proposed reasons, supporting evidence, challenge checks, uncertainty signals, and retrieval-source health instead of receiving one opaque paragraph.

RetroCause 是一个开源的因果解释工作台，适合研究复杂事件的“原因链”。它不是因果真理机器，也不是生产级科学因果推断系统。它的目标是让 AI 输出更可检查：用户可以看到原因、证据、反证检查、不确定性和检索来源健康状态，而不是只看到一段不可追踪的总结。

![RetroCause live evidence board](docs/images/golden-us-iran-live-ui.png)

## What You Get / 你会看到什么

- **Evidence-backed causal chains / 带证据的因果链：** competing explanations with probabilities and linked evidence.
- **Readable brief / 阅读版简报：** a structured in-app report with the likely explanation, top reasons, challenge coverage, gaps, evidence coverage, and source-health summary.
- **Markdown research brief / Markdown 研究简报：** copy a portable report with the question, likely explanation, reasons, challenge coverage, evidence, and source trace.
- **Copy fallback / 复制降级：** if browser clipboard permissions block one-click copy, the app opens a manual-copy text area.
- **Source trace / 来源轨迹：** each live run shows which sources were queried, how many results were found, whether cache was used, and whether a source was limited or degraded.
- **Source health summary / 来源健康摘要：** the readable brief summarizes checked sources, successful sources, cached sources, degraded sources, stable-source coverage, and whether the result is still reviewable.
- **Challenge coverage / 反证覆盖：** checked causal edges show whether refuting or context evidence was found. If a checked edge has no attached refuting evidence, the brief says that directly instead of showing ambiguous `0 challenge` wording.
- **Provider preflight / 模型预检：** test whether the selected model and API key can return valid JSON before running a full analysis.
- **Value harness / 结果价值检查：** the UI tells you whether a result is ready for review, needs more evidence, or is blocked by provider/model setup.
- **Production brief modes / 生产级简报模式：** auto-detect or choose Market / Investment, Policy / Geopolitics, or Postmortem so the output explains what a user can decide, what evidence supports it, what could change the view, and what is not ready yet.
- **Demo transparency / Demo 透明标记：** demo, partial-live, and live modes are labeled explicitly.

## Current Status / 当前状态

**English:** RetroCause is a research-grade alpha published as `v0.1.0-alpha.4` at [github.com/logi-cmd/retrocause-ai](https://github.com/logi-cmd/retrocause-ai). The browser app, API, tests, provider preflight, challenge coverage, Markdown research brief, copy fallback, source-health summary, value harness, scenario-aware production brief harness, and SourceBroker retrieval-health pass work locally.

**中文：** RetroCause 当前是 research-grade alpha，已在 [github.com/logi-cmd/retrocause-ai](https://github.com/logi-cmd/retrocause-ai) 发布 `v0.1.0-alpha.4`。本地浏览器应用、API、测试、模型预检、反证覆盖、Markdown 研究简报、复制降级、来源健康摘要、结果价值检查、场景化生产级简报，以及 SourceBroker 检索健康状态都已经可用。

Known limits / 已知限制：

- Results are evidence-grounded explanations, not verified causal truth.
- Live quality depends on source availability, model behavior, API quota, and provider rate limits.
- Source adapters can be rate-limited. Sustainable hosted use requires source policies, cache, provider budgets, and run orchestration.
- Source trace rows expose retrieval-health states such as `cached`, `rate-limited`, `source-limited`, `timeout`, and `source-error`. Treat these as source/retrieval limits, not as evidence against a cause.
- Some generated labels may remain partly English in Chinese mode, but live graph nodes should keep their specific meaning instead of falling back to generic factor labels.
- PDF/DOCX export, saved runs, scheduled watch topics, team review, and branded reports are not included in OSS.

- 结果是“有证据锚定的解释”，不是已经被证明的因果真理。
- Live 模式质量取决于来源可用性、模型行为、API 额度和 provider 限流。
- 检索源适配器可能被限流。可持续的托管版本需要来源策略、缓存、provider 预算和运行编排。
- 来源轨迹会显示 `cached`、`rate-limited`、`source-limited`、`timeout`、`source-error` 等检索健康状态。它们表示“来源或检索受限”，不是“某个原因被证伪”。
- 中文模式下，部分模型生成的长标签可能仍保留英文；但 live 因果图节点会保留具体含义，而不是退回成泛化的“因素”标签。
- OSS 当前不包含 PDF/DOCX 导出、历史保存、定时追踪、团队审阅或品牌化报告。

## Quick Start / 快速开始

### 1. Install / 安装

```bash
pip install -e ".[dev]"
cd frontend
npm install
cd ..
```

### 2. Start the app / 启动应用

```bash
python start.py
```

Then open / 然后打开：

- Frontend / 前端: `http://localhost:3005`
- Backend API / 后端 API: `http://localhost:8000`

### 3. Try demo mode / 先试 Demo

Open the homepage and submit a question without an API key. RetroCause will show clearly labeled demo output so you can inspect the interface safely.

打开首页，不填 API key 直接提交问题。RetroCause 会显示明确标记的 demo 输出，你可以先体验界面、证据墙和因果链。

Example questions / 示例问题：

- Why did SVB collapse?
- Why did the 2008 financial crisis happen?
- Why is rent so high in New York?
- 美国和伊朗在伊斯兰堡谈判结束，未达成协议的原因是什么？
- 为什么比特币今天价格下跌？

### 4. Run live analysis / 跑真实分析

1. Open **Model settings** on the homepage.
2. Paste your OpenRouter API key.
3. Click **Run model preflight**.
4. Choose **Auto detect**, **Market / Investment**, **Policy / Geopolitics**, or **Postmortem** in the use-case selector.
5. If preflight passes, click **Start analysis**.
6. Inspect the production brief, analysis brief, source trace, challenge coverage, and value harness before trusting the result.
7. In source trace, treat `rate-limited`, `source-limited`, `timeout`, and `source-error` rows as retrieval-health limits. They tell you what source failed or degraded, not whether the proposed cause is true or false.
8. Click **Copy report** in the readable brief card to take the Markdown report into notes, docs, or research workflows. If the browser blocks clipboard access, use the manual-copy report box that appears.

中文步骤：

1. 打开首页的 **模型与密钥设置**。
2. 粘贴你的 OpenRouter API key。
3. 点击 **运行模型预检**。
4. 在使用场景选择器里选择 **自动识别**、**市场 / 投资**、**政策 / 地缘政治** 或 **复盘**。
5. 预检通过后点击 **开始分析**。
6. 先检查生产级简报、分析简报、来源轨迹、反证覆盖和 Value Harness，再决定是否相信结果。
7. 在来源轨迹里，`rate-limited`、`source-limited`、`timeout`、`source-error` 表示检索健康问题。它们说明哪个来源失败或降级，不代表某个原因本身为真或为假。
8. 在分析结论卡片中点击 **复制报告**，把 Markdown 结果带进笔记、文档、投研或政策分析流程。如果浏览器拦截剪贴板权限，请使用自动展开的手动复制文本框。

API keys are only needed for real analysis. Without a key, the app remains usable in demo mode.

真实分析需要 API key。没有 key 时，应用仍可用 demo 模式体验。

## Optional Hosted Search Sources / 可选托管检索源

RetroCause OSS works without hosted-search accounts. Optional hosted adapters are only registered when you provide keys before starting the app:

```bash
set TAVILY_API_KEY=your_tavily_key
set BRAVE_SEARCH_API_KEY=your_brave_key
python start.py
```

PowerShell example:

```powershell
$env:TAVILY_API_KEY = "your_tavily_key"
$env:BRAVE_SEARCH_API_KEY = "your_brave_key"
python start.py
```

- `TAVILY_API_KEY` enables Tavily Search as an optional source.
- `BRAVE_SEARCH_API_KEY` enables Brave Search as an optional source.
- If those variables are absent, RetroCause uses the built-in OSS source adapters.
- Hosted providers may enforce rate limits or storage rules. RetroCause exposes those limits in source trace instead of hiding them.

RetroCause OSS 不依赖托管检索账号。只有在启动前提供 key 时，可选托管适配器才会注册：

- `TAVILY_API_KEY` 启用 Tavily Search。
- `BRAVE_SEARCH_API_KEY` 启用 Brave Search。
- 未设置这些变量时，RetroCause 使用内置 OSS 检索源继续运行。
- 托管 provider 可能有额度、限流或存储规则。RetroCause 会把这些限制显示在来源轨迹里，而不是假装检索成功。

## API Usage / API 用法

Run the backend with `python start.py`, then call:

```bash
curl -X POST http://localhost:8000/api/analyze/v2 \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Why did SVB collapse?\"}"
```

Provider preflight:

```bash
curl -X POST http://localhost:8000/api/providers/preflight \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"openrouter\",\"explicit_model\":\"deepseek/deepseek-chat-v3-0324\",\"api_key\":\"YOUR_KEY\"}"
```

Windows PowerShell note / Windows PowerShell 注意：

For Chinese queries, send UTF-8 JSON bytes. Plain string request bodies can corrupt Chinese text on some Windows consoles.

中文问题请用 UTF-8 bytes 发送 JSON。某些 Windows 控制台直接发送字符串 body 时，中文可能变成 `????????`。

## Development / 开发

Run the full local verification suite:

```bash
npm test
```

This runs:

- frontend lint
- frontend build
- `ruff check retrocause/`
- `pytest tests/`
- full-stack E2E smoke tests

## Tech Stack / 技术栈

- Backend: Python, FastAPI, OpenAI-compatible SDK
- Frontend: Next.js, React, Tailwind CSS
- Causal graph: NetworkX
- Probabilistic reasoning groundwork: NumPyro / JAX
- Evidence sources: web search adapters, AP News, Federal Register, GDELT, ArXiv, Semantic Scholar, optional Tavily, optional Brave Search
- Retrieval strategy: see [`docs/retrieval-and-output-strategy.md`](docs/retrieval-and-output-strategy.md)

## When To Use It / 适合什么场景

RetroCause is useful when a user needs to explain an event and inspect the reasoning path:

- market or policy event explanations
- geopolitical/news causal briefings
- company or competitor postmortems
- research demos for evidence-grounded explanation UX

RetroCause 适合需要“解释事件原因，并检查推理链”的场景：

- 市场或政策事件解释
- 地缘政治 / 新闻因果简报
- 公司或竞品复盘
- 证据锚定解释界面的研究 demo

## OSS vs Pro Boundary / OSS 和 Pro 边界

**OSS:** local, inspectable analysis for individual researchers and builders. OSS includes the evidence board, source trace, challenge coverage, value harness, scenario-aware single-run production briefs, optional user-key hosted search adapters, and a copyable Markdown research brief.

**Pro direction:** hosted reliability for individuals and small teams. Pro should justify payment through run queues, quota management, cache reuse, saved runs, uploaded evidence, scheduled watch topics, PDF/DOCX reports, lightweight team review, source-policy controls, and higher-trust operating workflows. Enterprise private deployment is not a near-term goal.

**OSS：** 面向个人研究者和开发者，重点是本地可运行、可检查、可复制。OSS 包含证据墙、来源轨迹、反证覆盖、结果价值检查、场景化单次生产级简报、用户自带 key 的可选托管检索源，以及可复制的 Markdown 研究简报。

**Pro 方向：** 面向个人和小团队的托管可靠性。付费价值应来自运行队列、额度管理、缓存复用、历史保存、上传资料、定时主题追踪、PDF/DOCX 报告、轻量团队审阅、来源策略控制和更高可信的运营流程。企业私有部署不是近期目标。

## License / 许可证

MIT
