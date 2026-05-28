# 项目解释：MiniMind + FIRE DSL

## 一句话版本

本项目用 MiniMind 训练一个小型垂直领域模型，让它把自然语言金融因子想法转换成规范 FIRE operator DSL 代码块，并通过 FIRE DSL 工具验证输出是否可解析、可执行。

## 正式任务

输入：

```text
从量化研究角度，估值便宜程度高于自身 85 日 70% 分位数越多，价值信号越突出。
```

目标输出：

````text
```dsl_fire
result = sub(recip(pb), ts_quantile(recip(pb), 85, 0.7))
```
````

注意：正式输出不是裸表达式，而是 fenced `dsl_fire` code block，代码块内只写一行 `result = <DSL>`。

## 数据和材料

- 老师任务要求：`LLM_MIS2026.pptx`
- MiniMind 教学 notebook：`MiniMind_Student_Guide.ipynb`
- MiniMind 源码：`minimind/`
- 正式 FIRE DSL 数据：`fire-dsl-data/`
- MiniMind 学习参考：`learn-minimind`

## MiniMind 训练链路

```text
JSONL 数据
-> chat template
-> tokenizer
-> input_ids / labels
-> Transformer
-> logits
-> cross entropy loss
-> optimizer 更新参数
-> 推理和评估
```

## 本项目的 baseline

- 模型：MiniMind 小配置或课程配置。
- 训练脚本：`minimind/trainer/train_full_sft.py`
- 训练数据：`fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl`
- 评估数据：
  - `fire-dsl-data/eval/fire_operator_dsl_eval_code_public.jsonl`
  - `fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl`

## 本项目的优化方向

推荐优先级：

1. 领域继续预训练 + SFT。
2. LoRA SFT。
3. 超参数对比。
4. Reasoning SFT 对比。
5. Tokenizer 分析。

DPO/RLHF/RLAIF 暂不作为主线，因为老师数据包明确排除了这些默认格式。

