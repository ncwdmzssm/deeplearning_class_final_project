# 展示 PPT 大纲

本文件是汇报排版用简版提纲；更详细的逐页讲稿见：

```text
reports/generated/slide_storyboard.md
```

## 1. 项目目标

- 讲清 MiniMind 小型 LLM 的训练、推理、评估流程。
- 把 MiniMind 应用于 FIRE DSL 金融因子代码生成。
- 通过 baseline、domain pretrain、normalization、verifier reranking 做优化对比。

建议素材：FIRE DSL 输入输出样例。

## 2. MiniMind 小模型复现训练流程

建议放图：

```text
reports/diagrams/01_data_model_loss_eval_flow.mmd
```

核心链路：

```text
JSONL 数据 -> chat template -> tokenizer -> input_ids / labels -> Transformer -> logits -> loss -> optimizer -> checkpoint -> inference -> evaluation
```

## 3. FIRE DSL 数据任务

任务定义：自然语言金融因子想法转成标准 `dsl_fire` 代码块。

标准输出：

````text
```dsl_fire
result = <合法 FIRE DSL 表达式>
```
````

## 4. SFT 数据流与 Loss

建议放图：

```text
reports/diagrams/02_sft_loss_flow.mmd
```

要点：

- 模型读取完整 conversation。
- system/user/padding 的 label 通常设为 `-100`。
- loss 主要监督 assistant 输出。
- cross entropy 使用 `ignore_index=-100` 忽略不监督位置。

## 5. Baseline 实验

建议放图：

```text
reports/figures/02_executable_progress.png
```

结论：baseline generalization executable 为 26.17%，说明基础流程跑通，但小模型泛化能力有限。

## 6. Domain Pretrain + SFT 优化

建议放图：

```text
reports/figures/01_generalization_metrics_bar.png
```

结论：domain pretrain 将 generalization executable 从 26.17% 提升到 35.67%。

## 7. Low-temperature Decoding 与 Normalization

建议放图：

```text
reports/figures/03_error_rows_stacked.png
```

结论：

- 低温推理小幅提升生成稳定性。
- normalization 将 format error 清零。
- 但 normalization 不改变 DSL 语义，所以 executable 没明显提升。

## 8. Verifier Reranking 优化

建议放图：

```text
reports/diagrams/03_optimization_pipeline.mmd
reports/figures/05_optimization_contribution.png
```

结论：5 候选生成 + FIRE DSL parser/executor 筛选，将 generalization executable 提升到 52.50%。

## 9. 总体结果对比

建议放图：

```text
reports/figures/01_generalization_metrics_bar.png
reports/tables/metrics_for_ppt.md
```

当前最佳方案：

```text
fire_dsl_domain_sft_rerank5_t02
```

核心结果：

```text
Format: 100.00%
Parse OK: 76.33%
Executable: 52.50%
```

## 10. Public vs Generalization

建议放图：

```text
reports/figures/04_public_vs_generalization.png
```

结论：public 用于 seen-style 检查，generalization 更能反映 held-out 泛化能力；报告主结论以 generalization 为准。

## 11. 错误分析与不足

建议放图：

```text
reports/figures/03_error_rows_stacked.png
```

剩余瓶颈：

```text
semantic_mismatch
```

解释：reranking 能提升合法性和可执行性，但不能保证语义完全匹配题目。

## 12. 总结与下一步

总结：

- 复现了 MiniMind 从数据到 loss 到推理评估的完整流程。
- 领域继续预训练证明有效。
- 输出规范化解决格式问题。
- verifier reranking 是当前最有效优化。

下一步：

- curriculum learning：simple -> medium -> hard DSL。
- 语义对齐数据增强。
- 针对 semantic_mismatch 做更细粒度评估。
