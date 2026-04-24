# RetroCause

**English:** Ask "why did this happen?" and inspect an evidence-backed causal map.

**中文：** 输入一个“为什么会这样？”的问题，查看带证据、反证检查、来源轨迹和不确定性提示的因果解释。

RetroCause is an open-source causal explanation workspace for complex events. It is not a truth oracle and it is not a production causal-inference system. Its goal is to make AI-assisted explanations inspectable: users can see proposed reasons, supporting evidence, challenge checks, uncertainty signals, and retrieval-source health instead of receiving one opaque paragraph.

RetroCause 是一个开源的因果解释工作台，用来研究复杂事件的“原因链”。它不是因果真理机器，也不是生产级科学因果推断系统。它的目标是让 AI 辅助解释更可检查：用户可以看到原因、证据、反证检查、不确定性和检索来源健康状态，而不是只看到一段不可追踪的总结。

![RetroCause evidence board](docs/images/readme-evidence-board-homepage.png)

## Current Status / 当前状态

RetroCause is currently a stable-deliverable local OSS alpha focused on inspectable causal analysis. It is ready to clone, run, and evaluate locally. It is not a hosted service, and it does not ask users to paste model or search credentials into the OSS browser/API surface.

RetroCause 目前是一个稳定可交付的本地 OSS alpha，重点是可检查的因果分析。它已经可以被 clone、启动并在本地评估使用。它不是托管服务，也不会在 OSS 浏览器/API 入口要求用户粘贴模型或搜索凭据。

The latest public GitHub release is still `v0.1.0-alpha.5`; see [`docs/oss-release-gate.md`](docs/oss-release-gate.md) for the non-alpha `v0.1.0` release bar.

当前公开 GitHub release 仍是 `v0.1.0-alpha.5`；非 alpha 的 `v0.1.0` 发布门槛见 [`docs/oss-release-gate.md`](docs/oss-release-gate.md)。

What works locally:

- FastAPI backend and Next.js browser app
- demo / local result labeling
- evidence-backed causal chains
- readable brief and copyable Markdown research brief
- challenge/refutation coverage
- SourceBroker retrieval trace with cached, rate-limited, source-limited, timeout, and source-error states
- scenario-aware brief modes for market, policy/geopolitics, and postmortem questions
- local run metadata, usage ledger, saved runs, and pasted uploaded evidence
- full local verification through `npm test`

本地已经可用：

- FastAPI 后端和 Next.js 浏览器应用
- demo / local 结果标记
- 带证据的因果链
- 可阅读简报和可复制 Markdown 研究简报
- 反证 / challenge coverage
- SourceBroker 来源轨迹，包括缓存、限流、来源受限、超时和来源错误等状态
- 面向市场、政策 / 地缘政治、复盘问题的场景化简报
- 本地 run metadata、usage ledger、saved runs、粘贴式 uploaded evidence
- 通过 `npm test` 的完整本地验证

Known limits:

- Results are evidence-grounded explanations, not verified causal truth.
- The OSS browser/API surface is keyless. Hosted model/search execution belongs to the separate Rust Pro line.
- Source trace rows describe retrieval health. They are not evidence for or against a cause by themselves.
- Saved runs and uploaded evidence are local OSS features. They are not hosted storage, team sharing, ACLs, or secure document management.
- PDF/DOCX export, scheduled watch topics, team review, branded reports, and hosted queues are not part of the OSS release.
- Some generated labels may remain partly English in Chinese mode, but live graph nodes should keep their specific meaning.

已知限制：

- 结果是“证据锚定的解释”，不是已经被证明的因果真理。
- OSS 浏览器/API 入口是 keyless 的；托管模型/搜索执行属于独立 Rust Pro 线。
- 来源轨迹描述的是检索健康状态，它本身不是支持或反驳某个原因的证据。
- saved runs 和 uploaded evidence 是本地 OSS 功能，不是托管存储、团队共享、ACL 或安全文档管理。
- PDF/DOCX 导出、定时主题、团队审阅、品牌化报告、托管队列不属于当前 OSS alpha。
- 中文模式下，部分模型生成的长标签可能仍保留英文，但 graph 节点应保留具体含义。

## Quick Start / 快速开始

### 1. Install / 安装

Use Python 3.10+ and Node.js. From the repository root:

```bash
pip install -e ".[dev]"
npm install
npm --prefix frontend install
```

使用 Python 3.10+ 和 Node.js。在仓库根目录执行：

```bash
pip install -e ".[dev]"
npm install
npm --prefix frontend install
```

### 2. Start / 启动

```bash
python start.py
```

Open:

- Frontend: `http://127.0.0.1:3005`
- Backend API: `http://127.0.0.1:8000`

打开：

- 前端：`http://127.0.0.1:3005`
- 后端 API：`http://127.0.0.1:8000`

### 3. Try Local Analysis / 运行本地分析

Submit a question from the homepage. RetroCause returns a clearly labeled local/demo result so you can inspect the interface, evidence board, source trace, and causal chains safely.

在首页提交问题。RetroCause 会返回明确标记的 local/demo 结果，方便你安全检查界面、证据墙、来源轨迹和因果链。

Example questions:

- Why did SVB collapse?
- Why did the 2008 financial crisis happen?
- Why is rent so high in New York?
- Why did Bitcoin move today?
- Why did a SaaS product launch fail to convert trial users?

示例问题：

- SVB 为什么倒闭？
- 2008 年金融危机的原因是什么？
- 纽约房租为什么这么高？
- 比特币今天为什么波动？
- 一个 SaaS 产品发布后为什么没能把试用用户转成付费用户？

Recommended flow:

1. Choose **Auto detect**, **Market / Investment**, **Policy / Geopolitics**, or **Postmortem**.
2. For a Chinese A-share smoke test, click the sample query button; it fills the query and selects **Market / Investment**.
3. Click **Start analysis**.
4. Inspect the production brief, analysis brief, source trace, challenge coverage, and value harness before trusting the result.
5. Use **Copy report** to export the Markdown research brief.

建议流程：

1. 选择 **Auto detect**、**Market / Investment**、**Policy / Geopolitics** 或 **Postmortem**。
2. 如果要做中文 A 股 smoke test，点击示例问题按钮；它会填入问题并选择 **Market / Investment**。
3. 点击 **Start analysis**。
4. 先检查 production brief、analysis brief、source trace、challenge coverage 和 value harness，再决定是否信任结果。
5. 使用 **Copy report** 导出 Markdown 研究简报。

## Model And Search Boundary / 模型与搜索边界

The OSS repository contains no provider secrets, and the OSS UI does not expose credential fields. OpenRouter is deprecated and no longer part of the supported OSS provider surface.

OSS 仓库不包含 provider secret，OSS UI 也不暴露凭据输入框。OpenRouter 已弃用，不再属于受支持的 OSS provider surface。

Future hosted model/search execution should live in the separate full-stack Rust Pro implementation, where credentials, quotas, queues, and billing can be designed deliberately.

未来托管模型/搜索执行应放在独立的全栈 Rust Pro 实现中，这样凭据、配额、队列和计费才能被认真设计。

## Local Workflow Features / 本地工作流功能

The OSS release includes small local workflow features because they make inspection easier:

- Run status: every V2 analysis response includes a local `run_id`, status, run steps, and usage ledger.
- Saved runs: recent run payloads can be reopened from the browser UI.
- Uploaded evidence: pasted notes can be stored locally and reused as user-provided evidence.

OSS 版本包含一些小型本地工作流功能，因为它们能让检查过程更清楚：

- Run status：每个 V2 分析响应包含本地 `run_id`、状态、步骤和 usage ledger。
- Saved runs：最近的运行结果可以在浏览器 UI 中重新打开。
- Uploaded evidence：用户粘贴的笔记可以存入本地 evidence store，作为用户提供的证据复用。

These are local inspectability features. They are not hosted Pro infrastructure.

这些是本地可检查性功能，不是 hosted Pro 基础设施。

## API Usage / API 用法

Run the backend with `python start.py`, then call:

```bash
curl -X POST http://127.0.0.1:8000/api/analyze/v2 \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Why did SVB collapse?\"}"
```

Useful local endpoints:

- `POST /api/analyze/v2`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `POST /api/evidence/upload`

Windows PowerShell note: for Chinese queries, send UTF-8 JSON bytes. Plain string request bodies can corrupt Chinese text on some Windows consoles.

Windows PowerShell 注意：中文问题建议发送 UTF-8 JSON bytes。某些 Windows 控制台直接发送字符串 body 时，中文可能被破坏。

## Development / 开发验证

Run the full local verification suite:

```bash
npm test
```

This covers frontend lint/build, backend lint, pytest, and the browser E2E smoke path.

这会覆盖前端 lint/build、后端 lint、pytest，以及浏览器 E2E smoke path。

## When To Use It / 适用场景

RetroCause is useful when a user needs to explain an event and inspect the reasoning path:

- market or policy event explanations
- Chinese A-share intraday questions such as `芯原股份今天盘中为什么下跌？`
- geopolitical/news causal briefings
- company or competitor postmortems
- research demos for evidence-grounded explanation UX

RetroCause 适合需要“解释事件原因，并检查推理链”的场景：

- 市场或政策事件解释
- 中文 A 股盘中问题，例如 `芯原股份今天盘中为什么下跌？`
- 地缘政治 / 新闻因果简报
- 公司或竞品复盘
- 证据锚定解释 UX 的研究 demo

## OSS vs Future Pro / OSS 与未来 Pro

**OSS:** local, inspectable analysis for individual researchers and builders. OSS includes the evidence board, source trace, challenge coverage, value harness, scenario-aware single-run briefs, local saved runs, pasted uploaded evidence, and a copyable Markdown research brief.

**Future Pro:** a separate full-stack Rust product. Pro should focus on hosted reliability, durable queues, workspace storage, exports, scheduled watch topics, review workflows, source-policy controls, and a redesigned knowledge-graph-first frontend.

**OSS：** 面向个人研究者和开发者，重点是本地可运行、可检查、可复制。OSS 包含证据墙、来源轨迹、反证覆盖、value harness、场景化单次简报、本地 saved runs、粘贴式 uploaded evidence、可复制 Markdown 研究简报。

**未来 Pro：** 独立全栈 Rust 产品。Pro 重点是托管可靠性、持久队列、工作区存储、导出、定时主题、审阅流程、来源策略控制，以及重新设计的知识图谱优先前端。

## License / 许可证

MIT
