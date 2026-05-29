# Generalization 指标对比

- Domain pretrain 明显提升输出格式和基础 DSL 生成能力。
- Normalization 把格式正确率推到 100%，但不改变表达式语义。
- Verifier reranking 同时提升 Parse OK 和 FIRE DSL Executable，是当前最有效优化。
