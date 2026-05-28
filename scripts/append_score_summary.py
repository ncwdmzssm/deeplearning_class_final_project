import argparse
import csv
import re
from pathlib import Path

FIELDS = [
    "run_name",
    "model_type",
    "train_data",
    "from_weight",
    "hidden_size",
    "num_layers",
    "max_seq_len",
    "batch_size",
    "learning_rate",
    "epochs",
    "eval_set",
    "prediction_csv",
    "score_log",
    "exact_dsl_match",
    "fenced_code_format",
    "python_parse_ok",
    "fire_dsl_executable",
    "format_error_rows",
    "parse_error_rows",
    "execution_error_rows",
    "notes",
]

def find_metric(text, name, default=""):
    m = re.search(rf"^{re.escape(name)}:\s*([0-9.]+)%?", text, flags=re.MULTILINE)
    return m.group(1) if m else default

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary_csv", default="results/summary_table.csv")
    ap.add_argument("--score_log", required=True)
    ap.add_argument("--prediction_csv", required=True)
    ap.add_argument("--run_name", required=True)
    ap.add_argument("--model_type", required=True)
    ap.add_argument("--train_data", required=True)
    ap.add_argument("--from_weight", required=True)
    ap.add_argument("--hidden_size", required=True)
    ap.add_argument("--num_layers", required=True)
    ap.add_argument("--max_seq_len", required=True)
    ap.add_argument("--batch_size", required=True)
    ap.add_argument("--learning_rate", required=True)
    ap.add_argument("--epochs", required=True)
    ap.add_argument("--eval_set", required=True)
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    text = Path(args.score_log).read_text(encoding="utf-8", errors="ignore")

    row = {
        "run_name": args.run_name,
        "model_type": args.model_type,
        "train_data": args.train_data,
        "from_weight": args.from_weight,
        "hidden_size": args.hidden_size,
        "num_layers": args.num_layers,
        "max_seq_len": args.max_seq_len,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
        "epochs": args.epochs,
        "eval_set": args.eval_set,
        "prediction_csv": args.prediction_csv,
        "score_log": args.score_log,
        "exact_dsl_match": find_metric(text, "exact_dsl_match"),
        "fenced_code_format": find_metric(text, "fenced_code_format"),
        "python_parse_ok": find_metric(text, "python_parse_ok"),
        "fire_dsl_executable": find_metric(text, "fire_dsl_executable"),
        "format_error_rows": find_metric(text, "format_error_rows"),
        "parse_error_rows": find_metric(text, "parse_error_rows"),
        "execution_error_rows": find_metric(text, "execution_error_rows"),
        "notes": args.notes,
    }

    out = Path(args.summary_csv)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_header = not out.exists()

    with out.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    print(f"Appended summary row to {out}")

if __name__ == "__main__":
    main()
