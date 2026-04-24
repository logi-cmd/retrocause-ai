# 技术参考 — 论文与框架

> Task 3 (反事实验证) 调研结果。更新于 2026-04-01。

## 核心论文

### 1. Executable Counterfactuals (2025)

- **作者**: Vashishtha, Dai, Mei, Sharma, Tan, Peng
- **来源**: arXiv:2510.01539
- **核心**: 通过代码执行实现 Pearl 反事实三步框架 (Abduction → Action → Prediction)
- **关键发现**: SOTA 模型在反事实推理上比干预推理低 25-40% 准确率
- **适用**: RetroCause 反事实验证模块的 A-A-P 执行引擎设计

### 2. Backtracking Counterfactuals (2023)

- **作者**: von Kügelgen, Mohamed, Beckers
- **来源**: CLeaR 2023, PMLR 213
- **核心**: 在 SCM 框架内形式化"反向追踪"反事实，不违反因果律
- **关键**: 传统 "小奇迹" 方法局部违反自然法则，backtracking 保持因果律不变
- **适用**: 从文献构建因果图时的反事实推理哲学基础

### 3. Abduct, Act, Predict (A2P) (2025)

- **作者**: West, Weng, Zhu et al.
- **来源**: arXiv:2509.10401
- **核心**: A2P 脚手架引导 LLM 完成故障归因
- **关键**: 将故障归因从"模式识别"重构为"结构化因果推理"，精度提升 2.85x
- **实现**: https://github.com/ResearAI/A2P
- **适用**: LLM 辅助反事实推理的具体实现参考

### 4. Sharp Bounds for Generalized Causal Sensitivity Analysis (2023)

- **作者**: Frauen, Melnychuk, Feuerriegel
- **来源**: NeurIPS 2023, arXiv:2305.16988
- **核心**: 广义因果敏感性分析，推导 ATE/CTE/中介分析的锐边界
- **关键**: 当无法精确识别因果效应时，提供边界范围
- **适用**: 无观测数据场景下的反事实不确定性量化

### 5. Language Models as Causal Effect Generators (2024)

- **作者**: Bynum, Cho
- **来源**: arXiv:2411.08019, EMNLP 2025
- **核心**: SD-SCM 框架，用户定义因果结构，LLM 定义因果机制
- **关键**: 直接处理"无数据"场景，用 LLM 生成反事实数据
- **适用**: 当文献证据不足以支撑完整 SCM 时的备选方案

### 6. Causal Inference in NLP (2022)

- **作者**: Feder, Keith, Manzoor et al.
- **来源**: ACL TACL
- **核心**: 系统性梳理 NLP 中因果推断的方法论
- **适用**: 文本作为因果中介场景的方法论参考

### 7. Zero-shot Causal Graph Extrapolation from Text via LLMs (2023)

- **作者**: Antonucci, Piqué, Zaffalon
- **来源**: arXiv:2312.14670
- **核心**: 零样本从文本推断因果关系
- **适用**: 因果发现阶段的增强参考

### 8. Partial Counterfactual Identification of Continuous Outcomes (2023)

- **作者**: Melnychuk, Frauen, Feuerriegel
- **来源**: NeurIPS 2023
- **核心**: 曲率敏感性模型处理连续结果的部分识别
- **适用**: 放宽可识别性假设的理论基础

## 实践框架

### DoWhy (PyWhy)

- **仓库**: https://github.com/py-why/dowhy (8k+ stars)
- **反事实模块**: `gcm.counterfactual_samples()`
- **关键**: 需要可逆 SCM (加性噪声模型) 来重建外生噪声值
- **我们可借鉴**: 噪声重建 + 反事实采样逻辑

### pgmpy — CausalInference

- **文档**: https://pgmpy.org/exact_infer/causal.html
- **关键**: 离散/连续变量反事实查询，基于贝叶斯网络和 SEM
- **我们可借鉴**: 项目已有 pgmpy 依赖但未使用

### CausalNex

- **关键**: `do_intervention()` + `weakly_connected_components` 检测断开子图
- **我们可借鉴**: 硬干预后的连通性分析

## Claude Code Framework 可借鉴模式

来源: https://github.com/anthropics/claude-code

| 模式 | 描述 | RetroCause 应用 |
|------|------|-----------------|
| Ralph Loop | 迭代自省循环，每轮发现新问题则继续 | 因果图迭代精炼 — 每轮反驳发现新假设 |
| Plugin Architecture | 可插拔模块结构 | 反事实方法可插拔 (do-calculus, SCM, 敏感性) |
| Confidence-Based Filtering | 评分 0-100，低于阈值过滤 | 因果声明确信度评分，低于阈值触发额外验证 |
| Settings Profiles | 不同模式配置 | 探索性 vs 确证性分析模式 |
| Rule-Based Guardrails | 声明式规则引擎 | 已实现 HookEngine，可扩展反事实规则 |

## 技术路线决策

### 为什么选择 A-A-P + 敏感性分析而非完整 SCM

1. **无观测数据**: 我们只有文献文本，没有可拟合 SCM 的数据
2. **文献本质**: 因果关系从文本中提取，精确参数值不可得
3. **实用性优先**: 提供边界比提供错误点估计更有价值
4. **可扩展**: 后续有数据时可升级到完整 SCM

### Task 3 实现方案

```
EvidenceAnchoring → [CounterfactualVerification] → DebateRefinement
                              ↓
                   1. Graph Surgery: 移除根因节点
                   2. Reachability Check: 结果是否仍可达
                   3. Probability Delta: 原始 vs 干预后路径概率
                   4. Sensitivity Bounds: 未观测混杂的锐边界
                   5. A-A-P via LLM: 文献中的反事实论证
```
