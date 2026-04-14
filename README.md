# RetroCause

**English:** Ask "why did this happen?" and inspect an evidence-backed causal map.

**中文：** 输入一个“为什么会这样？”的问题，得到带证据、反证、来源轨迹和因果链的可视化解释。

RetroCause is an open-source causal explanation workspace for complex events. It is not a truth oracle and it is not a production causal-inference system. Its goal is to make AI explanations easier to inspect: users can see the proposed reasons, supporting evidence, challenge checks, uncertainty signals, and source trace instead of receiving one opaque paragraph.

RetroCause 是一个开源的因果解释工作台，适合研究复杂事件的“原因链”。它不是因果真理机器，也不是生产级科学因果推断系统。它的目标是让 AI 输出更可检查：用户可以看到原因、证据、反证检查、不确定性和检索来源，而不是只看到一段不可追踪的总结。

![RetroCause live evidence board](docs/images/golden-us-iran-live-ui.png)

## What You Get / 你会看到什么

- **Evidence-backed causal chains / 带证据的因果链**: competing explanations with probabilities and linked evidence.
- **Readable brief / 阅读版简报**: a structured in-app report with the likely explanation, top reasons, challenge coverage, gaps, and evidence coverage.
- **Markdown research brief / Markdown 研究简报**: copy a portable report with question, likely explanation, reasons, challenge coverage, evidence, and source trace.
- **Copy fallback / 复制降级**: if browser clipboard permissions block one-click copy, the app opens a manual-copy report text area so the result is still portable.
- **Specific live graph labels / 具体的 Live 图谱标签**: live causal-map notes keep the model's specific reason labels instead of collapsing untranslated nodes into generic factor names.
- **Source health summary / 来源健康摘要**: the readable brief summarizes checked sources, stable-source coverage, failed sources, and result hits before users trust the answer.
- **Challenge coverage / 反证覆盖**: checked edges show whether refuting or context evidence was found; if a checked edge has no attached refuting evidence, the brief says that directly instead of showing ambiguous `0 challenge` wording. 已检查的因果边会说明是否找到反证或上下文证据；如果某条边没有附着反证证据，简报会直接说明，而不是显示容易误读的 `0 challenge`。
- **Source trace / 来源轨迹**: each live run shows which sources were queried and how many results were found.
- **Provider preflight / 模型预检**: test whether the selected model and API key can return valid JSON before running a full analysis.
- **Value harness / 结果价值检查**: the UI tells you whether a result is ready for review, needs more evidence, or is blocked by provider/model setup.
- **Demo transparency / Demo 透明标记**: demo, partial-live, and live modes are labeled explicitly.

## Current Status / 当前状态

**English:** RetroCause is a research-grade alpha published as `v0.1.0-alpha.4` at [github.com/logi-cmd/retrocause-ai](https://github.com/logi-cmd/retrocause-ai). The browser app, API, tests, provider preflight, challenge coverage, Markdown research brief, copy fallback, source-health summary, and value harness are working locally. A live golden-case run for the US/Iran Islamabad talks query passed on 2026-04-14 with OpenRouter DeepSeek V3.

**中文：** RetroCause 当前是 research-grade alpha，已在 [github.com/logi-cmd/retrocause-ai](https://github.com/logi-cmd/retrocause-ai) 发布 `v0.1.0-alpha.4`。本地浏览器应用、API、测试、模型预检、反证覆盖、Markdown 研究简报、复制降级、来源健康摘要和结果价值检查已经可用。2026-04-14 使用 OpenRouter DeepSeek V3 跑通了“美国和伊朗在伊斯兰堡谈判结束，未达成协议的原因是什么”这个 live golden case。

Known limits / 已知限制：

- Results are evidence-grounded explanations, not verified causal truth.
- Live quality depends on source availability, model behavior, and API quota.
- Some generated labels may remain partly English in Chinese mode, but live graph nodes should keep their specific meaning instead of falling back to generic factor labels.
- PDF/export/share/team workflows are not included yet.
- OSS report output is a copyable Markdown research brief. Higher-end PDF, team, scheduled, and branded workflows belong in a future Pro tier.

- 结果是“有证据锚定的解释”，不是已经被证明的因果真理。
- Live 模式质量取决于来源可用性、模型行为和 API 额度。
- 中文模式下，部分模型生成的长标签可能仍保留英文，但 Live 因果图节点应保留具体含义，而不是退回成泛化的“因素”标签。
- 当前还没有 PDF 导出、分享、团队工作流。
- OSS 报告输出现在是可复制的 Markdown 研究简报。PDF、团队协作、定时生成、品牌模板等更适合未来 Pro 版本。

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

打开首页，不填 API key 直接提交问题。RetroCause 会显示明确标记的 demo 输出，你可以先体验交互和证据墙。

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
4. If preflight passes, click **Start analysis**.
5. Inspect the analysis brief, source trace, challenge coverage, and value harness before trusting the result.
6. Click **Copy report** in the readable brief card to take the Markdown report into notes, docs, or research workflows. If the browser blocks clipboard access, use the manual-copy report box that appears.

中文步骤：

1. 打开首页左侧的 **模型与密钥设置**。
2. 粘贴你的 OpenRouter API key。
3. 点击 **运行模型预检**。
4. 预检通过后点击 **开始分析**。
5. 先检查分析简报、来源轨迹、反证覆盖和 Value Harness，再决定是否相信结果。
6. 在分析结论卡片中点击 **复制报告**，把结果带进笔记、文档或研究流程。如果浏览器拦截剪贴板权限，请使用自动展开的手动复制文本框。

API keys are only needed for real analysis. Without a key, the app remains usable in demo mode.

真实分析需要 API key。没有 key 时，应用仍可用 demo 模式体验。

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
- Evidence sources: web search adapters, AP News, Federal Register, GDELT, ArXiv, Semantic Scholar

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

## OSS vs Pro Boundary / OSS 与 Pro 边界

**OSS:** local, inspectable analysis for individual researchers and builders. OSS should include the evidence board, source trace, challenge coverage, value harness, and a copyable Markdown research brief so users can take the result into their own notes or analysis workflow.

**Pro:** repeatable delivery workflows. Pro should justify payment through hosted runs, PDF/DOCX reports, team sharing, scheduled briefings, saved comparisons, source policy controls, domain packs, branded templates, and higher-trust operating workflows.

**中文：** OSS 版服务个人研究者和开发者，重点是本地可运行、可检查、可复制。OSS 应包含证据墙、来源轨迹、反证覆盖、结果价值检查，以及可复制的 Markdown 研究简报，方便用户放进自己的笔记、投研或政策分析流程。

**Pro：** Pro 版应该服务可重复交付的工作流，包括托管运行、PDF/DOCX 报告、团队分享、定时简报、历史对比、来源策略控制、垂直领域包、品牌模板和更高可信的运营能力。

## License / 许可证

MIT
