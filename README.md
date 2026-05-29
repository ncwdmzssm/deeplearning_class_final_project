# MiniMind + FIRE DSL 深度学习期末项目

本仓库用于课程期末项目：基于 MiniMind 小型大语言模型，完成 FIRE DSL 金融因子代码生成任务的训练、推理、评估和优化实验。

项目主线：

```text
自然语言金融因子想法
-> MiniMind tokenizer / dataset / Transformer / SFT loss
-> 生成 fenced dsl_fire 代码块
-> FIRE DSL parser / executor 自动评估
-> domain pretrain、normalization、verifier reranking 优化
-> 生成报告图表和 PPT 材料
```

当前最佳方案：

```text
fire_dsl_domain_sft_rerank5_t02
Generalization FIRE DSL Executable = 52.50%
```

核心结论：baseline SFT 的 generalization executable 为 26.17%；加入 domain pretrain、低温推理、输出规范化和 verifier reranking 后，最佳可执行率提升到 52.50%。

---

## 1. 队友从 GitHub 获取代码

### 1.1 第一次 clone

推荐先 clone 本项目主仓库：

```bash
git clone https://github.com/ncwdmzssm/deeplearning_class_final_project.git
cd deeplearning_class_final_project
```

如果项目主要工作在 `server-experiments` 分支，切换到该分支：

```bash
git fetch origin
git switch server-experiments
```

如果本地没有这个分支：

```bash
git switch -c server-experiments origin/server-experiments
```

如果改变代码，请新建分支，具体操作在下文

### 1.2 MiniMind 源码说明

本仓库默认不上传 `minimind/` 目录和模型权重，因为它们较大且属于外部项目/运行产物。`.gitignore` 中已经忽略：

```text
minimind/
*.pth
*.pt
*.bin
*.safetensors
```

因此，fresh clone 后如果要重新训练或推理，需要额外获取 MiniMind 源码：

```bash
git clone https://github.com/jingyaogong/minimind.git minimind
```

确认目录结构应类似：

```text
minimind/model/model_minimind.py
minimind/model/tokenizer.json
minimind/trainer/train_full_sft.py
minimind/trainer/train_pretrain.py
```

注意：GitHub 仓库里通常只有代码、数据、日志和结果 CSV，不包含已经训练好的 `.pth` 权重。要推理必须满足二选一：

```text
1. 自己重新训练得到 minimind/out/*.pth
2. 从组员处单独获取权重文件并放入 minimind/out/
```

---

## 2. 环境配置

### 2.1 推荐环境

服务器推荐：

```text
Python 3.10+ / 3.11+ / 3.12
CUDA GPU 推荐，但不是所有脚本都必须 GPU
```

### 2.2 创建环境

Conda 示例：

```bash
conda create -n minimind-fire python=3.12 -y
conda activate minimind-fire
```

如果服务器已经有 base 环境且依赖可用，也可以直接使用 base。

### 2.3 安装依赖

先安装 MiniMind 依赖：

```bash
pip install -r minimind/requirements.txt
```

再补充本项目脚本常用依赖：

```bash
pip install pandas numpy matplotlib tqdm transformers
```

PyTorch 建议按服务器 CUDA 版本安装。如果服务器已有 torch，可以先检查：

```bash
python - <<'PY'
import torch
print(torch.__version__)
print('cuda available:', torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0))
PY
```

### 2.4 快速检查

```bash
python scripts/inspect_fire_dsl_data.py
python fire-dsl-data/tools/demo_verify_dsl.py
python scripts/make_report_artifacts.py
```

成功标准：

```text
1. 数据检查脚本能输出 train/eval 数量。
2. FIRE DSL demo 可以执行。
3. reports/figures/ 下生成 5 张 PNG 图。
```

---

## 3. Git 分支和协作流程

### 3.1 查看当前分支

```bash
git branch --show-current
git status
```

### 3.2 创建自己的工作分支

建议每个人从 `server-experiments` 切自己的分支，避免互相覆盖：

```bash
git switch server-experiments
git pull --rebase origin server-experiments
git switch -c yourname-work
```

示例：

```bash
git switch -c zhangsan-report
```

### 3.3 更新远程最新内容

如果你在 `server-experiments` 上工作：

```bash
git pull --rebase origin server-experiments
```

如果你在个人分支上工作，也建议先更新主分支再 rebase：

```bash
git fetch origin
git rebase origin/server-experiments
```

### 3.4 提交代码和结果

不要使用 `git add .`，因为可能误加大文件或嵌套仓库。推荐：

```bash
git add scripts results logs experiments reports docs HANDOFF.md README.md PROJECT_README.md TODO_CHECKLIST.md
```

提交：

```bash
git commit -m "Update report docs and experiment artifacts"
```

推送当前分支：

```bash
git push -u origin your-branch-name
```

如果直接推 `server-experiments`：

```bash
git push -u origin server-experiments
```

### 3.5 共享服务器上的 GitHub 凭据安全

共享服务器不要长期保存 GitHub token。推送完成后可以检查：

```bash
git remote -v
git config --global --get credential.helper
```

如果之前保存了 token，可清理：

```bash
git config --global --unset credential.helper
rm -f ~/.git-credentials
```

---

## 4. 仓库目录结构说明

### 4.1 根目录文件

```text
README.md
```
仓库入口文档。队友从 GitHub clone 后先读这个。

```text
PROJECT_README.md
```
项目主说明，内容与 README 保持同步，兼容旧文档入口。

```text
HANDOFF.md
```
交接文档。说明当前做到哪里、最佳实验、重要结果、脚本作用和下一步方向。

```text
TODO_CHECKLIST.md
```
任务清单。用于检查课程项目还有哪些工作要补。

```text
LLM_MIS2026.pptx
MiniMind_Student_Guide.ipynb
数据理解.pdf
```
老师材料和课程 notebook。用于理解课程任务要求和 MiniMind 教学流程。

```text
第一轮优化结果与下一轮方向.md
第二轮优化结果与下一轮方向.md
第三轮优化结果与下一轮方向.md
第三轮优化代码（三个方向）.txt
汇报用材料制作.txt
在服务器上的推送git命令.txt
```
项目推进过程中的记录文件，适合理解决策过程和服务器操作历史。

### 4.2 `docs/`

项目解释和代码使用文档。

```text
docs/01_project_explanation.md
```
解释项目目标、MiniMind 和 FIRE DSL 任务。

```text
docs/02_minimind_code_reading.md
```
MiniMind 源码阅读重点：tokenizer、dataset、model、loss、trainer。

```text
docs/03_experiment_protocol.md
```
实验协议：baseline、domain pretrain、SFT、评估方式。

```text
docs/04_environment_setup.md
```
环境配置说明。

```text
docs/05_data_guide.md
```
FIRE DSL 数据说明，区分训练集、public eval、generalization eval。

```text
docs/06_learn_minimind_route.md
```
结合 learn-minimind 仓库的学习路线。

```text
docs/07_code_usage_guide.md
```
最重要的操作指南之一。按任务给出检查数据、训练、推理、normalization、reranking、评分、生成图表、Git 上传命令。

### 4.3 `data/`

早期手写的小样例数据，仅用于理解 SFT 格式，不作为正式实验数据。

```text
data/finance_dsl_sft_train.jsonl
data/finance_dsl_sft_eval.jsonl
data/finance_dsl_terms.txt
```

正式实验不要用这里的数据。

### 4.4 `fire-dsl-data/`

老师给的正式 FIRE DSL 数据和执行工具，是本项目正式数据主线。

```text
fire-dsl-data/train/fire_operator_dsl_sft_code.jsonl
```
正式 SFT 训练集。

```text
fire-dsl-data/train/fire_operator_dsl_pretrain_domain.jsonl
```
领域继续预训练数据。

```text
fire-dsl-data/train/fire_operator_dsl_sft_reasoning_short.jsonl
```
带 reasoning_content 的扩展数据。注意它的输出格式与正式 fenced code block 主线不完全一致，不能直接混入 baseline。

```text
fire-dsl-data/eval/fire_operator_dsl_eval_code_public.jsonl
```
public / seen-style 评估集，用于检查常见格式和映射能力。

```text
fire-dsl-data/eval/fire_operator_dsl_eval_code_generalization.jsonl
```
held-out generalization 评估集，是报告主指标来源。

```text
fire-dsl-data/tools/fire_operator_dsl.py
```
FIRE DSL parser/executor，用于判断表达式是否可执行。

```text
fire-dsl-data/docs/
```
数据卡、算子目录、验证报告和增强数据说明。

### 4.5 `minimind/`

MiniMind 官方源码目录。fresh clone 本仓库后可能没有该目录，需要单独 clone。

重点文件：

```text
minimind/model/model_minimind.py
```
MiniMind Transformer 模型结构和 generate 逻辑。

```text
minimind/dataset/lm_dataset.py
```
预训练/SFT 数据读取、chat template、label mask 逻辑。

```text
minimind/trainer/train_pretrain.py
```
领域继续预训练入口。

```text
minimind/trainer/train_full_sft.py
```
全参数 SFT 训练入口。

```text
minimind/trainer/train_lora.py
```
LoRA SFT 入口，当前不是主线。

```text
minimind/out/
```
训练后的权重输出目录，通常不上传 GitHub。

### 4.6 `scripts/`

本项目自定义脚本目录，是复现实验和生成汇报材料的主要入口。

```text
scripts/inspect_fire_dsl_data.py
```
检查 FIRE DSL 数据数量和格式。

```text
scripts/analyze_tokenizer_terms.py
```
分析 FIRE DSL 术语在 tokenizer 中的拆分情况。

```text
scripts/make_fire_eval_csv.py
```
把 eval JSONL 转成可填写/评分的 CSV 模板。

```text
scripts/batch_fire_infer.py
```
批量推理脚本，读取 eval JSONL，输出 predictions CSV。

```text
scripts/score_fire_predictions.py
```
自动评分脚本，计算 Exact、Format、Parse OK、Executable。

```text
scripts/analyze_fire_errors.py
```
错误类型分析，输出 errors CSV 和错误数量统计。

```text
scripts/normalize_fire_predictions.py
```
输出规范化，把模型回答统一整理成 fenced `dsl_fire` code block。

```text
scripts/select_best_fire_candidate.py
```
verifier reranking，从多个候选中选 parse/executable 最好的结果。

```text
scripts/run_fire_eval.sh
```
一键执行推理、评分、错误分析、写入 summary。

```text
scripts/run_experiment_pipeline.sh
```
一键训练 baseline 或 domain_pretrain_sft，并自动评估。

```text
scripts/append_score_summary.py
```
把 score log 追加写入 `results/summary_table.csv`。

```text
scripts/make_report_artifacts.py
```
生成 PPT 图表、Mermaid 流程图、汇报摘要和 storyboard。汇报前必跑。

### 4.7 `results/`

实验输出结果目录。

```text
results/summary_table.csv
```
最重要的结果总表。报告中的指标应以它为准。

```text
results/*_predictions.csv
```
模型预测结果。

```text
results/*_errors.csv
```
错误分析结果。

```text
results/rerank_candidates/
```
verifier reranking 的多个候选输出。

```text
results/backups/
```
关键结果表的备份。

### 4.8 `logs/`

训练、推理、评分和错误分析日志。

```text
logs/train_*.log
```
训练日志，包含 loss 和训练过程。

```text
logs/*_infer.log
```
批量推理日志。

```text
logs/*_score.log
```
评分日志。

```text
logs/*_errors.log
```
错误类型统计日志。

```text
logs/rerank_candidates/
```
多候选推理日志。

### 4.9 `experiments/`

实验配置记录。

```text
experiments/*.env
```
记录每个实验的 run name、模型大小、训练轮数、学习率、temperature 等。

### 4.10 `reports/`

汇报材料目录。

```text
reports/experiment_report_summary.md
```
实验结果文字总结。

```text
reports/presentation_outline.md
```
PPT 简版大纲。

```text
reports/research_report_template.md
```
研究报告模板。

```text
reports/tables/metrics_for_ppt.csv
reports/tables/metrics_for_ppt.md
```
PPT 可用指标表。

```text
reports/figures/*.png
```
PPT 可直接使用的图表。

```text
reports/figures/*.md
```
每张图对应的讲稿要点。

```text
reports/diagrams/*.mmd
```
Mermaid 流程图：数据流、SFT loss、优化流程。

```text
reports/generated/experiment_summary_for_ppt.md
reports/generated/slide_storyboard.md
reports/generated/artifact_manifest.json
```
自动生成的汇报摘要、逐页讲稿和材料清单。

---

## 5. 拿到代码后应该先看哪些文件

### 5.1 只想快速理解项目

按顺序读：

```text
README.md
HANDOFF.md
reports/experiment_report_summary.md
reports/generated/slide_storyboard.md
```

读完应能知道：项目目标、当前最好结果、PPT 怎么讲。

### 5.2 想理解 MiniMind 训练流程

按顺序读：

```text
docs/01_project_explanation.md
docs/02_minimind_code_reading.md
minimind/dataset/lm_dataset.py
minimind/model/model_minimind.py
minimind/trainer/train_pretrain.py
minimind/trainer/train_full_sft.py
```

重点理解：

```text
JSONL -> chat template -> tokenizer -> input_ids/labels -> Transformer -> logits -> cross entropy loss
```

### 5.3 想理解数据和评估

按顺序读：

```text
docs/05_data_guide.md
fire-dsl-data/README.md
fire-dsl-data/docs/dataset_card.md
scripts/score_fire_predictions.py
scripts/analyze_fire_errors.py
results/summary_table.csv
```

重点理解：

```text
public eval 是 seen-style 检查
generalization eval 是 held-out 泛化检查
报告主结论看 generalization
```

### 5.4 想继续跑代码

先读：

```text
docs/07_code_usage_guide.md
scripts/run_experiment_pipeline.sh
scripts/run_fire_eval.sh
```

然后按需要运行训练、推理或报告生成。

### 5.5 想做 PPT

先读：

```text
reports/presentation_outline.md
reports/generated/slide_storyboard.md
reports/generated/experiment_summary_for_ppt.md
```

直接使用：

```text
reports/figures/*.png
reports/diagrams/*.mmd
reports/tables/metrics_for_ppt.md
```

---

## 6. 常用命令速查

### 6.1 生成汇报图表

```bash
python scripts/make_report_artifacts.py
```

### 6.2 查看核心结果

```bash
cat results/summary_table.csv
cat reports/experiment_report_summary.md
```

### 6.3 评分某个 predictions 文件

```bash
python scripts/score_fire_predictions.py results/xxx_predictions.csv
```

### 6.4 错误分析

```bash
python scripts/analyze_fire_errors.py results/xxx_predictions.csv results/xxx_errors.csv
```

### 6.5 跑一个 eval 流程

```bash
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
TEMPERATURE=0.01 \
EVAL_SET=generalization \
NOTES="domain_sft low temperature" \
bash scripts/run_fire_eval.sh
```

---

## 7. 当前核心实验结果

Generalization：

| 方法 | Format | Parse OK | Executable | 说明 |
|---|---:|---:|---:|---|
| Baseline SFT | 65.17% | 51.33% | 26.17% | 基础 SFT |
| Domain Pretrain + SFT | 90.83% | 55.67% | 35.67% | 训练阶段优化有效 |
| Low-temp Decoding | 91.83% | 55.67% | 37.17% | 推理更稳定 |
| Output Normalization | 100.00% | 56.17% | 37.17% | 消除格式错误 |
| Verifier Reranking | 100.00% | 76.33% | 52.50% | 当前最佳 |
| Larger Model 256/4 | 68.67% | 43.50% | 25.83% | 反例：更大不一定更泛化 |

Public：

| 方法 | Format | Parse OK | Executable |
|---|---:|---:|---:|
| Baseline SFT | 35.70% | 29.40% | 21.60% |
| Domain Pretrain + SFT | 90.20% | 64.65% | 45.70% |
| Verifier Reranking | 100.00% | 77.05% | 55.05% |

---

## 8. 后续方向

当前主要瓶颈不是格式，而是：

```text
semantic_mismatch
```

也就是模型能生成合法 DSL，但语义不一定对应题目。

下一步优先级：

1. Curriculum learning：按 simple -> medium -> hard DSL 逐步训练。
2. 针对 semantic_mismatch 的数据增强。
3. 更强的 reranking：不仅检查可执行，还加入字段、窗口、函数族匹配规则。
4. Tokenizer 分析可以作为解释材料，不建议作为主线重训 tokenizer。

---

## 9. 注意事项

- 不要把 `minimind/out/*.pth` 上传 GitHub。
- 不要盲目 `git add .`。
- 汇报指标以 `results/summary_table.csv` 为准。
- 报告主结论以 generalization 为准，public 只作辅助。
- 生成图表前先确认 `summary_table.csv` 是最新版。
