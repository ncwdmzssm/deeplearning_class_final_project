# 实验方案：MiniMind + FIRE DSL

## 实验 1：Baseline SFT

目标：验证原始 MiniMind SFT 流程能否学习 FIRE DSL code-block 生成。

训练数据：

```text
fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl
```

smoke test：

```powershell
cd minimind
python trainer\train_full_sft.py --data_path ..\fire-dsl-data\train\fire_operator_dsl_sft_code.jsonl --epochs 1 --batch_size 2 --num_workers 0 --device cuda:0 --hidden_size 128 --num_hidden_layers 2 --max_seq_len 512 --from_weight none --save_dir ..\out --save_weight fire_dsl_baseline
```

正式训练建议：

- 8GB GPU 先用 `hidden_size=128/256`、`num_hidden_layers=2/4`。
- 如果显存不足，降低 batch size，并用 accumulation steps。
- 完整训练不必追求大模型，课程重点是流程、优化和评估。

## 实验 2：Domain Pretrain + SFT

目标：验证领域继续预训练是否提升 FIRE DSL 泛化。

阶段 A：

```powershell
cd minimind
python trainer\train_pretrain.py --data_path ..\fire-dsl-data\train\fire_operator_dsl_pretrain_domain.jsonl --epochs 1 --batch_size 4 --num_workers 0 --device cuda:0 --hidden_size 128 --num_hidden_layers 2 --max_seq_len 512 --from_weight none --save_dir ..\out --save_weight fire_dsl_domain_pretrain
```

阶段 B：

```powershell
python trainer\train_full_sft.py --data_path ..\fire-dsl-data\train\fire_operator_dsl_sft_code.jsonl --epochs 1 --batch_size 2 --num_workers 0 --device cuda:0 --hidden_size 128 --num_hidden_layers 2 --max_seq_len 512 --from_weight fire_dsl_domain_pretrain --save_dir ..\out --save_weight fire_dsl_domain_sft
```

对比：`fire_dsl_baseline` vs `fire_dsl_domain_sft`。

## 实验 3：LoRA SFT

目标：在 8GB GPU 上用更低成本做垂直领域适配。

```powershell
cd minimind
python trainer\train_lora.py --data_path ..\fire-dsl-data\train\fire_operator_dsl_sft_code.jsonl --epochs 1 --batch_size 4 --num_workers 0 --device cuda:0 --hidden_size 128 --num_hidden_layers 2 --max_seq_len 512 --from_weight fire_dsl_baseline --save_dir ..\out --lora_name fire_dsl_lora
```

如果没有合适的 base weight，可把 LoRA 作为扩展实验，不作为最低完成要求。

## 实验 4：超参数对比

至少比较两组：

| 实验 | max_seq_len | learning_rate | epochs | 备注 |
|---|---:|---:|---:|---|
| baseline-a | 512 | 1e-5 | 1 | 保守配置 |
| baseline-b | 768 | 3e-5 | 1 | 更长上下文 |

评价只看训练 loss 不够，必须看 held-out generalization。

## 实验 5：Reasoning / Tokenizer 分析

Reasoning 数据：

```text
fire-dsl-data/train/fire_operator_dsl_sft_reasoning_short.jsonl
```

注意：该文件 assistant content 是裸 DSL，不是 fenced code block。若要作为正式优化，需要先转换格式，或单独作为分析实验。

Tokenizer 分析：

```powershell
python scripts\analyze_tokenizer_terms.py
```

报告中说明哪些字段/算子被拆得很碎，以及这对小模型学习 DSL 的影响。

## 推理和评估

```powershell
python scripts\batch_fire_infer.py --eval_jsonl fire-dsl-data\eval\fire_operator_dsl_eval_code_public.jsonl --output_csv results\fire_eval_public_predictions.csv --weight fire_dsl_baseline --hidden_size 128 --num_hidden_layers 2
python scripts\batch_fire_infer.py --eval_jsonl fire-dsl-data\eval\fire_operator_dsl_eval_code_generalization.jsonl --output_csv results\fire_eval_generalization_predictions.csv --weight fire_dsl_baseline --hidden_size 128 --num_hidden_layers 2
python scripts\score_fire_predictions.py results\fire_eval_public_predictions.csv
python scripts\score_fire_predictions.py results\fire_eval_generalization_predictions.csv
python scripts\analyze_fire_errors.py results\fire_eval_generalization_predictions.csv results\fire_eval_generalization_errors.csv
```

指标：

- Exact DSL Match
- Fenced Code Format
- Python Parse OK
- FIRE DSL Executable
- 人工评分和错误类型

