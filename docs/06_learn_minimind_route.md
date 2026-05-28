# learn-minimind 学习路线和本项目对应关系

参考仓库：

- https://github.com/bcefghj/learn-minimind
- SFT 讲解：https://github.com/bcefghj/learn-minimind/blob/main/docs/L13-%E7%9B%91%E7%9D%A3%E5%BE%AE%E8%B0%83SFT.md

## 为什么要看这个仓库

`learn-minimind` 是对 MiniMind 的教学式拆解，适合把“源码能跑”和“知道为什么这样跑”连接起来。它不替代老师的数据和任务要求，但可以作为你们报告里解释 MiniMind 原理的主要参考。

## 必看章节

| 章节 | 对应本项目问题 |
|---|---|
| L05 Tokenizer | FIRE DSL 字段/算子如何变成 token |
| L11 数据处理 | JSONL 如何变成训练样本 |
| L12 Pretrain | 领域继续预训练为什么有意义 |
| L13 SFT | 为什么 SFT 只监督 assistant 输出 |
| L14 LoRA | 为什么 8GB GPU 更适合 LoRA |
| L20 推理优化 | batch inference 和生成参数如何设置 |

## 三个人怎么学

全员都要知道主链路：

```text
JSONL -> chat template -> tokenizer -> input_ids/labels -> model -> logits -> loss
```

分工建议：

- A：Tokenizer、Dataset、SFT loss mask。
- B：Pretrain、LoRA、训练命令和显存约束。
- C：推理、评估、错误分析和报告整合。

## 写进报告的关键观点

1. Pretrain 和 SFT 的核心区别不是模型结构，而是数据格式和训练目标。
2. SFT 中模型读取完整对话，但 loss 主要计算 assistant 回复。
3. 训练和推理必须使用一致的 chat template，否则模型学到的格式和实际生成格式会错位。
4. LoRA 只训练少量参数，适合 8GB 显存下做垂直领域适配。
5. 对 FIRE DSL 任务，输出格式本身就是目标的一部分，不能只看表达式是否大概像。

