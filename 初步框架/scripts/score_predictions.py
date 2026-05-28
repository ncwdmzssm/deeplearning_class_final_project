import csv
import re
import sys
from pathlib import Path


KNOWN_FUNCTIONS = {
    "rank",
    "delay",
    "delta",
    "correlation",
    "covariance",
    "ts_mean",
    "ts_sum",
    "ts_std",
    "ts_rank",
    "ts_min",
    "ts_max",
    "decay_linear",
    "signedpower",
    "scale",
    "indneutralize",
}


KNOWN_FIELDS = {"open", "close", "high", "low", "volume", "vwap", "returns", "industry"}


def balanced_parentheses(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def extract_functions(text: str) -> set[str]:
    return set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", text))


def main(path: Path) -> int:
    total = 0
    syntax_ok = 0
    function_ok = 0
    hallucination = 0

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"question", "expected", "prediction"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            print(f"Missing columns: {sorted(missing)}")
            return 2

        for row in reader:
            if row["prediction"].strip().upper() == "TODO":
                continue
            total += 1
            pred = row["prediction"].strip()
            expected = row["expected"].strip()
            if balanced_parentheses(pred):
                syntax_ok += 1

            expected_funcs = extract_functions(expected)
            pred_funcs = extract_functions(pred)
            if expected_funcs and expected_funcs <= pred_funcs:
                function_ok += 1
            elif not expected_funcs:
                function_ok += 1

            unknown_funcs = pred_funcs - KNOWN_FUNCTIONS
            unknown_words = {
                w
                for w in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", pred)
                if w not in KNOWN_FUNCTIONS and w not in KNOWN_FIELDS
            }
            if unknown_funcs or unknown_words:
                hallucination += 1

    if total == 0:
        print("No scored rows found. Fill the prediction column before formal evaluation.")
        return 0

    print(f"file: {path}")
    print(f"total: {total}")
    print(f"dsl_syntax_accuracy: {syntax_ok / total:.2%}")
    print(f"function_accuracy: {function_ok / total:.2%}")
    print(f"hallucination_rate: {hallucination / total:.2%}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/score_predictions.py results/predictions.csv")
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1])))
