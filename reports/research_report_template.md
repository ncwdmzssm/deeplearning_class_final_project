# MiniMind FIRE Operator DSL 垂直领域训练报告

## 1. 项目背景

TODO：说明课程任务、MiniMind 项目定位、FIRE operator DSL 的任务意义。

本项目目标：

```text
自然语言金融因子想法 -> fenced dsl_fire code block
```

## 2. 参考资料和学习路线

TODO：说明如何使用 `learn-minimind` 理解 MiniMind。

建议写入：

- L05 Tokenizer：解释 DSL 字段/算子如何变成 token。
- L11 数据处理：解释 JSONL 到 Dataset。
- L12 Pretrain：解释领域继续预训练。
- L13 SFT：解释 assistant loss mask。
- L14 LoRA：解释低成本微调。
- L20 推理优化：解释 batch inference。

## 3. MiniMind 代码理解

### 3.1 Tokenizer

TODO：说明 tokenizer 和 chat template。

### 3.2 Dataset

TODO：说明 `SFTDataset` 如何构造 `input_ids` 和 `labels`。

### 3.3 Loss Mask

TODO：说明 user/system/padding 为什么是 `-100`。

### 3.4 Model

TODO：说明 embedding、attention、feed-forward、logits、loss。

### 3.5 Training

TODO：说明 `train_full_sft.py`、`train_pretrain.py`、`train_lora.py` 的角色。

## 4. FIRE DSL 数据

| 文件 | 数量 | 用途 |
|---|---:|---|
| `fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl` | 10049 | 默认 SFT 训练 |
| `fire-dsl-data/train/fire_operator_dsl_pretrain_domain.jsonl` | 7262 | 领域继续预训练 |
| `fire-dsl-data/eval/fire_operator_dsl_eval_code_public.jsonl` | 2000 | seen-style 评估 |
| `fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl` | 600 | held-out 泛化评估 |

标准输出：

````text
```dsl_fire
result = div(sub(close, open), open)
```
````

## 5. Baseline 实验

TODO：填写训练配置。

| 配置项 | 值 |
|---|---|
| weight | TODO |
| hidden_size | TODO |
| num_hidden_layers | TODO |
| max_seq_len | TODO |
| batch_size | TODO |
| learning_rate | TODO |
| epochs | TODO |
| device | TODO |

TODO：放训练 loss、checkpoint、样例输出。

## 6. 优化实验

至少完成一个：

| 优化方向 | 实验目的 | 是否完成 |
|---|---|---|
| Domain pretrain + SFT | 让模型先熟悉 FIRE DSL 领域文本 | TODO |
| LoRA SFT | 降低显存和训练成本 | TODO |
| 超参数对比 | 找到更稳配置 | TODO |
| Reasoning SFT | 分析 reasoning 是否帮助算子选择 | TODO |
| Tokenizer 分析 | 解释 DSL tokenization 难点 | TODO |

## 7. 自动评估

### Public Seen-Style Eval

| 模型 | Exact DSL Match | Code Format | Parse OK | FIRE Executable |
|---|---:|---:|---:|---:|
| Baseline | TODO | TODO | TODO | TODO |
| 优化模型 | TODO | TODO | TODO | TODO |

### Held-Out Generalization Eval

| 模型 | Exact DSL Match | Code Format | Parse OK | FIRE Executable |
|---|---:|---:|---:|---:|
| Baseline | TODO | TODO | TODO | TODO |
| 优化模型 | TODO | TODO | TODO | TODO |

## 8. 错误分析

TODO：整理至少 20 条 generalization 样例。

| 错误类型 | 数量 | 例子 | 原因 |
|---|---:|---|---|
| format_error | TODO | TODO | TODO |
| parse_error | TODO | TODO | TODO |
| execution_error | TODO | TODO | TODO |
| semantic_mismatch | TODO | TODO | TODO |
| legacy_token_error | TODO | TODO | TODO |

## 9. 总结

TODO：总结学到的 MiniMind 训练流程、哪种优化有效、为什么 generalization 更重要、后续如何改进。

