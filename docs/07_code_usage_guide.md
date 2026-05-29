# 代码使用指南

本文档按任务说明当前 MiniMind + FIRE DSL 项目如何运行、输入输出是什么、如何判断成功。

默认服务器目录：
（换成代码实际存放地址即可）
```bash
cd ~/work/minimind-fire-project
```

## 1. 检查数据

用途：确认 FIRE DSL 训练集、评估集存在且格式可读。

输入：

```text
fire-dsl-data/train/*.jsonl
fire-dsl-data/eval/*.jsonl
```

命令：

```bash
python scripts/inspect_fire_dsl_data.py
```

成功标准：能看到 train/public/generalization 的数量统计，没有 JSON 解析错误。

## 2. 训练 baseline SFT

用途：得到没有 domain pretrain 的基础模型。

命令：

```bash
RUN_NAME=fire_dsl_baseline_e3 \
MODE=baseline_sft \
HIDDEN_SIZE=128 \
NUM_LAYERS=2 \
MAX_SEQ_LEN=512 \
BATCH_SIZE=2 \
LR=3e-4 \
EPOCHS=3 \
TEMPERATURE=0.1 \
bash scripts/run_experiment_pipeline.sh
```

输出：

```text
minimind/out/fire_dsl_baseline_e3_128.pth
logs/train_fire_dsl_baseline_e3.log
results/fire_dsl_baseline_e3_*_predictions.csv
```

成功标准：`results/summary_table.csv` 出现 `fire_dsl_baseline_e3`。

## 3. 训练 Domain Pretrain + SFT

用途：让模型先熟悉 FIRE DSL 领域文本，再学习自然语言到 DSL code block 的映射。

命令：

```bash
RUN_NAME=fire_dsl_domain_sft \
MODE=domain_pretrain_sft \
HIDDEN_SIZE=128 \
NUM_LAYERS=2 \
MAX_SEQ_LEN=512 \
PRETRAIN_BATCH_SIZE=4 \
BATCH_SIZE=2 \
PRETRAIN_LR=5e-4 \
LR=3e-4 \
PRETRAIN_EPOCHS=2 \
EPOCHS=3 \
TEMPERATURE=0.1 \
bash scripts/run_experiment_pipeline.sh
```

输出：

```text
minimind/out/fire_dsl_domain_sft_pretrain_128.pth
minimind/out/fire_dsl_domain_sft_128.pth
logs/train_fire_dsl_domain_sft*.log
```

成功标准：generalization executable 高于 baseline。

## 4. 跑 Batch Inference

用途：用指定权重对 eval 集生成预测。

命令示例：

```bash
python scripts/batch_fire_infer.py \
  --eval_jsonl fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl \
  --output_csv results/example_predictions.csv \
  --save_dir minimind/out \
  --weight fire_dsl_domain_sft \
  --hidden_size 128 \
  --num_hidden_layers 2 \
  --device cuda \
  --temperature 0.01
```

输出：

```text
results/example_predictions.csv
```

成功标准：CSV 中 `prediction` 列有模型输出。

## 5. 跑 Output Normalization

用途：把模型输出规范化为标准 fenced `dsl_fire` code block。

命令：

```bash
python scripts/normalize_fire_predictions.py \
  results/fire_dsl_domain_sft_t001_generalization_predictions.csv \
  results/fire_dsl_domain_sft_t001_norm_generalization_predictions.csv
```

成功标准：重新评分后 `fenced_code_format` 为 100%。

## 6. 跑 Verifier Reranking

用途：每个问题生成多个候选，用 FIRE DSL parser/executor 选择更合法的候选。

先生成 5 份候选：

```bash
mkdir -p results/rerank_candidates logs/rerank_candidates

for i in 1 2 3 4 5
do
  python scripts/batch_fire_infer.py \
    --eval_jsonl fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl \
    --output_csv results/rerank_candidates/domain_sft_t02_c${i}_generalization.csv \
    --save_dir minimind/out \
    --weight fire_dsl_domain_sft \
    --hidden_size 128 \
    --num_hidden_layers 2 \
    --device cuda \
    --temperature 0.2 \
    --top_p 0.95 \
    2>&1 | tee logs/rerank_candidates/domain_sft_t02_c${i}_generalization.log
done
```

再选择最优候选：

```bash
python scripts/select_best_fire_candidate.py \
  results/fire_dsl_domain_sft_rerank5_t02_generalization_predictions.csv \
  results/rerank_candidates/domain_sft_t02_c1_generalization.csv \
  results/rerank_candidates/domain_sft_t02_c2_generalization.csv \
  results/rerank_candidates/domain_sft_t02_c3_generalization.csv \
  results/rerank_candidates/domain_sft_t02_c4_generalization.csv \
  results/rerank_candidates/domain_sft_t02_c5_generalization.csv
```

成功标准：重新评分后 parse_ok 和 executable 明显高于单次推理。

## 7. 评分和错误分析

命令：

```bash
python scripts/score_fire_predictions.py results/xxx_predictions.csv \
  2>&1 | tee logs/xxx_score.log

python scripts/analyze_fire_errors.py results/xxx_predictions.csv results/xxx_errors.csv \
  2>&1 | tee logs/xxx_errors.log
```

关键指标：

```text
exact_dsl_match
fenced_code_format
python_parse_ok
fire_dsl_executable
```

报告主看：

```text
fire_dsl_executable
python_parse_ok
```

## 8. 生成报告图表

用途：从 `summary_table.csv` 自动生成 PPT 图表和讲稿。

命令：

```bash
python scripts/make_report_artifacts.py
```

输出：

```text
reports/figures/*.png
reports/tables/metrics_for_ppt.csv
reports/tables/metrics_for_ppt.md
reports/diagrams/*.mmd
reports/generated/experiment_summary_for_ppt.md
reports/generated/slide_storyboard.md
reports/experiment_report_summary.md
```

成功标准：

```text
reports/figures/ 下至少有 5 张 PNG。
reports/tables/metrics_for_ppt.csv 包含 fire_dsl_domain_sft_rerank5_t02。
reports/experiment_report_summary.md 中文正常且写明最佳 executable = 52.50%。
```

## 9. 上传 GitHub

推荐先检查：

```bash
git status
```

添加项目文件：

```bash
git add scripts results logs experiments reports docs HANDOFF.md PROJECT_README.md TODO_CHECKLIST.md
```

提交：

```bash
git commit -m "Add report artifacts and handoff docs"
```

推送前同步远程：

```bash
git pull --rebase origin server-experiments
```

推送：

```bash
git push -u origin server-experiments
```

不要上传大权重和临时缓存。确认 `.gitignore` 包含：

```text
*.pth
*.pt
*.bin
*.safetensors
minimind/out/
```
