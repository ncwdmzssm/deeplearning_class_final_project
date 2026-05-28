import json
import sys
from pathlib import Path


def validate(path: Path) -> int:
    errors = 0
    count = 0
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            count += 1
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"{path}:{line_no}: invalid JSON: {exc}")
                errors += 1
                continue

            conversations = item.get("conversations")
            if not isinstance(conversations, list) or len(conversations) < 2:
                print(f"{path}:{line_no}: conversations must be a list with at least 2 messages")
                errors += 1
                continue

            for idx, msg in enumerate(conversations):
                if msg.get("role") not in {"system", "user", "assistant", "tool"}:
                    print(f"{path}:{line_no}: message {idx} has invalid role: {msg.get('role')!r}")
                    errors += 1
                if not isinstance(msg.get("content"), str):
                    print(f"{path}:{line_no}: message {idx} content must be a string")
                    errors += 1

            if conversations[-1].get("role") != "assistant":
                print(f"{path}:{line_no}: last message should be assistant for SFT")
                errors += 1

    print(f"{path}: {count} records checked, {errors} errors")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_jsonl.py <file.jsonl> [more.jsonl...]")
        raise SystemExit(2)

    status = 0
    for arg in sys.argv[1:]:
        status |= validate(Path(arg))
    raise SystemExit(status)
