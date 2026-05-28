我看了你现在的结果。结论很明确：

```text
流程已经跑通；
domain pretrain + SFT 是目前最有效的优化；
但模型还远没到“DSL 生成可靠”的程度，主要瓶颈已经从格式问题转向语法/语义问题。
```

**当前结果对比**

| 模型 | Eval | Exact | Format | Parse OK | Executable | 判断 |
|---|---|---:|---:|---:|---:|---|
| baseline_e3 | public | 13.40% | 35.70% | 29.40% | 21.60% | public 上有记忆，但格式差 |
| baseline_e3 | generalization | 0.00% | 65.17% | 51.33% | 26.17% | 泛化弱 |
| baseline_old | generalization | 0.00% | 73.83% | 57.50% | 28.50% | 比 e3 略好 |
| domain_sft | generalization | 0.00% | 90.83% | 55.67% | 35.67% | 当前最佳 |

最重要的是 generalization：

```text
baseline_e3 executable: 26.17%
domain_sft executable: 35.67%
```

说明领域继续预训练确实有效，至少让模型更会输出 FIRE DSL 格式和部分可执行表达式。

---

## 结果说明

### 1. Domain pretrain 明显改善格式

`domain_sft` 的格式正确率：

```text
90.83%
```

比 baseline_e3 的：

```text
65.17%
```

提升很明显。

这说明：

```text
领域 pretrain + SFT 帮模型学会了“应该输出 dsl_fire code block”
```

这是可以写进报告的有效优化结论。

### 2. 但 Exact Match 仍然是 0

generalization 上：

```text
exact_dsl_match: 0.00%
```

这个不意外。因为 held-out 集是训练中没出现过的 DSL 组合，exact match 要求完全一致，非常苛刻。

但不能只用 exact match 判断。你们更应该强调：

```text
executable 指标更能反映模型是否生成了合法 DSL。
```

### 3. 当前最大问题是语法和语义

`domain_sft` 错误类型：

```text
semantic_mismatch: 214
parse_error: 211
execution_error: 120
format_error: 55
```

解释：

- `format_error` 已经少了，说明格式基本学会；
- `parse_error` 还很多，括号、逗号、函数参数经常错；
- `semantic_mismatch` 最多，说明即使能生成，也经常不是正确算子组合；
- `execution_error` 说明还会生成不存在的函数或非法参数。

你给出的样例里有这些典型错误：

```text
ts_cumsum        # 不在规范算子里，应该是 ts_win_cumsum 或其他合法算子
ts_regggmax      # 幻觉函数
dsl_ffire        # code block 标记拼错
tsign            # 幻觉函数
括号不闭合
函数参数数量错误
```

---

# 下一步优先级

我建议你按这个顺序继续。

## 第一步：补齐 domain_sft 的 public eval

你现在只有：

```text
domain_sft generalization
```

还缺：

```text
domain_sft public
```

跑：

```bash
cd ~/work/minimind-fire-project

RUN_NAME=fire_dsl_domain_sft \
WEIGHT=fire_dsl_domain_sft \
MODEL_TYPE=domain_pretrain_plus_sft \
TRAIN_DATA=fire_operator_dsl_sft_code.jsonl \
FROM_WEIGHT=fire_dsl_domain_pretrain \
HIDDEN_SIZE=128 \
NUM_LAYERS=2 \
MAX_SEQ_LEN=512 \
BATCH_SIZE=2 \
LEARNING_RATE=3e-4 \
EPOCHS=3 \
DEVICE=cuda \
TEMPERATURE=0.1 \
EVAL_SET=public \
NOTES="domain pretrain 2 epochs then SFT 3 epochs" \
bash scripts/run_fire_eval.sh
```

这样你的对比表才完整：

```text
baseline public / generalization
domain_sft public / generalization
```

---

## 第二步：先做推理温度对比，不用重训

你现在大概率用的是：

```text
temperature=0.1
```

代码生成任务可以再试：

```text
temperature=0.01
```

跑 domain_sft generalization：

```bash
cd ~/work/minimind-fire-project

RUN_NAME=fire_dsl_domain_sft_t001 \
WEIGHT=fire_dsl_domain_sft \
MODEL_TYPE=domain_pretrain_plus_sft \
TRAIN_DATA=fire_operator_dsl_sft_code.jsonl \
FROM_WEIGHT=fire_dsl_domain_pretrain \
HIDDEN_SIZE=128 \
NUM_LAYERS=2 \
MAX_SEQ_LEN=512 \
BATCH_SIZE=2 \
LEARNING_RATE=3e-4 \
EPOCHS=3 \
DEVICE=cuda \
TEMPERATURE=0.01 \
EVAL_SET=generalization \
NOTES="domain_sft inference temperature 0.01" \
bash scripts/run_fire_eval.sh
```

如果 `parse_ok` 和 `executable` 提升，之后所有评估都用 `0.01`。

这个是最低成本优化。

---

## 第三步：训练更大的模型

当前模型：

```text
hidden_size=128
num_layers=2
参数量约 1.26M
```

太小了。它能学格式，但很难稳定学会复杂 DSL 组合。

建议下一组：

```text
hidden_size=256
num_layers=4
batch_size=1
max_seq_len=512
```

先 domain pretrain：

```bash
cd ~/work/minimind-fire-project/minimind/trainer

python train_pretrain.py \
  --data_path ../../fire-dsl-data/train/fire_operator_dsl_pretrain_domain.jsonl \
  --epochs 2 \
  --batch_size 2 \
  --learning_rate 5e-4 \
  --num_workers 0 \
  --device cuda:0 \
  --dtype float16 \
  --hidden_size 256 \
  --num_hidden_layers 4 \
  --max_seq_len 512 \
  --from_weight none \
  --save_dir ../out \
  --save_weight fire_dsl_domain_pretrain_256 \
  2>&1 | tee ../../logs/train_fire_dsl_domain_pretrain_256.log
```

再 SFT：

```bash
python train_full_sft.py \
  --data_path ../../fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl \
  --epochs 3 \
  --batch_size 1 \
  --learning_rate 3e-4 \
  --num_workers 0 \
  --device cuda:0 \
  --dtype float16 \
  --hidden_size 256 \
  --num_hidden_layers 4 \
  --max_seq_len 512 \
  --from_weight fire_dsl_domain_pretrain_256 \
  --save_dir ../out \
  --save_weight fire_dsl_domain_sft_256 \
  2>&1 | tee ../../logs/train_fire_dsl_domain_sft_256.log
```

评估：

```bash
cd ~/work/minimind-fire-project

RUN_NAME=fire_dsl_domain_sft_256 \
WEIGHT=fire_dsl_domain_sft_256 \
MODEL_TYPE=domain_pretrain_plus_sft \
TRAIN_DATA=fire_operator_dsl_sft_code.jsonl \
FROM_WEIGHT=fire_dsl_domain_pretrain_256 \
HIDDEN_SIZE=256 \
NUM_LAYERS=4 \
MAX_SEQ_LEN=512 \
BATCH_SIZE=1 \
LEARNING_RATE=3e-4 \
EPOCHS=3 \
DEVICE=cuda \
TEMPERATURE=0.01 \
EVAL_SET=generalization \
NOTES="256 hidden 4 layers domain pretrain + SFT" \
bash scripts/run_fire_eval.sh
```

目标是看：

```text
fire_dsl_executable 是否超过 45%-50%
parse_ok 是否超过 65%
```

---

## 第四步：做一个“格式/语法后处理”优化

这是非常适合你们报告的工程优化。

当前错误里很多是：

```text
dsl_ffire
缺少换行
多余 </think>
括号不闭合
代码块外有废话
```

可以加一个后处理脚本，把模型输出规范化：

```text
提取 result = ...
修正 dsl_ffire -> dsl_fire
去掉 </think>
只保留第一个代码块
补齐 code block
```

这不会让语义变正确，但可以提升：

```text
fenced_code_format
parse_ok
fire_dsl_executable
```

报告里可以叫：

```text
推理阶段格式规范化优化
```

这个优化成本低，而且很贴合你们现在的错误分布。

建议先不改训练，先做评估后处理版本，对比：

```text
domain_sft raw
vs
domain_sft + output normalization
```

---

## 第五步：暂时不要做 LoRA

你现在已经有：

```text
domain pretrain + full SFT
```

并且效果提升明显。LoRA 更适合作为“算力不够时”的方案。

目前更值得做的是：

```text
1. domain_sft public 补齐
2. temperature 0.01
3. 256/4 模型
4. 输出后处理
```

LoRA 可以放在扩展部分，不是优先项。

---

# 报告里怎么写当前结果

你可以这样总结：

```text
Baseline SFT 在 held-out generalization 集上 exact match 为 0，
说明小模型很难直接生成完全一致的 DSL 表达式。但从可执行率看，
baseline_e3 的 FIRE DSL executable 为 26.17%。

加入 FIRE DSL domain pretrain 后，generalization 集上的 code block
格式正确率从 65.17% 提升到 90.83%，可执行率从 26.17% 提升到
35.67%。这说明领域继续预训练显著提升了模型对 FIRE DSL 输出格式
和基本算子语法的掌握。

不过错误分析显示，domain_sft 的主要错误已经从格式错误转向
semantic mismatch 和 parse error，说明后续优化重点应放在模型容量、
推理温度、输出规范化和复杂算子组合泛化能力上。
```

---

# 建议你的下一步执行清单

按顺序来：

```text
1. 补跑 domain_sft public eval
2. 跑 domain_sft temperature=0.01 generalization
3. 如果 0.01 有提升，补跑 public
4. 训练 256 hidden / 4 layers 的 domain pretrain + SFT
5. 做 output normalization 后处理对比
6. 更新 summary_table.csv 和报告表格
```

当前最有价值的对比表应该是：

| 模型 | Generalization Format | Parse OK | Executable | 结论 |
|---|---:|---:|---:|---|
| baseline_e3 | 65.17% | 51.33% | 26.17% | 基础流程跑通 |
| baseline_old | 73.83% | 57.50% | 28.50% | 旧模型略好 |
| domain_sft | 90.83% | 55.67% | 35.67% | 领域预训练有效 |
| domain_sft_t001 | TODO | TODO | TODO | 验证低温推理 |
| domain_sft_256 | TODO | TODO | TODO | 验证模型容量 |

你们现在已经有一个可以写进报告的有效优化结论：**domain pretrain + SFT 明显提升 FIRE DSL 格式稳定性和可执行率**。