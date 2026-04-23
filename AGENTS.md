# AGENTS.md — RetroCause

## 先阅读

1. `README.md`
2. `pyproject.toml`
3. 你计划修改的具体文件

## 工作方式

- 优先复用现有模式，不要轻易新建抽象。
- 保持改动小、易 review。
- 任务不简单时，先列出要改的文件。
- 推理步骤的每个输出必须有证据锚定，不得凭空给出因果结论。
- 概率值必须在 [0,1] 区间内。
- LLM 输出的因果结论必须附带来源或引用。

## 项目约定

- 语言: Python 3.10+
- 测试: pytest
- 依赖管理: pyproject.toml + pip
- 核心推理: NumPyro (JAX)
- 因果图: networkx + pgmpy
- LLM 调用: openai SDK

## 完成定义

- `pytest tests/` 通过
- `ruff check retrocause/` 通过
- 核心管道能跑通一个示例案例

<!-- agent-guardrails:start -->
# Agent 规则（强制执行，非可选）

## 强制：先阅读

写代码前，必须先阅读：

1. `AGENTS.md`（本文件）
2. `docs/PROJECT_STATE.md`
3. `README.md`
4. 你计划修改的具体文件

跳过此步骤 = 违反规则。

## 强制：完成前必须运行检查

**告诉用户"任务完成"之前，必须运行：**

```bash
agent-guardrails check --base-ref HEAD~1
```

**强制规则：**

- 如果发现问题 -> 必须停下修复。不要告诉用户"完成"。
- 如果没有问题 -> 在总结中包含检查结果。
- 如果命令不存在 -> 告诉用户先运行 `npx agent-guardrails setup`。

**不运行此命令 = 任务未完成。**

## 强制：任务契约

如果 `.agent-guardrails/task-contract.json` 存在：

- 必须停留在声明的范围内（允许的路径、预期的文件）。
- 必须运行契约中列出的所需命令。
- 必须更新 `.agent-guardrails/evidence/current-task.md`，写明执行过的命令、关键结果和残余风险。

如果契约不存在且任务不简单，必须先运行：

```bash
agent-guardrails plan --task "<任务描述>"
```

然后在生成的契约范围内实现。

## 强制：工作规则

- 必须优先复用现有模式，不要轻易新建抽象。
- 必须保持改动小、易 review。
- 必须任务不简单时，先列出要改的文件。
- 必须上下文不足时指出，不要自行脑补。
- 必须行为变化时补充或更新测试。

## 强制：完成定义

以下所有项都必须为真，才能报告完成：

- [ ] 实现符合当前项目约定。
- [ ] 行为变化在合适情况下具备测试覆盖。
- [ ] 任务要求的命令确实执行过，并且已经上报给 `check`。
- [ ] 当前任务的 evidence note 存在，并真实反映了任务结果。
- [ ] 风险、假设和后续工作已记录。

任何一项为假，任务未完成。

<!-- agent-guardrails:end -->
