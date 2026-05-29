# 可执行率提升路径

- Baseline SFT 的 generalization 可执行率为 26.17%。
- Domain pretrain + SFT 提升到 35.67%，说明领域继续预训练有效。
- Verifier reranking 提升到 52.50%，说明外部 DSL 执行器能显著筛掉非法候选。
