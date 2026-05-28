import ast
import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "fire-dsl-data" / "tools"
sys.path.insert(0, str(TOOLS))


def extract_dsl(text: str) -> str:
    text = text.strip()
    match = re.search(r"```dsl_fire\s*result\s*=\s*(.*?)\s*```", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    if text.startswith("result ="):
        return text.split("=", 1)[1].strip()
    return text


def is_fenced_code(text: str) -> bool:
    return bool(re.search(r"^```dsl_fire\s*result\s*=\s*.+?\s*```$", text.strip(), flags=re.DOTALL))


def parse_ok(expr: str) -> bool:
    try:
        ast.parse(expr, mode="eval")
        return True
    except SyntaxError:
        return False


def main(path: Path) -> int:
    try:
        from fire_operator_dsl import make_synthetic_data, verify_expression
    except ImportError as exc:
        print(f"Cannot import FIRE DSL tools: {exc}")
        return 1

    data = make_synthetic_data(seed=7, n_days=120, n_assets=10)

    total = 0
    exact = 0
    fenced = 0
    parsed = 0
    executable = 0
    format_errors = 0
    parse_errors = 0
    exec_errors = 0
    skipped = 0

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"expected_dsl", "prediction"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print(f"Missing columns: {sorted(missing)}")
            return 2

        for row in reader:
            prediction = row["prediction"].strip()
            if not prediction or prediction.upper() == "TODO":
                skipped += 1
                continue

            total += 1
            expected = row["expected_dsl"].strip()
            pred_dsl = extract_dsl(prediction)

            if pred_dsl == expected:
                exact += 1
            if is_fenced_code(prediction):
                fenced += 1
            else:
                format_errors += 1
            if parse_ok(pred_dsl):
                parsed += 1
            else:
                parse_errors += 1
            try:
                verify_expression(pred_dsl, data)
                executable += 1
            except Exception:
                exec_errors += 1

    print(f"file: {path}")
    print(f"scored_rows: {total}")
    print(f"skipped_todo_rows: {skipped}")
    if total == 0:
        print("No scored rows found. Fill prediction column before formal evaluation.")
        return 0
    print(f"exact_dsl_match: {exact / total:.2%}")
    print(f"fenced_code_format: {fenced / total:.2%}")
    print(f"python_parse_ok: {parsed / total:.2%}")
    print(f"fire_dsl_executable: {executable / total:.2%}")
    print(f"format_error_rows: {format_errors}")
    print(f"parse_error_rows: {parse_errors}")
    print(f"execution_error_rows: {exec_errors}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/score_fire_predictions.py results/fire_eval_predictions.csv")
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
