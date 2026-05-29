# PPT 指标表

| 方法 | Eval | Exact | Format | Parse OK | Executable | 说明 |
|---|---|---:|---:|---:|---:|---|
| Baseline SFT | generalization | 0.00% | 65.17% | 51.33% | 26.17% | baseline SFT 3 epochs |
| Domain Pretrain + SFT | generalization | 0.00% | 90.83% | 55.67% | 35.67% | domain pretrain 2 epochs then SFT 3 epochs |
| Low-temp Decoding | generalization | 0.00% | 91.83% | 55.67% | 37.17% | domain_sft inference temperature 0.01 |
| Output Normalization | generalization | 0.00% | 100.00% | 56.17% | 37.17% | domain_sft temperature 0.01 plus output normalization |
| Verifier Reranking | generalization | 0.00% | 100.00% | 76.33% | 52.50% | 5 candidates at temperature 0.2, select by parse/executable verifier |
| Larger Model 256/4 | generalization | 0.33% | 68.67% | 43.50% | 25.83% | domain_pretrain_sft auto pipeline |
| Baseline SFT | public | 13.40% | 35.70% | 29.40% | 21.60% | baseline SFT 3 epochs |
| Domain Pretrain + SFT | public | 19.05% | 90.20% | 64.65% | 45.70% | domain pretrain 2 epochs then SFT 3 epochs |
| Verifier Reranking | public | 21.15% | 100.00% | 77.05% | 55.05% | 5 candidates at temperature 0.2, select by parse/executable verifier |
| Larger Model 256/4 | public | 39.30% | 60.85% | 50.05% | 44.35% | domain_pretrain_sft auto pipeline |
