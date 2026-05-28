import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
MINIMIND = ROOT / "minimind"
TERMS = ROOT / "data" / "finance_dsl_terms.txt"


def main() -> int:
    sys.path.insert(0, str(MINIMIND))
    try:
        from transformers import AutoTokenizer
    except ImportError:
        return fallback_vocab_analysis()

    tokenizer_path = MINIMIND / "model"
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_path), trust_remote_code=True)

    print("term,token_count,token_ids,decoded")
    for raw in TERMS.read_text(encoding="utf-8").splitlines():
        term = raw.strip()
        if not term:
            continue
        ids = tokenizer(term, add_special_tokens=False).input_ids
        decoded = tokenizer.decode(ids).replace("\n", "\\n")
        print(f"{term},{len(ids)},{ids},{decoded}")
    return 0


def fallback_vocab_analysis() -> int:
    tokenizer_json = MINIMIND / "model" / "tokenizer.json"
    if not tokenizer_json.exists():
        print(f"Missing tokenizer file: {tokenizer_json}")
        return 1

    data = json.loads(tokenizer_json.read_text(encoding="utf-8"))
    vocab = data.get("model", {}).get("vocab", {})
    added = {item.get("content"): item.get("id") for item in data.get("added_tokens", [])}

    print("transformers is not installed; using tokenizer.json vocabulary fallback.")
    print("term,exact_vocab_match,token_id,related_vocab_pieces")
    for raw in TERMS.read_text(encoding="utf-8").splitlines():
        term = raw.strip()
        if not term:
            continue
        token_id = vocab.get(term, added.get(term))
        related = [piece for piece in vocab if term.lower() in piece.lower() or piece.lower() in term.lower()]
        related = sorted(related, key=len, reverse=True)[:8]
        related_text = " ".join(related).encode("ascii", errors="backslashreplace").decode("ascii")
        print(f"{term},{token_id is not None},{token_id},{related_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
