import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIRE = ROOT / "fire-dsl-data"


def count_jsonl(path: Path):
    count = 0
    first = None
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            count += 1
            if first is None:
                first = json.loads(line)
    return count, first


def check_sft_code(path: Path) -> list[str]:
    errors = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            item = json.loads(line)
            conv = item.get("conversations", [])
            if len(conv) < 2:
                errors.append(f"{path}:{i}: missing conversations")
                continue
            answer = conv[-1].get("content", "")
            if not answer.startswith("```dsl_fire\nresult = ") or not answer.rstrip().endswith("\n```"):
                errors.append(f"{path}:{i}: assistant answer is not fenced dsl_fire result format")
            if len(errors) >= 10:
                break
    return errors


def check_eval(path: Path) -> list[str]:
    errors = []
    required = {"id", "prompt", "expected_dsl", "expected_code"}
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            item = json.loads(line)
            missing = required - set(item)
            if missing:
                errors.append(f"{path}:{i}: missing {sorted(missing)}")
                continue
            code = item["expected_code"]
            if not code.startswith("```dsl_fire\nresult = ") or not code.rstrip().endswith("\n```"):
                errors.append(f"{path}:{i}: expected_code is not fenced dsl_fire result format")
            if len(errors) >= 10:
                break
    return errors


def main() -> int:
    files = sorted(FIRE.glob("**/*.jsonl"))
    for path in files:
        count, first = count_jsonl(path)
        rel = path.relative_to(ROOT)
        print(f"{rel}: {count} records")
        if "sft_code" in path.name:
            errors = check_sft_code(path)
        elif "eval_code" in path.name:
            errors = check_eval(path)
        else:
            errors = []
        if errors:
            print("  errors:")
            for err in errors:
                print(f"  - {err}")
        else:
            print("  schema/format check: ok or not applicable")
        if first:
            print(f"  first keys: {', '.join(first.keys())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
