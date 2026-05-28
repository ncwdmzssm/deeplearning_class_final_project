# 展示 PPT 大纲

## 1. 标题页

MiniMind + FIRE Operator DSL 垂直领域训练实验

## 2. 项目目标

- 理解 MiniMind 训练流程。
- 使用 `fire-dsl-data/` 训练金融 DSL 模型。
- 跑通 baseline。
- 做至少一个优化实验。
- 比较 public 和 generalization 结果。

## 3. 学习路线

TODO：展示 `learn-minimind` 对应章节：Tokenizer、数据处理、Pretrain、SFT、LoRA、推理。

## 4. MiniMind 训练链路

```text
JSONL -> chat template -> tokenizer -> input_ids/labels -> Transformer -> logits -> loss
```

## 5. FIRE DSL 任务定义

展示输入输出样例：

````text
```dsl_fire
result = div(sub(close, open), open)
```
````

## 6. 数据集说明

TODO：展示训练集、public eval、generalization eval 的数量和用途。

## 7. Baseline 实验

TODO：展示训练配置、loss、样例输出。

## 8. 优化方法

TODO：展示 domain pretrain + SFT 或 LoRA SFT。

## 9. 自动评估指标

- Exact DSL Match
- Fenced Code Format
- Parse OK
- FIRE DSL Executable

## 10. 对比结果

TODO：public 和 generalization 分开汇报。

## 11. 错误分析

TODO：展示 3-5 个典型失败案例。

## 12. 总结

TODO：总结 MiniMind 原理理解、垂直领域训练收获、优化是否有效。

