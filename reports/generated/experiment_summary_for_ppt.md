# 实验结果总结

## 核心结论

- 当前最佳 generalization 方案是 `fire_dsl_domain_sft_rerank5_t02`。
- FIRE DSL executable 从 baseline 的 26.17% 提升到 52.50%，绝对提升 26.33 个百分点。
- Domain pretrain 主要提升格式稳定性和基础 DSL 学习。
- Output normalization 消除格式错误，但不改变 DSL 表达式语义。
- Verifier reranking 显著提升 Parse OK 和 FIRE DSL Executable。
- 剩余瓶颈主要是 semantic_mismatch：模型能生成合法 DSL，但语义不一定与题目一致。

## Generalization 指标

| 方法 | Eval | Exact | Format | Parse OK | Executable |
|---|---|---:|---:|---:|---:|
| Baseline SFT | generalization | 0.00% | 65.17% | 51.33% | 26.17% |
| Domain Pretrain + SFT | generalization | 0.00% | 90.83% | 55.67% | 35.67% |
| Low-temp Decoding | generalization | 0.00% | 91.83% | 55.67% | 37.17% |
| Output Normalization | generalization | 0.00% | 100.00% | 56.17% | 37.17% |
| Verifier Reranking | generalization | 0.00% | 100.00% | 76.33% | 52.50% |
| Larger Model 256/4 | generalization | 0.33% | 68.67% | 43.50% | 25.83% |

## Public 指标

| 方法 | Eval | Exact | Format | Parse OK | Executable |
|---|---|---:|---:|---:|---:|
| Baseline SFT | public | 13.40% | 35.70% | 29.40% | 21.60% |
| Domain Pretrain + SFT | public | 19.05% | 90.20% | 64.65% | 45.70% |
| Verifier Reranking | public | 21.15% | 100.00% | 77.05% | 55.05% |
| Larger Model 256/4 | public | 39.30% | 60.85% | 50.05% | 44.35% |

## 优化方法解释

| 优化 | 对应流程位置 | 解决的问题 | 结果解释 |
|---|---|---|---|
| Domain Pretrain + SFT | 训练阶段 | 让模型先熟悉 FIRE DSL 语料，再学习自然语言到代码块映射 | generalization executable 从 26.17% 到 35.67% |
| Low-temperature Decoding | 推理阶段 | 降低随机性，让代码生成更稳定 | executable 小幅到 37.17% |
| Output Normalization | 推理后处理 | 修复 code block、`result =`、多余标签等格式问题 | format 到 100%，但 executable 不变 |
| Verifier Reranking | 推理阶段 + 外部校验 | 多候选生成后用 FIRE DSL parser/executor 选择可解析、可执行结果 | executable 到 52.50%，当前最有效 |
| Larger Model 256/4 | 模型容量 | 尝试扩大模型 | public exact 变高，但 generalization executable 下降，说明更大不一定更泛化 |

## 图表索引

- `reports/figures/01_generalization_metrics_bar.png`：三类核心指标对比。
- `reports/figures/02_executable_progress.png`：可执行率提升路径。
- `reports/figures/03_error_rows_stacked.png`：错误数量变化。
- `reports/figures/04_public_vs_generalization.png`：public 与 generalization 对比。
- `reports/figures/05_optimization_contribution.png`：优化贡献拆解。
