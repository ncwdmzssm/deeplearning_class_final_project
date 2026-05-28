import csv
import json
import sys
from pathlib import Path


def convert(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("r", encoding="utf-8") as f, dst.open("w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(
            out,
            fieldnames=[
                "id",
                "split_type",
                "family",
                "prompt",
                "expected_dsl",
                "expected_code",
                "prediction",
                "manual_score",
                "notes",
            ],
        )
        writer.writeheader()
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            writer.writerow(
                {
                    "id": item.get("id", ""),
                    "split_type": item.get("split_type", ""),
                    "family": item.get("family", ""),
                    "prompt": item.get("prompt", ""),
                    "expected_dsl": item.get("expected_dsl", ""),
                    "expected_code": item.get("expected_code", ""),
                    "prediction": "TODO",
                    "manual_score": "TODO",
                    "notes": "TODO",
                }
            )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/make_fire_eval_csv.py <eval.jsonl> <out.csv>")
        raise SystemExit(2)
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
