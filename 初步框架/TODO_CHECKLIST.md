# TODO 清单：MiniMind + FIRE DSL 正式版

## A. 全员共同理解

- [ ] 阅读 `LLM_MIS2026.pptx` 第 15 页。
- [ ] 阅读 `MiniMind_Student_Guide.ipynb`。
- [ ] 阅读 `docs/06_learn_minimind_route.md`。
- [ ] 阅读 `fire-dsl-data/README.md` 和 `fire-dsl-data/docs/dataset_card.md`。
- [ ] 能解释：Tokenizer、Pretrain、SFT、LoRA、loss mask、chat template。
- [ ] 能解释正式任务：自然语言金融因子想法 -> fenced `dsl_fire` code block。

## B. 路径和数据检查

- [x] MiniMind 源码在 `minimind/`。
- [x] 正式课程数据在 `fire-dsl-data/`。
- [ ] 跑数据检查：

```powershell
python scripts\inspect_fire_dsl_data.py
```

- [ ] 跑 DSL 工具 demo：

```powershell
python fire-dsl-data\tools\demo_verify_dsl.py
```

- [ ] 生成评估 CSV：

```powershell
python scripts\make_fire_eval_csv.py fire-dsl-data\eval\fire_operator_dsl_eval_code_public.jsonl results\fire_eval_public_predictions.csv
python scripts\make_fire_eval_csv.py fire-dsl-data\eval\fire_operator_dsl_eval_code_generalization.jsonl results\fire_eval_generalization_predictions.csv
```

## C. Baseline SFT

- [ ] 建立 Python 3.10/3.11 环境并安装依赖。
- [ ] 用小配置跑通 baseline smoke test。
- [ ] 正式 baseline 使用 `fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl`。
- [ ] 记录训练配置：weight、hidden size、layers、max seq len、batch size、learning rate、epoch、device。
- [ ] 保存训练日志、checkpoint 路径、样例输出。

## D. 推理和评估

- [ ] 用 `scripts/batch_fire_infer.py` 跑 public eval。
- [ ] 用 `scripts/batch_fire_infer.py` 跑 generalization eval。
- [ ] 用 `scripts/score_fire_predictions.py` 计算自动指标。
- [ ] 用 `scripts/analyze_fire_errors.py` 生成错误类型统计。
- [ ] 人工抽样 20-50 条，标注语义是否合理。

## E. 优化实验

- [ ] 优化 1：domain pretrain + SFT。
- [ ] 优化 2：LoRA SFT。
- [ ] 优化 3：超参数对比，至少比较 2 组配置。
- [ ] 扩展：reasoning SFT 对比，注意裸 DSL 与 code block 格式冲突。
- [ ] 扩展：tokenizer 分析，不重训 tokenizer，只解释 DSL tokenization 难点。

## F. 报告和 PPT

- [ ] 报告 `learn-minimind` 如何帮助理解 MiniMind。
- [ ] 报告老师数据包的文件角色和样本数量。
- [ ] 报告 baseline 训练流程和结果。
- [ ] 报告至少一个优化实验。
- [ ] public 和 generalization 分开汇报，重点解释 generalization。
- [ ] 错误分析至少包含：格式错误、解析错误、不可执行、语义不匹配、旧字段/旧函数错误。

