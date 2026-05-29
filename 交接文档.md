# MiniMind + FIRE DSL 项目交接说明

## 1. 当前项目做到哪里了

本项目已经完成从 MiniMind 小型 LLM 训练流程复现，到 FIRE DSL 垂直领域数据训练、推理、自动评估和多轮优化的主线工作。

当前已经跑通：

- FIRE DSL 数据检查和评估集转换。
- MiniMind baseline SFT。
- FIRE DSL domain pretrain + SFT。
- temperature 推理参数对比。
- output normalization 后处理。
- verifier reranking：多候选生成 + FIRE DSL parser/executor 筛选。
- public / generalization 两套评估。
- 自动保存 predictions、score logs、error analysis 和 summary table。

## 2. 当前最佳实验

当前最佳 generalization 方案：

```text
fire_dsl_domain_sft_rerank5_t02
```

关键指标：

```text
Exact DSL Match: 0.00%
Fenced Code Format: 100.00%
Python Parse OK: 76.33%
FIRE DSL Executable: 52.50%
```

与 baseline 对比：

```text
baseline_e3 generalization executable: 26.17%
rerank5_t02 generalization executable: 52.50%
```

结论：domain pretrain 改善模型对 FIRE DSL 的基础学习；normalization 消除格式错误；verifier reranking 是目前最有效的推理阶段优化。

## 3. 重要结果在哪里

核心总表：

```text
results/summary_table.csv
```

PPT 可用图表：

```text
reports/figures/
```

PPT 表格：

```text
reports/tables/metrics_for_ppt.csv
reports/tables/metrics_for_ppt.md
```

流程图：

```text
reports/diagrams/
```

汇报讲稿和总结：

```text
reports/experiment_report_summary.md
reports/generated/experiment_summary_for_ppt.md
reports/generated/slide_storyboard.md
```

## 4. 重要脚本分别干什么

```text
scripts/inspect_fire_dsl_data.py
```
检查 FIRE DSL 数据文件数量、字段和格式。

```text
scripts/batch_fire_infer.py
```
对 eval JSONL 批量推理，生成 predictions CSV。

```text
scripts/score_fire_predictions.py
```
计算 exact match、format、parse ok、FIRE DSL executable。

```text
scripts/analyze_fire_errors.py
```
分析错误类型，输出 format_error、parse_error、execution_error、semantic_mismatch 等。

```text
scripts/normalize_fire_predictions.py
```
把模型输出规范化成标准 `dsl_fire` code block。

```text
scripts/select_best_fire_candidate.py
```
从多个候选 CSV 中选择 parse/executable 最好的候选，用于 verifier reranking。

```text
scripts/run_fire_eval.sh
```
统一执行 batch inference、score、error analysis、append summary。

```text
scripts/run_experiment_pipeline.sh
```
自动跑 baseline 或 domain_pretrain_sft 训练并评估。

```text
scripts/make_report_artifacts.py
```
生成 PPT 图表、Mermaid 流程图、汇报摘要、逐页 storyboard 和指标表。

## 5. 队友如果要继续实验，从哪里开始

如果有代码改动，请在git上新建分支。

优先方向：curriculum learning 或语义对齐数据增强。

当前 reranking 后的主要问题是：

```text
semantic_mismatch
```

也就是模型生成的 DSL 往往合法可执行，但不一定与题目语义一致。

建议下一步：

```text
1. 把 SFT 数据按 DSL 复杂度拆分为 simple / medium / hard。
2. 从 domain pretrain 权重开始，按 simple -> medium -> full 训练。
3. 对 curriculum 模型再做 verifier reranking。
4. 和 fire_dsl_domain_sft_rerank5_t02 的 52.50% executable 对比。
```

## 6. 不要随便动的文件

不要上传或随便删除大模型权重：

```text
minimind/out/
*.pth
*.pt
*.bin
*.safetensors
```

## 7. 汇报前最后一步

运行：

```bash
python scripts/make_report_artifacts.py
```

然后重点查看：

```text
reports/figures/01_generalization_metrics_bar.png
reports/figures/02_executable_progress.png
reports/figures/03_error_rows_stacked.png
reports/generated/slide_storyboard.md
```
