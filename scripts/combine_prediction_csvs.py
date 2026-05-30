#!/usr/bin/env python3
import argparse
import ast
import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "fire-dsl-data" / "tools"))

from fire_operator_dsl import make_synthetic_data, verify_expression  # noqa: E402


def extract_dsl(text: str) -> str:
    text = (text or "").strip()
    match = re.search(r"```dsl_fire\s*result\s*=\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if text.startswith("result ="):
        return text.split("=", 1)[1].strip()
    return text


def is_fenced_code(text: str) -> bool:
    return bool(re.search(r"^```dsl_fire\s*result\s*=\s*.+?\s*```$", (text or "").strip(), flags=re.DOTALL | re.IGNORECASE))


def parse_ok(expr: str) -> bool:
    try:
        ast.parse(expr, mode="eval")
        return True
    except SyntaxError:
        return False


def verify_ok(expr: str, data) -> bool:
    try:
        verify_expression(expr, data)
        return True
    except Exception:
        return False


def quality(pred: str, data):
    expr = extract_dsl(pred)
    fenced = is_fenced_code(pred)
    parsed = parse_ok(expr)
    executed = parsed and verify_ok(expr, data)
    return (1 if executed else 0, 1 if parsed else 0, 1 if fenced else 0, -len(expr))


def main():
    parser = argparse.ArgumentParser(description="Combine two prediction CSVs by verifier quality.")
    parser.add_argument("--primary_csv", required=True)
    parser.add_argument("--secondary_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--primary_tag", default="primary")
    parser.add_argument("--secondary_tag", default="secondary")
    args = parser.parse_args()

    data = make_synthetic_data(seed=7, n_days=120, n_assets=10)
    primary_rows = list(csv.DictReader(Path(args.primary_csv).open("r", encoding="utf-8-sig", newline="")))
    secondary_rows = list(csv.DictReader(Path(args.secondary_csv).open("r", encoding="utf-8-sig", newline="")))
    if len(primary_rows) != len(secondary_rows):
        raise ValueError("CSV row counts do not match.")

    output_rows = []
    choose_secondary = 0
    for primary, secondary in zip(primary_rows, secondary_rows):
        qp = quality(primary.get("prediction", ""), data)
        qs = quality(secondary.get("prediction", ""), data)
        if qs > qp:
            chosen = dict(secondary)
            chosen["notes"] = ((chosen.get("notes") or "") + f" | chosen_from={args.secondary_tag}").strip()
            choose_secondary += 1
        else:
            chosen = dict(primary)
            chosen["notes"] = ((chosen.get("notes") or "") + f" | chosen_from={args.primary_tag}").strip()
        output_rows.append(chosen)

    out = Path(args.output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=primary_rows[0].keys())
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"rows={len(output_rows)}")
    print(f"secondary_chosen={choose_secondary}")
    print(f"output={out}")


if __name__ == "__main__":
    main()
