import csv
import re
import sys
from collections import Counter
from pathlib import Path

from score_fire_predictions import extract_dsl, is_fenced_code, parse_ok


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "fire-dsl-data" / "tools"))


def classify(row, verify_expression, data):
    prediction = row["prediction"].strip()
    if not prediction or prediction.upper() == "TODO":
        return "todo"
    pred_dsl = extract_dsl(prediction)
    if pred_dsl == row["expected_dsl"].strip():
        return "exact_match"
    if not is_fenced_code(prediction):
        return "format_error"
    if not parse_ok(pred_dsl):
        return "parse_error"
    try:
        verify_expression(pred_dsl, data)
    except Exception:
        return "execution_error"
    if re.search(r"\b(rank|ts_returns|safe_div|open_price|pb_ratio)\b", pred_dsl):
        return "legacy_token_error"
    return "semantic_mismatch"


def main(path: Path, out_path: Path | None) -> int:
    from fire_operator_dsl import make_synthetic_data, verify_expression

    data = make_synthetic_data(seed=7, n_days=120, n_assets=10)
    counts = Counter()
    annotated = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            label = classify(row, verify_expression, data)
            counts[label] += 1
            row["error_type"] = label
            annotated.append(row)

    print(f"file: {path}")
    for label, count in counts.most_common():
        print(f"{label}: {count}")

    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = list(annotated[0].keys()) if annotated else []
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(annotated)
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in {2, 3}:
        print("Usage: python scripts/analyze_fire_errors.py <predictions.csv> [annotated_out.csv]")
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None))
