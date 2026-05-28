# MiniMind 源码阅读顺序

按下面顺序读，不要一开始就看所有文件。

## 1. `dataset/lm_dataset.py`

重点看：

- `PretrainDataset.__getitem__`
- `SFTDataset.create_chat_prompt`
- `SFTDataset.generate_labels`
- `SFTDataset.__getitem__`
- `DPODataset`

你需要回答：

- JSONL 数据如何被读进来？
- conversation 如何变成 prompt？
- prompt 如何变成 `input_ids`？
- 哪些位置的 label 是 `-100`？
- assistant 的回答为什么会被监督？

## 2. `model/model_minimind.py`

重点看：

- `MiniMindConfig`
- `Attention`
- `FeedForward`
- `MOEFeedForward`
- `MiniMindBlock`
- `MiniMindModel`
- `MiniMindForCausalLM`

你需要回答：

- token id 如何变成 embedding？
- attention 的 Q/K/V 是怎么来的？
- RoPE 在哪里用？
- MLP/FeedForward 在哪里用？
- logits 是怎么得到的？
- loss 是在哪里算的？

## 3. `trainer/train_full_sft.py`

重点看：

- argparse 参数；
- `init_model`；
- `SFTDataset`；
- DataLoader；
- `train_epoch`；
- loss backward；
- optimizer step；
- checkpoint 保存。

你需要回答：

- 训练数据路径由哪个参数传入？
- batch 的 `input_ids` 和 `labels` 形状是什么？
- loss 由哪一行得到？
- 梯度裁剪在哪里？
- 权重保存在哪里？

## 4. `trainer/train_pretrain.py`

只需要理解和 SFT 的差异：

- Pretrain 数据是普通 `text`；
- labels 基本等于 input_ids；
- 目标是普通 next-token prediction。

## 5. `eval_llm.py`

重点看：

- 如何加载模型；
- 如何调用 tokenizer；
- 如何生成回答；
- 如何写固定测试问题。

## 建议写进报告的代码理解表

| 模块 | 文件 | 作用 | 本项目关注点 |
|---|---|---|---|
| 数据 | `dataset/lm_dataset.py` | JSONL 到 tensor | SFT mask 和 chat template |
| 模型 | `model/model_minimind.py` | Transformer LM | embedding、attention、loss |
| 训练 | `trainer/train_full_sft.py` | SFT 训练循环 | loss、backward、optimizer |
| 推理 | `eval_llm.py` | 生成回答 | 固定测试集输出 |

