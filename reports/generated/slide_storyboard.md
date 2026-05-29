# PPT 逐页讲稿 Storyboard

## 1. 项目目标
- 放图：FIRE DSL 任务示例。
- 结论：本项目不是做大模型性能竞赛，而是复现小型 LLM 的训练、推理和评估流程。
- 讲稿：我们用 MiniMind 学习 LLM 从数据到 loss 再到生成结果的完整链路，并把它应用到金融因子 DSL 生成任务。

## 2. MiniMind 小模型复现训练流程
- 放图：`reports/diagrams/01_data_model_loss_eval_flow.mmd`。
- 结论：MiniMind 把 JSONL 对话数据转成 token，再通过 Transformer 预测下一个 token。
- 讲稿：这个流程覆盖 tokenizer、dataset、model、loss、optimizer、checkpoint 和 inference。

## 3. FIRE DSL 数据任务
- 放图：一条输入 prompt 和 expected DSL 示例。
- 结论：任务目标是把自然语言金融因子想法生成 `dsl_fire` 代码块。
- 讲稿：输出不仅要像代码，还必须能被 FIRE DSL parser/executor 解析和执行。

## 4. 数据流与 SFT Loss
- 放图：`reports/diagrams/02_sft_loss_flow.mmd`。
- 结论：SFT 看完整上下文，但主要监督 assistant 回复部分。
- 讲稿：system/user/padding 的 label 通常被设成 -100，cross entropy 会忽略这些位置。

## 5. Baseline 实验
- 放图：`reports/figures/02_executable_progress.png`。
- 结论：baseline generalization executable 为 26.17%，说明基础流程跑通但泛化较弱。
- 讲稿：小模型能学到部分格式和函数，但复杂 DSL 组合经常失败。

## 6. Domain Pretrain 优化
- 放图：`reports/figures/01_generalization_metrics_bar.png`。
- 结论：domain pretrain 将 executable 提升到 35.67%。
- 讲稿：先让模型熟悉 FIRE DSL 的函数、字段和表达式，再做 SFT，有助于领域格式学习。

## 7. Normalization 优化
- 放图：`reports/figures/03_error_rows_stacked.png`。
- 结论：normalization 将 format error 清零，但 executable 没有明显提升。
- 讲稿：这说明格式问题可以工程化修复，但表达式语义仍要靠模型或 verifier。

## 8. Verifier Reranking 优化
- 放图：`reports/diagrams/03_optimization_pipeline.mmd` 和 `reports/figures/05_optimization_contribution.png`。
- 结论：reranking 将 generalization executable 提升到 52.50%。
- 讲稿：我们让模型生成 5 个候选，然后用 FIRE DSL 执行器筛出可解析、可执行的候选。

## 9. 结果对比图
- 放图：`reports/figures/01_generalization_metrics_bar.png`。
- 结论：当前最佳方案是 `fire_dsl_domain_sft_rerank5_t02`。
- 讲稿：它在 format、parse ok 和 executable 三个指标上都最稳定。

## 10. Public vs Generalization
- 放图：`reports/figures/04_public_vs_generalization.png`。
- 结论：public 更像 seen-style，generalization 更能反映 held-out 泛化。
- 讲稿：我们报告主结论以 generalization 为准。

## 11. 问题与下一步
- 放图：错误类型表或 `reports/figures/03_error_rows_stacked.png`。
- 结论：剩余瓶颈是 semantic_mismatch。
- 讲稿：reranking 能提升合法性，但不能保证语义完全匹配，下一步应做 curriculum learning 或语义对齐数据增强。

## 12. 总结
- 放图：`reports/figures/02_executable_progress.png`。
- 结论：我们复现了 MiniMind 训练流程，并验证了训练阶段和推理阶段优化的效果。
- 讲稿：最终可执行率从 26.17% 提升到 52.50%，说明小模型配合领域训练和外部 verifier 也能完成可解释的 DSL 生成优化。
