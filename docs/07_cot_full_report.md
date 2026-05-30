# CoT 优化完整实验报告：MiniMind + FIRE DSL

## 1. 报告目的

这份报告完整整理本次 `CoT` 优化从最初尝试到最终超过 `domain_sft` 的全过程，重点回答四个问题：

1. 为什么最初的 `CoT` 方案没有效果。
2. 后续如何逐步改造 `CoT` 设计。
3. 每一轮实验具体使用了哪些数据、脚本、权重和结果文件。
4. 最终为什么是“`domain rerank + CoT` 融合方案”取得了最好结果。

本报告面向课程项目汇报和后续复现实验，尽量把“设计思路 + 实现步骤 + 对应文件位置 + 结果指标”一次说清楚。

## 2. CoT 是什么，为什么理论上有用

`CoT` 是 `Chain of Thought` 的缩写，中文通常叫“思维链”或“逐步推理”。

它的核心思想不是让模型单纯“多说几句”，而是让模型在给出最终答案前，先显式写出一段中间推理过程。这个中间过程可以帮助模型把复杂任务拆成几个更小、更容易处理的子步骤。

在一般语言模型任务中，`CoT` 的理论价值主要有三点：

1. **把复杂映射拆成多步**
   - 原本“输入一句话 -> 直接输出答案”是一步完成。
   - 加上 `CoT` 后，模型可以先识别关键信息，再组合答案。
2. **降低一步到位生成的难度**
   - 对需要多重约束的任务，模型直接一步生成最终答案往往容易漏条件、漏结构。
   - 中间推理可以作为过渡层，帮助模型减少遗漏。
3. **强化语义对齐**
   - 如果任务不仅要求格式正确，还要求“真正理解题意”，那么显式推理有机会帮助模型更好地对齐用户意图和输出结构。

把这个思路放到我们当前的 `FIRE DSL` 项目里，理论上 `CoT` 有用的原因是：

- 输入是自然语言金融因子想法，本身语义比较抽象。
- 输出是强约束的 `dsl_fire` 表达式，需要同时满足：
  - 字段选择正确
  - 算子选择正确
  - 窗口参数合理
  - 最终语法和执行都合法

也就是说，这个任务天然包含一条隐藏的中间链路：

```text
自然语言描述
-> 识别字段 / 算子 / 窗口 / 方向
-> 组合成 DSL
-> 包装成 fenced dsl_fire code block
```

从理论上讲，`CoT` 正适合这种“先理解语义、再拼结构化表达式”的任务。

不过，这里要特别强调：**理论上有用，不等于直接套上去就一定有效。**

原因是我们这个任务和普通开放式问答不一样，它对最终输出有很强的格式和可执行约束：

- 如果 `CoT` 写得太长，会污染最终 `dsl_fire` code block
- 如果模型把大量容量花在“学会解释”，就可能反而削弱“学会生成合法 DSL”的能力

因此，本报告后面的实验会看到一个非常关键的结论：

- `CoT` 在理论上确实可能帮助语义映射
- 但在 `FIRE DSL` 这种强结构化任务里，必须**限制 CoT 的形式、长度和使用方式**
- 否则它很容易从“帮助推理”变成“破坏输出”

## 3. 任务背景

本项目的核心任务不是普通聊天生成，而是：

```text
自然语言金融因子想法
-> MiniMind 模型生成
-> 输出 fenced `dsl_fire` code block
-> 解析 / 执行校验
-> 在 public / generalization 上评估
```

因此，`CoT` 是否有效，不能只看“模型是不是更会解释”，而必须看：

- `fenced_code_format`
- `python_parse_ok`
- `fire_dsl_executable`

也就是说，这里真正重要的是**结构化输出稳定性**和**DSL 可执行性**，而不是生成更长的自然语言。

项目主目录：

- 本地工作区：`/Users/huzhen/Desktop/深度学习 project/deeplearning_class_final_project`
- 服务器工作区：`/home/student/work/deeplearning_class_final_project`

## 4. 基础结论先给出

本次 CoT 路线一共经历了 4 个阶段：

1. `纯 CoT from scratch`
2. `domain pretrain + mixed structured CoT`
3. `CoT rerank smoke test`
4. `domain_rerank + CoT extract verifier 融合`

最终最优方案不是“单独靠 CoT 模型打赢 baseline”，而是：

```text
最强 domain_sft_rerank5_t02
+ 改良版 CoT extract
+ 逐样本 verifier 融合
= hybrid_domain_rerank_plus_cot
```

最终结果：

- `generalization`：
  - `fire_dsl_executable = 59.00%`
  - 超过 `domain_sft_rerank5_t02` 的 `52.50%`
- `public`：
  - `fire_dsl_executable = 57.65%`
  - 超过 `domain_sft_rerank5_t02` 的 `55.05%`

## 5. 相关文件总览

### 5.1 本地新增脚本

- [build_structured_cot_dataset.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/build_structured_cot_dataset.py)
  - 把原始 `reasoning_content` 转成“短结构化分析 + fenced dsl_fire”的训练样本。
- [extract_first_dsl_block.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/extract_first_dsl_block.py)
  - 从模型输出中提取第一个合法 `dsl_fire` 代码块。
- [batch_fire_rerank_infer.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/batch_fire_rerank_infer.py)
  - 多候选采样 + verifier 评分 + 重排推理。
- [combine_prediction_csvs.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/combine_prediction_csvs.py)
  - 把两份预测 CSV 按逐样本 verifier 质量融合成最终结果。

### 5.2 本地训练数据

- 原始 plain SFT 数据：
  - [fire_operator_dsl_sft_code.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl)
- 原始 reasoning 数据：
  - [fire_operator_dsl_sft_reasoning_short.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_reasoning_short.jsonl)
- 生成后的 structured CoT 数据：
  - [fire_operator_dsl_sft_structured_cot_codeblock.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_structured_cot_codeblock.jsonl)
- 生成后的 mixed CoT 数据：
  - [fire_operator_dsl_sft_mixed_cot_80_20.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_80_20.jsonl)

### 5.3 服务器上的关键权重

以下权重保存在服务器目录：

- `minimind/out/fire_dsl_cot_sft_128.pth`
- `minimind/out/fire_dsl_domain_pretrain_128.pth`
- `minimind/out/fire_dsl_domain_mixed_cot_80_20_128.pth`

完整服务器路径：

- `/home/student/work/deeplearning_class_final_project/minimind/out/fire_dsl_cot_sft_128.pth`
- `/home/student/work/deeplearning_class_final_project/minimind/out/fire_dsl_domain_pretrain_128.pth`
- `/home/student/work/deeplearning_class_final_project/minimind/out/fire_dsl_domain_mixed_cot_80_20_128.pth`

### 5.4 服务器上的关键结果文件

以下结果保存在服务器目录：

- 旧版 CoT：
  - `results/fire_dsl_cot_sft_generalization_raw_predictions.csv`
  - `results/fire_dsl_cot_sft_generalization_extract_predictions.csv`
- 改良版 mixed CoT：
  - `results/fire_dsl_domain_mixed_cot_80_20_generalization_raw_predictions.csv`
  - `results/fire_dsl_domain_mixed_cot_80_20_generalization_extract_predictions.csv`
  - `results/fire_dsl_domain_mixed_cot_80_20_public_raw_predictions.csv`
  - `results/fire_dsl_domain_mixed_cot_80_20_public_extract_predictions.csv`
- 最终融合版：
  - `results/fire_dsl_hybrid_domain_rerank_plus_cot_generalization_predictions.csv`
  - `results/fire_dsl_hybrid_domain_rerank_plus_cot_public_predictions.csv`

对应评分日志：

- `logs/fire_dsl_cot_sft_generalization_raw_score.log`
- `logs/fire_dsl_cot_sft_generalization_extract_score.log`
- `logs/fire_dsl_domain_mixed_cot_80_20_generalization_raw_score.log`
- `logs/fire_dsl_domain_mixed_cot_80_20_generalization_extract_score.log`
- `logs/fire_dsl_domain_mixed_cot_80_20_public_raw_score.log`
- `logs/fire_dsl_domain_mixed_cot_80_20_public_extract_score.log`
- `logs/fire_dsl_hybrid_domain_rerank_plus_cot_generalization_score.log`
- `logs/fire_dsl_hybrid_domain_rerank_plus_cot_public_score.log`

## 6. 第一阶段：直接做纯 CoT from scratch

### 6.1 初始设计思路

最开始的想法很直接：

- 使用现成的 `reasoning_short` 数据
- 直接训练一个 CoT 风格模型
- 看模型是否能通过 reasoning 改善自然语言到 DSL 的语义映射

目标是让模型先“想一想”，再生成 DSL。

### 6.2 实际问题

这个思路在你们任务里有两个核心风险：

1. 训练脚本不会自动使用 `reasoning_content` 作为辅助信号，而是只监督 `assistant.content`
2. 如果 `assistant.content` 里混入大量推理文本，模型很容易学会“输出解释”，而不是“稳定输出合法 DSL”

也就是说，**CoT 文字本身污染了结构化输出任务**。

### 6.3 对应文件

- 原始 reasoning 数据：
  - [fire_operator_dsl_sft_reasoning_short.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_reasoning_short.jsonl)
- 服务器训练日志：
  - `/home/student/work/deeplearning_class_final_project/logs/train_fire_dsl_cot_sft.log`
- 服务器权重：
  - `/home/student/work/deeplearning_class_final_project/minimind/out/fire_dsl_cot_sft_128.pth`

### 6.4 运行结果

只跑了 `generalization`，结果如下：

| 实验 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| old_cot_raw_g | 0.00% | 7.50% | 14.33% | 3.67% |
| old_cot_extract_g | 0.00% | 47.50% | 20.00% | 7.00% |

### 6.5 分析

这个阶段说明了两件事：

- `extract` 比 `raw` 好很多，说明模型输出里确实存在严重格式污染
- 即使做了 `extract`，性能依然很差，说明“纯 CoT from scratch”并不适合当前任务

结论：

- `CoT` 不是完全没用
- 但必须**弱化推理文本、强化最终 DSL**

## 7. 第二阶段：改造成 structured CoT + mixed SFT

### 7.1 改造思路

为了解决上面的问题，我把 CoT 方案做了 4 个关键改造：

1. `from_weight=none` 改成先接 `domain pretrain` 底座
2. 不再全量 CoT，而是改成 `80% plain SFT + 20% CoT`
3. CoT 文本从自由推理改成固定 4 行结构槽位
4. 推理后统一做 `extract fenced dsl_fire`

新的结构化 CoT 模板固定为：

~~~text
字段: ...
算子: ...
窗口: ...
方向: ...

```dsl_fire
result = ...
```
~~~

这样做的目的不是让模型“更会解释”，而是让它：

- 保留极少量语义中间层
- 不破坏最终 DSL 输出格式

### 7.2 数据构造方法

用 [build_structured_cot_dataset.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/build_structured_cot_dataset.py) 完成：

- 读入原始 `reasoning_short`
- 把 `reasoning_content` 解析成 4 个结构槽位
- 统一把最终表达式包成 fenced `dsl_fire`
- 再按 `80/20` 混合 plain SFT 与 structured CoT

生成结果：

- plain SFT 样本数：`10049`
- structured CoT 样本数：`8049`
- mixed 数据总数：`12562`
- CoT 实际使用数：`2513`

### 7.3 对应文件

- 构造脚本：
  - [build_structured_cot_dataset.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/build_structured_cot_dataset.py)
- 中间数据：
  - [fire_operator_dsl_sft_structured_cot_codeblock.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_structured_cot_codeblock.jsonl)
- 最终训练数据：
  - [fire_operator_dsl_sft_mixed_cot_80_20.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_80_20.jsonl)

### 7.4 训练方法

服务器上实际训练分两步：

1. 先补 `domain pretrain`：
   - 权重：`fire_dsl_domain_pretrain`
2. 再从该权重继续训练 mixed CoT：
   - 权重：`fire_dsl_domain_mixed_cot_80_20`

主要参数：

- `hidden_size=128`
- `num_hidden_layers=2`
- `batch_size=2`
- `epochs=3`
- `max_seq_len=512`
- `learning_rate=3e-4`

### 7.5 对应文件

- 服务器训练日志：
  - `/home/student/work/deeplearning_class_final_project/logs/train_fire_dsl_domain_pretrain.log`
  - `/home/student/work/deeplearning_class_final_project/logs/train_fire_dsl_domain_mixed_cot_80_20.log`
- 服务器权重：
  - `/home/student/work/deeplearning_class_final_project/minimind/out/fire_dsl_domain_pretrain_128.pth`
  - `/home/student/work/deeplearning_class_final_project/minimind/out/fire_dsl_domain_mixed_cot_80_20_128.pth`

## 8. 第三阶段：评估改良版 mixed CoT

### 8.1 为什么要分 raw 和 extract

因为 CoT 模型即使已经改成结构化模板，输出里仍然可能出现：

- 额外文字
- 破损的 code fence
- 多段 `dsl_fire`
- `result =` 前缀噪声

所以不能只评 `raw`，必须再评一遍 `extract`。

### 8.2 提取脚本

对应脚本：

- [extract_first_dsl_block.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/extract_first_dsl_block.py)

作用：

- 提取第一段 `dsl_fire`
- 标准化 `result = ...`
- 重新输出为合法 fenced code block

### 8.3 `generalization` 结果

| 实验 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| mixed_cot_raw_g | 0.00% | 22.67% | 18.33% | 11.33% |
| mixed_cot_extract_g | 0.00% | 92.83% | 52.00% | 11.67% |

### 8.4 `public` 结果

| 实验 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| mixed_cot_raw_p | 2.90% | 11.50% | 8.70% | 6.05% |
| mixed_cot_extract_p | 3.45% | 51.95% | 32.25% | 7.45% |

### 8.5 结论

这个阶段说明：

- 改良版 CoT **显著好于最初的纯 CoT**
- `extract` 可以大幅改善格式和解析
- 但单独的 mixed CoT 仍然**无法超过 `domain_sft`**

原因是：

- 它已经会“写得更像 DSL”
- 但还不够会“写出可执行 DSL”

换句话说，瓶颈已经从格式问题转成了 operator / argument 的执行正确性问题。

## 9. 第四阶段：尝试 CoT rerank

### 9.1 设计思路

我还额外实现了一版多候选重排推理，用 [batch_fire_rerank_infer.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/batch_fire_rerank_infer.py)：

- 对同一条输入采样 `top-k` 候选
- 先做 `extract / normalize`
- 再按 `可执行 > 可解析 > fenced > 更短表达式` 打分
- 选最优候选作为输出

### 9.2 对应文件

- 推理脚本：
  - [batch_fire_rerank_infer.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/batch_fire_rerank_infer.py)
- smoke 评分日志：
  - `/home/student/work/deeplearning_class_final_project/logs/fire_dsl_domain_mixed_cot_rerank5_t02_generalization_smoke50_score.log`

### 9.3 结果

`smoke50` 结果为：

- `fenced_code_format = 98.00%`
- `python_parse_ok = 64.00%`
- `fire_dsl_executable = 12.00%`

### 9.4 结论

这一步说明：

- 单独对 CoT 做 rerank，仍然不够强
- 它能改善格式和解析，但不能显著拉高执行率

所以如果目标是**一定超过 `domain_sft`**，不能只继续在 CoT 单支线上死磕。

## 10. 第五阶段：最终方案，domain rerank + CoT extract 融合

### 10.1 核心思路

到这里已经有两个模型支路：

1. `domain_sft_rerank5_t02`
   - 稳定、强、执行率已经很高
2. `mixed structured CoT extract`
   - 在部分样本上比 domain 路线更好

所以最终最优设计不是二选一，而是：

```text
对每一条样本：
同时拿 domain_rerank 结果 和 CoT_extract 结果
-> 用 verifier 比较两者质量
-> 逐条选更好的那个
-> 拼成最终预测文件
```

这实际上是一种**逐样本 verifier fusion**。

### 10.2 融合脚本

对应脚本：

- [combine_prediction_csvs.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/combine_prediction_csvs.py)

这个脚本的比较规则是：

- 可执行优先
- 其次可解析
- 其次 fenced code block
- 最后偏向更短的 DSL 表达式

### 10.3 `generalization` 融合结果

对比：

| 实验 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| domain_rerank_g | 0.00% | 100.00% | 76.33% | 52.50% |
| hybrid_g | 0.00% | 100.00% | 87.83% | 59.00% |

融合时从 CoT 分支替换了：

- `secondary_chosen = 178`

也就是有 `178` 条 `generalization` 样本最终选择了 CoT extract 版本。

### 10.4 `public` 融合结果

对比：

| 实验 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| domain_rerank_p | 21.15% | 100.00% | 77.05% | 55.05% |
| hybrid_p | 22.55% | 100.00% | 83.20% | 57.65% |

融合时从 CoT 分支替换了：

- `secondary_chosen = 209`

也就是有 `209` 条 `public` 样本最终选择了 CoT extract 版本。

### 10.5 最终结论

这个阶段实现了课程项目里最重要的目标：

- 不仅超过 `domain_sft`
- 还超过了已有最强的 `domain_sft_rerank5_t02`

## 11. 最终结果总结表

### 11.1 `generalization`

| 方案 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| `fire_dsl_domain_sft` | 0.00% | 90.83% | 55.67% | 35.67% |
| `fire_dsl_domain_sft_t001_norm` | 0.00% | 100.00% | 56.17% | 37.17% |
| `fire_dsl_domain_sft_rerank5_t02` | 0.00% | 100.00% | 76.33% | 52.50% |
| `fire_dsl_hybrid_domain_rerank_plus_cot` | 0.00% | 100.00% | 87.83% | 59.00% |

### 11.2 `public`

| 方案 | exact | fenced | parse | executable |
|---|---:|---:|---:|---:|
| `fire_dsl_domain_sft` | 19.05% | 90.20% | 64.65% | 45.70% |
| `fire_dsl_domain_sft_rerank5_t02` | 21.15% | 100.00% | 77.05% | 55.05% |
| `fire_dsl_hybrid_domain_rerank_plus_cot` | 22.55% | 100.00% | 83.20% | 57.65% |

## 12. 为什么最终方案能成功

这次 CoT 路线最后能成功，关键原因不是“CoT 本身变得特别强”，而是：

1. **CoT 被重新约束了**
   - 从自由文本推理改成固定槽位推理。
2. **CoT 不再单独承担全部任务**
   - 先用 plain SFT 保住格式能力。
3. **CoT 输出被后处理规范化**
   - 通过 `extract_first_dsl_block.py` 去掉输出污染。
4. **最终不是单模型决胜，而是 verifier 融合**
   - 让 CoT 只在它更强的样本上发力。

所以更准确地说：

- `CoT` 单独并没有打败最强 `domain_sft`
- 但 `CoT` 作为第二专家，被 verifier 融合后，成功把最强系统进一步推高

## 13. 这条 CoT 路线的最终定位

本次实验之后，可以把 CoT 在这个项目中的定位总结为：

- **不适合作为单独主模型**
- **适合作为辅助生成专家**
- **适合与 verifier / rerank / fusion 结合**

也就是说，CoT 在这个 FIRE DSL 项目里最有价值的角色不是“唯一答案生成器”，而是：

```text
提供一部分 domain_sft 没覆盖好的候选解
再由 verifier 挑出来
```

## 14. 文件定位清单

### 14.1 本地可以直接打开的文件

- 报告文件：
  - [07_cot_full_report.md](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/docs/07_cot_full_report.md)
- structured CoT 构造脚本：
  - [build_structured_cot_dataset.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/build_structured_cot_dataset.py)
- 提取脚本：
  - [extract_first_dsl_block.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/extract_first_dsl_block.py)
- rerank 推理脚本：
  - [batch_fire_rerank_infer.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/batch_fire_rerank_infer.py)
- 结果融合脚本：
  - [combine_prediction_csvs.py](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/scripts/combine_prediction_csvs.py)
- structured CoT 数据：
  - [fire_operator_dsl_sft_structured_cot_codeblock.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_structured_cot_codeblock.jsonl)
- mixed CoT 数据：
  - [fire_operator_dsl_sft_mixed_cot_80_20.jsonl](file:///Users/huzhen/Desktop/深度学习%20project/deeplearning_class_final_project/fire-dsl-data/train/fire_operator_dsl_sft_mixed_cot_80_20.jsonl)

### 14.2 服务器上的正式结果文件

服务器根目录：

- `/home/student/work/deeplearning_class_final_project`

正式结果文件：

- `results/fire_dsl_hybrid_domain_rerank_plus_cot_generalization_predictions.csv`
- `results/fire_dsl_hybrid_domain_rerank_plus_cot_public_predictions.csv`
- `logs/fire_dsl_hybrid_domain_rerank_plus_cot_generalization_score.log`
- `logs/fire_dsl_hybrid_domain_rerank_plus_cot_public_score.log`
- `results/summary_table.csv`

## 15. 最后一段汇报用结论

如果要在 PPT 或答辩里用一句话总结这次 CoT 路线，可以直接说：

> 我们先尝试了纯 CoT SFT，但发现它会显著污染 `dsl_fire` 输出格式；随后将 CoT 重构为 `domain pretrain + mixed structured CoT + extract` 的形式，使其成为一个更稳定的候选生成器；最后再与最强 `domain_sft_rerank` 做逐样本 verifier 融合，最终在 `generalization` 上把 `fire_dsl_executable` 从 `52.50%` 提升到 `59.00%`，在 `public` 上把 `55.05%` 提升到 `57.65%`，成为当前项目最佳结果。
