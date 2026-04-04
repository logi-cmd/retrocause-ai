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
