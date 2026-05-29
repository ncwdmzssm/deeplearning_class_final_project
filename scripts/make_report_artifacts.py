import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "summary_table.csv"
REPORTS = ROOT / "reports"
TABLE_DIR = REPORTS / "tables"
FIG_DIR = REPORTS / "figures"
DIAGRAM_DIR = REPORTS / "diagrams"
GENERATED_DIR = REPORTS / "generated"
REPORT_SUMMARY = REPORTS / "experiment_report_summary.md"
METRICS_CSV = TABLE_DIR / "metrics_for_ppt.csv"
METRICS_MD = TABLE_DIR / "metrics_for_ppt.md"

KEY_RUNS = [
    "fire_dsl_baseline_e3",
    "fire_dsl_domain_sft",
    "fire_dsl_domain_sft_t001",
    "fire_dsl_domain_sft_t001_norm",
    "fire_dsl_domain_sft_rerank5_t02",
    "fire_dsl_domain_256_l4",
    "fire_dsl_curriculum_128_l2",
    "fire_dsl_curriculum_rerank5_t02",
]

DISPLAY_NAMES = {
    "fire_dsl_baseline_e3": "Baseline SFT",
    "fire_dsl_domain_sft": "Domain Pretrain + SFT",
    "fire_dsl_domain_sft_t001": "Low-temp Decoding",
    "fire_dsl_domain_sft_t001_norm": "Output Normalization",
    "fire_dsl_domain_sft_rerank5_t02": "Verifier Reranking",
    "fire_dsl_domain_256_l4": "Larger Model 256/4",
    "fire_dsl_curriculum_128_l2": "Curriculum SFT",
    "fire_dsl_curriculum_rerank5_t02": "Curriculum + Rerank",
}


def ensure_dirs() -> None:
    for path in [TABLE_DIR, FIG_DIR, DIAGRAM_DIR, GENERATED_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_summary() -> list[dict]:
    if not SUMMARY.exists():
        raise SystemExit(f"Missing {SUMMARY}")
    with SUMMARY.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def pct(value: str | float) -> str:
    return f"{to_float(str(value)):.2f}%"


def dedupe_rows(rows: list[dict]) -> list[dict]:
    latest: dict[tuple[str, str], dict] = {}
    for row in rows:
        latest[(row.get("run_name", ""), row.get("eval_set", ""))] = row
    return list(latest.values())


def select_rows(rows: list[dict], eval_set: str | None = None) -> list[dict]:
    selected = []
    for run in KEY_RUNS:
        matches = [r for r in rows if r.get("run_name") == run and (eval_set is None or r.get("eval_set") == eval_set)]
        if matches:
            selected.append(matches[-1])
    return selected


def display_name(row: dict) -> str:
    return DISPLAY_NAMES.get(row.get("run_name", ""), row.get("run_name", ""))


def write_metrics_tables(rows: list[dict]) -> None:
    fields = [
        "run_name", "display_name", "model_type", "eval_set",
        "exact_dsl_match", "fenced_code_format", "python_parse_ok", "fire_dsl_executable",
        "format_error_rows", "parse_error_rows", "execution_error_rows", "notes",
    ]
    selected = []
    for eval_set in ["generalization", "public"]:
        selected.extend(select_rows(rows, eval_set))

    with METRICS_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            out = {k: row.get(k, "") for k in fields}
            out["display_name"] = display_name(row)
            writer.writerow(out)

    lines = [
        "# PPT 指标表", "",
        "| 方法 | Eval | Exact | Format | Parse OK | Executable | 说明 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in selected:
        lines.append(
            f"| {display_name(row)} | {row.get('eval_set', '')} | "
            f"{pct(row.get('exact_dsl_match', ''))} | {pct(row.get('fenced_code_format', ''))} | "
            f"{pct(row.get('python_parse_ok', ''))} | {pct(row.get('fire_dsl_executable', ''))} | "
            f"{row.get('notes', '')} |"
        )
    METRICS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def configure_matplotlib():
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def save_chart_note(filename: str, title: str, bullets: list[str]) -> None:
    lines = [f"# {title}", ""] + [f"- {b}" for b in bullets]
    (FIG_DIR / f"{filename}.md").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def plot_grouped_metrics(rows: list[dict]) -> None:
    plt = configure_matplotlib()
    names = [display_name(r) for r in rows]
    metrics = [("fenced_code_format", "Format"), ("python_parse_ok", "Parse OK"), ("fire_dsl_executable", "Executable")]
    xs = list(range(len(rows)))
    width = 0.24
    fig, ax = plt.subplots(figsize=(13, 6))
    colors = ["#4C78A8", "#F58518", "#54A24B"]
    for idx, (field, label) in enumerate(metrics):
        vals = [to_float(r.get(field, "")) for r in rows]
        offsets = [x + (idx - 1) * width for x in xs]
        bars = ax.bar(offsets, vals, width=width, label=label, color=colors[idx])
        ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=8)
    ax.set_title("Generalization 指标对比：训练与推理优化逐步提升", fontsize=15, pad=16)
    ax.set_ylabel("比例 (%)")
    ax.set_ylim(0, 110)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, rotation=18, ha="right")
    ax.legend(ncol=3, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_generalization_metrics_bar.png", dpi=180)
    plt.close(fig)
    save_chart_note("01_generalization_metrics_bar", "Generalization 指标对比", [
        "Domain pretrain 明显提升输出格式和基础 DSL 生成能力。",
        "Normalization 把格式正确率推到 100%，但不改变表达式语义。",
        "Verifier reranking 同时提升 Parse OK 和 FIRE DSL Executable，是当前最有效优化。",
    ])


def plot_executable_progress(rows: list[dict]) -> None:
    plt = configure_matplotlib()
    order = ["fire_dsl_baseline_e3", "fire_dsl_domain_sft", "fire_dsl_domain_sft_t001", "fire_dsl_domain_sft_t001_norm", "fire_dsl_domain_sft_rerank5_t02"]
    row_map = {r.get("run_name"): r for r in rows}
    selected = [row_map[r] for r in order if r in row_map]
    names = [display_name(r) for r in selected]
    vals = [to_float(r.get("fire_dsl_executable", "")) for r in selected]
    xs = list(range(len(vals)))
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.plot(xs, vals, marker="o", linewidth=3, color="#2F7D32")
    for x, v in zip(xs, vals):
        ax.text(x, v + 1.5, f"{v:.2f}%", ha="center", fontsize=10)
    ax.fill_between(xs, vals, color="#2F7D32", alpha=0.12)
    ax.set_title("FIRE DSL 可执行率提升路径", fontsize=15, pad=16)
    ax.set_ylabel("Executable (%)")
    ax.set_ylim(0, max(vals + [60]) + 8)
    ax.set_xticks(xs)
    ax.set_xticklabels(names, rotation=15, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "02_executable_progress.png", dpi=180)
    plt.close(fig)
    save_chart_note("02_executable_progress", "可执行率提升路径", [
        "Baseline SFT 的 generalization 可执行率为 26.17%。",
        "Domain pretrain + SFT 提升到 35.67%，说明领域继续预训练有效。",
        "Verifier reranking 提升到 52.50%，说明外部 DSL 执行器能显著筛掉非法候选。",
    ])


def plot_error_stacked(rows: list[dict]) -> None:
    plt = configure_matplotlib()
    names = [display_name(r) for r in rows]
    fmt = [to_int(r.get("format_error_rows", "")) for r in rows]
    parse = [to_int(r.get("parse_error_rows", "")) for r in rows]
    exe = [to_int(r.get("execution_error_rows", "")) for r in rows]
    xs = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.bar(xs, fmt, label="Format Error", color="#E45756")
    ax.bar(xs, parse, bottom=fmt, label="Parse Error", color="#F58518")
    bottoms = [a + b for a, b in zip(fmt, parse)]
    ax.bar(xs, exe, bottom=bottoms, label="Execution Error", color="#4C78A8")
    ax.set_title("错误数量变化：优化减少了哪些错误", fontsize=15, pad=16)
    ax.set_ylabel("错误行数")
    ax.set_xticks(xs)
    ax.set_xticklabels(names, rotation=18, ha="right")
    ax.legend(ncol=3, loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_error_rows_stacked.png", dpi=180)
    plt.close(fig)
    save_chart_note("03_error_rows_stacked", "错误数量变化", [
        "Normalization 将 format error 降为 0。",
        "Verifier reranking 进一步减少 parse error 和 execution error。",
        "剩余主要问题不再是格式，而是语义不匹配。",
    ])


def plot_public_vs_generalization(rows: list[dict]) -> None:
    plt = configure_matplotlib()
    pairs = []
    for run in ["fire_dsl_baseline_e3", "fire_dsl_domain_sft", "fire_dsl_domain_sft_rerank5_t02"]:
        public = next((r for r in rows if r.get("run_name") == run and r.get("eval_set") == "public"), None)
        general = next((r for r in rows if r.get("run_name") == run and r.get("eval_set") == "generalization"), None)
        if public and general:
            pairs.append((DISPLAY_NAMES.get(run, run), public, general))
    xs = list(range(len(pairs)))
    width = 0.34
    public_vals = [to_float(p[1].get("fire_dsl_executable", "")) for p in pairs]
    general_vals = [to_float(p[2].get("fire_dsl_executable", "")) for p in pairs]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    b1 = ax.bar([x - width / 2 for x in xs], public_vals, width=width, label="Public", color="#72B7B2")
    b2 = ax.bar([x + width / 2 for x in xs], general_vals, width=width, label="Generalization", color="#B279A2")
    ax.bar_label(b1, fmt="%.1f", padding=2, fontsize=9)
    ax.bar_label(b2, fmt="%.1f", padding=2, fontsize=9)
    ax.set_title("Public vs Generalization：seen-style 与泛化评估", fontsize=15, pad=16)
    ax.set_ylabel("Executable (%)")
    ax.set_ylim(0, max(public_vals + general_vals + [60]) + 8)
    ax.set_xticks(xs)
    ax.set_xticklabels([p[0] for p in pairs], rotation=10, ha="right")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_public_vs_generalization.png", dpi=180)
    plt.close(fig)
    save_chart_note("04_public_vs_generalization", "Public 与 Generalization 对比", [
        "Public 更接近训练分布，适合检查格式和常见映射。",
        "Generalization 是 held-out 组合，更能反映泛化能力。",
        "报告主结论以 generalization 为准。",
    ])


def plot_contribution(rows: list[dict]) -> None:
    plt = configure_matplotlib()
    order = [
        ("Baseline SFT", "fire_dsl_baseline_e3"),
        ("+ Domain Pretrain", "fire_dsl_domain_sft"),
        ("+ Low Temp", "fire_dsl_domain_sft_t001"),
        ("+ Normalization", "fire_dsl_domain_sft_t001_norm"),
        ("+ Verifier Rerank", "fire_dsl_domain_sft_rerank5_t02"),
    ]
    row_map = {r.get("run_name"): r for r in rows}
    selected = [(label, row_map[run]) for label, run in order if run in row_map]
    vals = [to_float(r.get("fire_dsl_executable", "")) for _, r in selected]
    deltas = [vals[0]] + [vals[i] - vals[i - 1] for i in range(1, len(vals))]
    labels = [x[0] for x in selected]
    colors = ["#4C78A8"] + ["#54A24B" if d >= 0 else "#E45756" for d in deltas[1:]]
    fig, ax = plt.subplots(figsize=(12, 5.5))
    bars = ax.bar(labels, deltas, color=colors)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.bar_label(bars, labels=[f"{d:+.2f}" if i else f"{d:.2f}" for i, d in enumerate(deltas)], padding=3)
    ax.set_title("优化贡献拆解：每一步带来的可执行率变化", fontsize=15, pad=16)
    ax.set_ylabel("Executable 增量/基线 (%)")
    ax.set_xticks(list(range(len(labels))))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "05_optimization_contribution.png", dpi=180)
    plt.close(fig)
    save_chart_note("05_optimization_contribution", "优化贡献拆解", [
        "Domain pretrain 是训练阶段的主要有效优化。",
        "Normalization 主要解决格式，不提升 executable。",
        "Verifier reranking 是推理阶段最有效优化。",
    ])


def make_figures(rows: list[dict]) -> None:
    general = select_rows(rows, "generalization")
    plot_grouped_metrics(general)
    plot_executable_progress(general)
    plot_error_stacked(general)
    plot_public_vs_generalization(rows)
    plot_contribution(general)


def write_diagrams() -> None:
    diagrams = {
        "01_data_model_loss_eval_flow.mmd": """flowchart LR
  A[\"JSONL 数据\"] --> B[\"Chat Template\"]
  B --> C[\"Tokenizer\"]
  C --> D[\"input_ids / labels\"]
  D --> E[\"MiniMind Transformer\"]
  E --> F[\"Logits\"]
  F --> G[\"Cross Entropy Loss\"]
  G --> H[\"Optimizer Update\"]
  H --> I[\"Checkpoint\"]
  I --> J[\"Inference\"]
  J --> K[\"Evaluation\"]
""",
        "02_sft_loss_flow.mmd": """flowchart LR
  A[\"Conversation\"] --> B[\"Tokenize\"]
  B --> C[\"Build Labels\"]
  C --> D[\"Mask system/user/padding = -100\"]
  C --> E[\"Assistant Tokens Supervised\"]
  D --> F[\"Shift Logits and Labels\"]
  E --> F
  F --> G[\"Cross Entropy ignore_index=-100\"]
  G --> H[\"Backpropagation\"]
""",
        "03_optimization_pipeline.mmd": """flowchart LR
  A[\"Baseline SFT\"] --> B[\"Domain Pretrain + SFT\"]
  B --> C[\"Low-temperature Decoding\"]
  C --> D[\"Output Normalization\"]
  D --> E[\"Multi-candidate Generation\"]
  E --> F[\"FIRE DSL Verifier Reranking\"]
  F --> G[\"Score and Error Analysis\"]
""",
    }
    for name, content in diagrams.items():
        (DIAGRAM_DIR / name).write_text(content, encoding="utf-8-sig")
    lines = [
        "# 汇报流程图索引", "",
        "| 文件 | 用途 |", "|---|---|",
        "| `01_data_model_loss_eval_flow.mmd` | 讲 MiniMind 训练、推理、评估全流程 |",
        "| `02_sft_loss_flow.mmd` | 讲 SFT 为什么只监督 assistant 部分 |",
        "| `03_optimization_pipeline.mmd` | 讲 domain pretrain、normalization、reranking 对应到流程哪里 |",
        "", "这些 Mermaid 文件可以复制到支持 Mermaid 的 Markdown、Notion、Typora 或在线 Mermaid 编辑器中导出图片。",
    ]
    (DIAGRAM_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def markdown_table(rows: list[dict]) -> str:
    lines = ["| 方法 | Eval | Exact | Format | Parse OK | Executable |", "|---|---|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            f"| {display_name(row)} | {row.get('eval_set', '')} | {pct(row.get('exact_dsl_match', ''))} | "
            f"{pct(row.get('fenced_code_format', ''))} | {pct(row.get('python_parse_ok', ''))} | "
            f"{pct(row.get('fire_dsl_executable', ''))} |"
        )
    return "\n".join(lines)


def write_report_summary(rows: list[dict]) -> None:
    general = select_rows(rows, "generalization")
    public = select_rows(rows, "public")
    best = max(general, key=lambda r: to_float(r.get("fire_dsl_executable", "")))
    baseline = next(r for r in general if r.get("run_name") == "fire_dsl_baseline_e3")
    best_gain = to_float(best.get("fire_dsl_executable", "")) - to_float(baseline.get("fire_dsl_executable", ""))
    lines = [
        "# 实验结果总结", "", "## 核心结论", "",
        f"- 当前最佳 generalization 方案是 `{best.get('run_name')}`。",
        f"- FIRE DSL executable 从 baseline 的 {pct(baseline.get('fire_dsl_executable', ''))} 提升到 {pct(best.get('fire_dsl_executable', ''))}，绝对提升 {best_gain:.2f} 个百分点。",
        "- Domain pretrain 主要提升格式稳定性和基础 DSL 学习。",
        "- Output normalization 消除格式错误，但不改变 DSL 表达式语义。",
        "- Verifier reranking 显著提升 Parse OK 和 FIRE DSL Executable。",
        "- 剩余瓶颈主要是 semantic_mismatch：模型能生成合法 DSL，但语义不一定与题目一致。",
        "", "## Generalization 指标", "", markdown_table(general),
        "", "## Public 指标", "", markdown_table(public),
        "", "## 优化方法解释", "",
        "| 优化 | 对应流程位置 | 解决的问题 | 结果解释 |",
        "|---|---|---|---|",
        "| Domain Pretrain + SFT | 训练阶段 | 让模型先熟悉 FIRE DSL 语料，再学习自然语言到代码块映射 | generalization executable 从 26.17% 到 35.67% |",
        "| Low-temperature Decoding | 推理阶段 | 降低随机性，让代码生成更稳定 | executable 小幅到 37.17% |",
        "| Output Normalization | 推理后处理 | 修复 code block、`result =`、多余标签等格式问题 | format 到 100%，但 executable 不变 |",
        "| Verifier Reranking | 推理阶段 + 外部校验 | 多候选生成后用 FIRE DSL parser/executor 选择可解析、可执行结果 | executable 到 52.50%，当前最有效 |",
        "| Larger Model 256/4 | 模型容量 | 尝试扩大模型 | public exact 变高，但 generalization executable 下降，说明更大不一定更泛化 |",
        "", "## 图表索引", "",
        "- `reports/figures/01_generalization_metrics_bar.png`：三类核心指标对比。",
        "- `reports/figures/02_executable_progress.png`：可执行率提升路径。",
        "- `reports/figures/03_error_rows_stacked.png`：错误数量变化。",
        "- `reports/figures/04_public_vs_generalization.png`：public 与 generalization 对比。",
        "- `reports/figures/05_optimization_contribution.png`：优化贡献拆解。",
    ]
    text = "\n".join(lines) + "\n"
    REPORT_SUMMARY.write_text(text, encoding="utf-8-sig")
    (GENERATED_DIR / "experiment_summary_for_ppt.md").write_text(text, encoding="utf-8-sig")


def write_slide_storyboard() -> None:
    lines = [
        "# PPT 逐页讲稿 Storyboard", "",
        "## 1. 项目目标", "- 放图：FIRE DSL 任务示例。", "- 结论：本项目不是做大模型性能竞赛，而是复现小型 LLM 的训练、推理和评估流程。", "- 讲稿：我们用 MiniMind 学习 LLM 从数据到 loss 再到生成结果的完整链路，并把它应用到金融因子 DSL 生成任务。", "",
        "## 2. MiniMind 小模型复现训练流程", "- 放图：`reports/diagrams/01_data_model_loss_eval_flow.mmd`。", "- 结论：MiniMind 把 JSONL 对话数据转成 token，再通过 Transformer 预测下一个 token。", "- 讲稿：这个流程覆盖 tokenizer、dataset、model、loss、optimizer、checkpoint 和 inference。", "",
        "## 3. FIRE DSL 数据任务", "- 放图：一条输入 prompt 和 expected DSL 示例。", "- 结论：任务目标是把自然语言金融因子想法生成 `dsl_fire` 代码块。", "- 讲稿：输出不仅要像代码，还必须能被 FIRE DSL parser/executor 解析和执行。", "",
        "## 4. 数据流与 SFT Loss", "- 放图：`reports/diagrams/02_sft_loss_flow.mmd`。", "- 结论：SFT 看完整上下文，但主要监督 assistant 回复部分。", "- 讲稿：system/user/padding 的 label 通常被设成 -100，cross entropy 会忽略这些位置。", "",
        "## 5. Baseline 实验", "- 放图：`reports/figures/02_executable_progress.png`。", "- 结论：baseline generalization executable 为 26.17%，说明基础流程跑通但泛化较弱。", "- 讲稿：小模型能学到部分格式和函数，但复杂 DSL 组合经常失败。", "",
        "## 6. Domain Pretrain 优化", "- 放图：`reports/figures/01_generalization_metrics_bar.png`。", "- 结论：domain pretrain 将 executable 提升到 35.67%。", "- 讲稿：先让模型熟悉 FIRE DSL 的函数、字段和表达式，再做 SFT，有助于领域格式学习。", "",
        "## 7. Normalization 优化", "- 放图：`reports/figures/03_error_rows_stacked.png`。", "- 结论：normalization 将 format error 清零，但 executable 没有明显提升。", "- 讲稿：这说明格式问题可以工程化修复，但表达式语义仍要靠模型或 verifier。", "",
        "## 8. Verifier Reranking 优化", "- 放图：`reports/diagrams/03_optimization_pipeline.mmd` 和 `reports/figures/05_optimization_contribution.png`。", "- 结论：reranking 将 generalization executable 提升到 52.50%。", "- 讲稿：我们让模型生成 5 个候选，然后用 FIRE DSL 执行器筛出可解析、可执行的候选。", "",
        "## 9. 结果对比图", "- 放图：`reports/figures/01_generalization_metrics_bar.png`。", "- 结论：当前最佳方案是 `fire_dsl_domain_sft_rerank5_t02`。", "- 讲稿：它在 format、parse ok 和 executable 三个指标上都最稳定。", "",
        "## 10. Public vs Generalization", "- 放图：`reports/figures/04_public_vs_generalization.png`。", "- 结论：public 更像 seen-style，generalization 更能反映 held-out 泛化。", "- 讲稿：我们报告主结论以 generalization 为准。", "",
        "## 11. 问题与下一步", "- 放图：错误类型表或 `reports/figures/03_error_rows_stacked.png`。", "- 结论：剩余瓶颈是 semantic_mismatch。", "- 讲稿：reranking 能提升合法性，但不能保证语义完全匹配，下一步应做 curriculum learning 或语义对齐数据增强。", "",
        "## 12. 总结", "- 放图：`reports/figures/02_executable_progress.png`。", "- 结论：我们复现了 MiniMind 训练流程，并验证了训练阶段和推理阶段优化的效果。", "- 讲稿：最终可执行率从 26.17% 提升到 52.50%，说明小模型配合领域训练和外部 verifier 也能完成可解释的 DSL 生成优化。",
    ]
    (GENERATED_DIR / "slide_storyboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8-sig")


def main() -> None:
    ensure_dirs()
    rows = dedupe_rows(read_summary())
    write_metrics_tables(rows)
    make_figures(rows)
    write_diagrams()
    write_report_summary(rows)
    write_slide_storyboard()
    generated = {
        "tables": [str(METRICS_CSV.relative_to(ROOT)), str(METRICS_MD.relative_to(ROOT))],
        "figures": sorted(str(p.relative_to(ROOT)) for p in FIG_DIR.glob("*.png")),
        "diagrams": sorted(str(p.relative_to(ROOT)) for p in DIAGRAM_DIR.glob("*.mmd")),
        "reports": [str(REPORT_SUMMARY.relative_to(ROOT)), str((GENERATED_DIR / "experiment_summary_for_ppt.md").relative_to(ROOT)), str((GENERATED_DIR / "slide_storyboard.md").relative_to(ROOT))],
    }
    (GENERATED_DIR / "artifact_manifest.json").write_text(json.dumps(generated, ensure_ascii=False, indent=2), encoding="utf-8-sig")
    print("Generated report artifacts:")
    for group, paths in generated.items():
        print(f"- {group}:")
        for path in paths:
            print(f"  - {path}")


if __name__ == "__main__":
    main()



