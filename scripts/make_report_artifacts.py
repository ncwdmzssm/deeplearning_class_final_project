import csv
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "summary_table.csv"
REPORT = ROOT / "reports" / "experiment_report_summary.md"
TABLE = ROOT / "reports" / "tables" / "metrics_for_ppt.csv"

KEY_RUNS = [
    "fire_dsl_baseline_e3",
    "fire_dsl_domain_sft",
    "fire_dsl_domain_sft_t001",
    "fire_dsl_domain_sft_t001_norm",
    "fire_dsl_domain_sft_rerank5_t02",
    "fire_dsl_curriculum_128_l2",
    "fire_dsl_domain_256_l4",
]

def read_summary():
    if not SUMMARY.exists():
        raise SystemExit(f"Missing {SUMMARY}")
    with SUMMARY.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def pct(v):
    try:
        return f"{float(v):.2f}%"
    except Exception:
        return str(v)

def main():
    rows = read_summary()
    rows = [r for r in rows if r.get("eval_set") == "generalization"]

    selected = []
    for name in KEY_RUNS:
        matches = [r for r in rows if r.get("run_name") == name]
        if matches:
            selected.append(matches[-1])

    if not selected:
        selected = rows

    TABLE.parent.mkdir(parents=True, exist_ok=True)
    with TABLE.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "run_name",
            "model_type",
            "exact_dsl_match",
            "fenced_code_format",
            "python_parse_ok",
            "fire_dsl_executable",
            "format_error_rows",
            "parse_error_rows",
            "execution_error_rows",
            "notes",
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in selected:
            w.writerow({k: r.get(k, "") for k in fields})

    best = max(selected, key=lambda r: float(r.get("fire_dsl_executable") or 0))

    lines = []
    lines.append("# 实验结果汇总\n")
    lines.append("## 核心结论\n")
    lines.append(f"- 当前 generalization 最优实验：`{best['run_name']}`。")
    lines.append(f"- FIRE DSL executable：{pct(best['fire_dsl_executable'])}。")
    lines.append(f"- fenced code format：{pct(best['fenced_code_format'])}。")
    lines.append(f"- python parse ok：{pct(best['python_parse_ok'])}。\n")

    lines.append("## Generalization 指标对比\n")
    lines.append("| 实验 | 优化方法 | Exact | Format | Parse OK | Executable | 备注 |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for r in selected:
        lines.append(
            f"| `{r.get('run_name','')}` "
            f"| {r.get('model_type','')} "
            f"| {pct(r.get('exact_dsl_match',''))} "
            f"| {pct(r.get('fenced_code_format',''))} "
            f"| {pct(r.get('python_parse_ok',''))} "
            f"| {pct(r.get('fire_dsl_executable',''))} "
            f"| {r.get('notes','')} |"
        )

    lines.append("\n## 错误数量对比\n")
    lines.append("| 实验 | Format Error | Parse Error | Execution Error |")
    lines.append("|---|---:|---:|---:|")
    for r in selected:
        lines.append(
            f"| `{r.get('run_name','')}` "
            f"| {r.get('format_error_rows','')} "
            f"| {r.get('parse_error_rows','')} "
            f"| {r.get('execution_error_rows','')} |"
        )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {REPORT}")
    print(f"wrote {TABLE}")

if __name__ == "__main__":
    main()
