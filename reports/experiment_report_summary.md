# 实验结果汇总

## 核心结论

- 当前 generalization 最优实验：`fire_dsl_domain_sft_t001`。
- FIRE DSL executable：37.17%。
- fenced code format：91.83%。
- python parse ok：55.67%。

## Generalization 指标对比

| 实验 | 优化方法 | Exact | Format | Parse OK | Executable | 备注 |
|---|---|---:|---:|---:|---:|---|
| `fire_dsl_baseline_e3` | full_sft | 0.00% | 65.17% | 51.33% | 26.17% | baseline SFT 3 epochs |
| `fire_dsl_domain_sft` | domain_pretrain_plus_sft | 0.00% | 90.83% | 55.67% | 35.67% | domain pretrain 2 epochs then SFT 3 epochs |
| `fire_dsl_domain_sft_t001` | domain_pretrain_plus_sft | 0.00% | 91.83% | 55.67% | 37.17% | domain_sft inference temperature 0.01 |
| `fire_dsl_domain_sft_t001_norm` | domain_pretrain_plus_sft_postprocess | 0.00% | 100.00% | 56.17% | 37.17% | domain_sft temperature 0.01 plus output normalization |
| `fire_dsl_domain_256_l4` | domain_pretrain_plus_sft | 0.33% | 68.67% | 43.50% | 25.83% | domain_pretrain_sft auto pipeline |

## 错误数量对比

| 实验 | Format Error | Parse Error | Execution Error |
|---|---:|---:|---:|
| `fire_dsl_baseline_e3` | 209 | 292 | 443 |
| `fire_dsl_domain_sft` | 55 | 266 | 386 |
| `fire_dsl_domain_sft_t001` | 49 | 266 | 377 |
| `fire_dsl_domain_sft_t001_norm` | 0 | 263 | 377 |
| `fire_dsl_domain_256_l4` | 188 | 339 | 445 |