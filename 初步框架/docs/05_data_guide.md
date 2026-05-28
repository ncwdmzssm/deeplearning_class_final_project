# 数据使用指南

## 结论

正式课程数据目录是：

```text
fire-dsl-data/
```

早期 `data/finance_dsl_*` 只是入门样例，不用于正式实验。

## 正式训练数据

| 文件 | 数量 | 用途 |
|---|---:|---|
| `fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl` | 10049 | 默认 SFT 训练集 |
| `fire-dsl-data/train/fire_operator_dsl_pretrain_domain.jsonl` | 7262 | 领域继续预训练 |
| `fire-dsl-data/train/fire_operator_dsl_sft_reasoning_short.jsonl` | 8049 | reasoning 扩展实验 |
| `fire-dsl-data/eval/fire_operator_dsl_eval_code_public.jsonl` | 2000 | seen-style 评估 |
| `fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl` | 600 | held-out 泛化评估 |

## 标准输出格式

````text
```dsl_fire
result = div(sub(close, open), open)
```
````

## 允许字段

```text
open, close, high, low, volume, vwap, pb, market_cap, industry
```

## 禁用旧名字

```text
rank
ts_returns
safe_div
open_price
pb_ratio
```

## 评估集如何使用

Public eval：

- 检查模型是否学会格式和常见映射。
- 与训练 DSL 有重叠，不能作为最终泛化结论。

Generalization eval：

- 检查模型是否能处理训练中没出现过的 DSL 组合。
- 报告中最重要。

## 生成评估 CSV

```powershell
python scripts\make_fire_eval_csv.py fire-dsl-data\eval\fire_operator_dsl_eval_code_public.jsonl results\fire_eval_public_predictions.csv
python scripts\make_fire_eval_csv.py fire-dsl-data\eval\fire_operator_dsl_eval_code_generalization.jsonl results\fire_eval_generalization_predictions.csv
```

