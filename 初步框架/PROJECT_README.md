# MiniMind + FIRE DSL 期末项目工作区

本项目主线：

```text
自然语言金融因子想法
-> MiniMind SFT / LoRA / domain pretrain
-> 输出 fenced dsl_fire 代码块
-> FIRE DSL 解析和执行校验
-> public / generalization 评估
```

正式课程数据目录是 `fire-dsl-data/`。早期 `data/finance_dsl_*` 只保留作入门样例，不用于正式实验。

## 核心材料

| 材料 | 用途 |
|---|---|
| `LLM_MIS2026.pptx` | 老师期末项目要求 |
| `MiniMind_Student_Guide.ipynb` | 课堂 MiniMind 教学 notebook |
| `minimind/` | MiniMind 官方源码 |
| `fire-dsl-data/` | 老师正式 FIRE operator DSL 数据包 |
| `docs/06_learn_minimind_route.md` | 结合 learn-minimind 的学习路线 |

参考学习仓库：

- https://github.com/bcefghj/learn-minimind
- https://github.com/bcefghj/learn-minimind/blob/main/docs/L13-%E7%9B%91%E7%9D%A3%E5%BE%AE%E8%B0%83SFT.md
- https://github.com/jingyaogong/minimind/blob/master/README_en.md

## 第一阶段：理解和检查

```powershell
python scripts\inspect_fire_dsl_data.py
python fire-dsl-data\tools\demo_verify_dsl.py
python scripts\analyze_tokenizer_terms.py
```

## 第二阶段：生成评估模板

```powershell
python scripts\make_fire_eval_csv.py fire-dsl-data\eval\fire_operator_dsl_eval_code_public.jsonl results\fire_eval_public_predictions.csv
python scripts\make_fire_eval_csv.py fire-dsl-data\eval\fire_operator_dsl_eval_code_generalization.jsonl results\fire_eval_generalization_predictions.csv
```

## 第三阶段：Baseline SFT

先用小配置 smoke test，确认训练链路能跑通：

```powershell
cd minimind
python trainer\train_full_sft.py --data_path ..\fire-dsl-data\train\fire_operator_dsl_sft_code.jsonl --epochs 1 --batch_size 2 --num_workers 0 --device cuda:0 --hidden_size 128 --num_hidden_layers 2 --max_seq_len 512 --from_weight none --save_dir ..\out --save_weight fire_dsl_baseline
```

如果显存不足，把 `--batch_size` 降为 1，或改用 `--device cpu` 只验证流程。

## 第四阶段：Batch Inference + 评估

```powershell
python scripts\batch_fire_infer.py --eval_jsonl fire-dsl-data\eval\fire_operator_dsl_eval_code_public.jsonl --output_csv results\fire_eval_public_predictions.csv --weight fire_dsl_baseline --hidden_size 128 --num_hidden_layers 2 --limit 50
python scripts\batch_fire_infer.py --eval_jsonl fire-dsl-data\eval\fire_operator_dsl_eval_code_generalization.jsonl --output_csv results\fire_eval_generalization_predictions.csv --weight fire_dsl_baseline --hidden_size 128 --num_hidden_layers 2 --limit 50
python scripts\score_fire_predictions.py results\fire_eval_public_predictions.csv
python scripts\score_fire_predictions.py results\fire_eval_generalization_predictions.csv
python scripts\analyze_fire_errors.py results\fire_eval_generalization_predictions.csv results\fire_eval_generalization_errors.csv
```

正式报告应去掉 `--limit 50`，跑完整 public 2000 条和 generalization 600 条。

## 推荐优化路线

优先级从高到低：

1. `domain pretrain + SFT`：先训练 `fire_operator_dsl_pretrain_domain.jsonl`，再 SFT。
2. `LoRA SFT`：适合 8GB 显存，训练成本低。
3. 超参数对比：`max_seq_len`、`learning_rate`、`epochs`。
4. Reasoning SFT 对比：需要注意输出格式，默认不直接混入 baseline。
5. Tokenizer 分析：作为报告中的解释性优化，不建议重训 tokenizer。

主评估以 `fire_operator_dsl_eval_code_generalization.jsonl` 为准；public eval 只作为 seen-style 格式检查。

