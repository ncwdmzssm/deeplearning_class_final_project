# CoT 加强方案：Operator-Arity-Aware Structured CoT

## 优化目标

上一版 `mixed structured CoT` 使用固定槽位：

```text
字段 / 算子 / 窗口 / 方向
```

这能减少自由推理对 `dsl_fire` 输出的污染，但它没有直接约束当前错误里最关键的部分：

- 幻觉函数名，例如拼出不存在的 `ts_regggmax`。
- 函数参数数量错误。
- code block 标签或 `<think>` 残留污染最终答案。
- CoT 分支单独可执行率不高，只能作为 fusion 的辅助候选。

因此本轮把 CoT 从“语义解释”进一步压缩成“DSL 合法性检查”。新的训练目标是让模型在最终代码块前显式检查：

```text
字段 / 算子 / 参数 / 窗口或常数 / 合法性 / 方向
```

其中 `参数` 来自 `fire-dsl-data/tools/fire_operator_dsl.py` 中真实函数签名。例如：

```text
参数: ts_prod: 2/1-2 OK；add: 2/2 OK；pct_change: 2/1-2 OK
合法性: 仅使用已知 FIRE 算子，参数数量匹配
```

## 已完成代码改动

- `scripts/build_structured_cot_dataset.py`
  - 新增 `--cot_style arity`。
  - 从 `fire_operator_dsl.py` 静态解析 `OPERATOR_SPECS` 和函数签名。
  - 从最终 DSL 表达式中提取字段、算子、数值常量、方向和参数个数。
  - 构造 operator-arity-aware CoT 样本。
- `scripts/extract_first_dsl_block.py`
  - 增强对 `dsl_ffire`、`dsl_fireire`、`</think>`、额外解释文本的清洗。
  - 在没有完整 code block 时，尝试从文本中抽取第一个 DSL 函数表达式并包装成标准 fenced code block。
- `scripts/batch_fire_rerank_infer.py`
  - rerank 前使用同一套增强提取逻辑。
  - 候选评分继续遵循 `executable > parseable > fenced > shorter`。
- `scripts/combine_prediction_csvs.py`
  - fusion 前先规范化 primary/secondary prediction。
  - 输出最终选择样本时写入规范化后的 fenced `dsl_fire` block。

## 已生成数据

```text
fire-dsl-data/train/fire_operator_dsl_sft_structured_cot_arity_codeblock.jsonl  8049
fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_90_10.jsonl           11166
fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_80_20.jsonl           12562
fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_70_30.jsonl           14356
```

三组 mixed 数据对应 CoT 消融比例：

| 数据集 | plain SFT | arity-aware CoT | 目的 |
|---|---:|---:|---|
| `arity_90_10` | 90% | 10% | 最保守，优先保护输出格式 |
| `arity_80_20` | 80% | 20% | 对齐上一版 mixed CoT 比例 |
| `arity_70_30` | 70% | 30% | 测试更强 CoT 信号是否再次污染输出 |

已通过：

```bash
python3 scripts/validate_jsonl.py \
  fire-dsl-data/train/fire_operator_dsl_sft_structured_cot_arity_codeblock.jsonl \
  fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_90_10.jsonl \
  fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_80_20.jsonl \
  fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_70_30.jsonl
```

## 推荐训练顺序

先训练最保守的 10% CoT：

```bash
cd /home/student/work/deeplearning_class_final_project/minimind/trainer

python train_full_sft.py \
  --data_path ../../fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_arity_90_10.jsonl \
  --epochs 3 \
  --batch_size 2 \
  --learning_rate 3e-4 \
  --num_workers 0 \
  --device cuda:0 \
  --dtype float16 \
  --hidden_size 128 \
  --num_hidden_layers 2 \
  --max_seq_len 512 \
  --from_weight fire_dsl_domain_pretrain \
  --save_dir ../out \
  --save_weight fire_dsl_domain_mixed_cot_arity_90_10 \
  2>&1 | tee ../../logs/train_fire_dsl_domain_mixed_cot_arity_90_10.log
```

如果 `arity_90_10` 的 extract/rerank 结果超过旧版 `mixed_cot_80_20`，再训练 `arity_80_20`；只有当 `arity_80_20` 没有明显格式污染时，再训练 `arity_70_30`。

## 推荐评估顺序

每个权重先跑 raw，再跑 extract，再跑 rerank smoke：

```bash
python scripts/batch_fire_infer.py \
  --eval_jsonl fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl \
  --output_csv results/fire_dsl_domain_mixed_cot_arity_90_10_generalization_raw_predictions.csv \
  --weight fire_dsl_domain_mixed_cot_arity_90_10 \
  --hidden_size 128 \
  --num_hidden_layers 2 \
  --temperature 0.01

python scripts/extract_first_dsl_block.py \
  --input_csv results/fire_dsl_domain_mixed_cot_arity_90_10_generalization_raw_predictions.csv \
  --output_csv results/fire_dsl_domain_mixed_cot_arity_90_10_generalization_extract_predictions.csv

python scripts/score_fire_predictions.py \
  results/fire_dsl_domain_mixed_cot_arity_90_10_generalization_extract_predictions.csv
```

如果 extract 结果有提升，再跑完整 rerank：

```bash
python scripts/batch_fire_rerank_infer.py \
  --eval_jsonl fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl \
  --output_csv results/fire_dsl_domain_mixed_cot_arity_90_10_generalization_rerank5_t02_predictions.csv \
  --weight fire_dsl_domain_mixed_cot_arity_90_10 \
  --hidden_size 128 \
  --num_hidden_layers 2 \
  --temperature 0.2 \
  --top_p 0.95 \
  --num_candidates 5
```

## 最终融合

如果新的 arity-aware CoT 分支在部分样本上优于 `domain_sft_rerank5_t02`，继续使用 verifier fusion：

```bash
python scripts/combine_prediction_csvs.py \
  --primary_csv results/fire_dsl_domain_sft_rerank5_t02_generalization_predictions.csv \
  --secondary_csv results/fire_dsl_domain_mixed_cot_arity_90_10_generalization_extract_predictions.csv \
  --output_csv results/fire_dsl_hybrid_domain_rerank_plus_cot_arity_90_10_generalization_predictions.csv \
  --primary_tag domain_rerank \
  --secondary_tag cot_arity_90_10_extract
```

最终报告中要对比：

```text
domain_sft
domain_sft_rerank5_t02
old mixed_cot_extract
arity-aware mixed_cot_extract
hybrid_domain_rerank_plus_cot
hybrid_domain_rerank_plus_cot_arity
```

判断标准优先级：

```text
generalization fire_dsl_executable > public fire_dsl_executable > python_parse_ok > fenced_code_format
```
