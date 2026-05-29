import csv
import re
import sys
from pathlib import Path

def normalize(text: str) -> str:
    t = (text or "").replace("\r", "\n").strip()
    t = re.sub(r"</?think>", "", t)
    t = re.sub(r"<\|.*?\|>", "", t)
    t = re.sub(r"dsl[_\\s-]*f+i+r+e+", "dsl_fire", t, flags=re.I)
    t = t.replace("```dsl_ffire", "```dsl_fire").replace("```dsdsl_fire", "```dsl_fire")

    block = re.search(r"```(?:\s*dsl_fire|\s*fire|\s*code|\s*python)?\s*(.*?)```", t, flags=re.S | re.I)
    body = block.group(1).strip() if block else t

    m = re.search(r"result\s*=\s*(.+)", body, flags=re.S | re.I)
    if m:
        expr = m.group(1)
    else:
        lines = [x.strip() for x in body.splitlines() if x.strip()]
        expr = next((x for x in lines if "(" in x or x in {"open","close","high","low","volume","vwap","pb","market_cap","industry"}), body)

    expr = expr.split("```")[0].strip()
    expr = expr.replace("`", "").strip()
    expr = re.sub(r"\s+", " ", expr)
    expr = expr.rstrip("。；;，, ")

    return f"```dsl_fire\nresult = {expr}\n```"

def main(inp, out):
    inp, out = Path(inp), Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with inp.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys())
    if "raw_prediction" not in fields:
        fields.append("raw_prediction")
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r["raw_prediction"] = r.get("prediction", "")
            r["prediction"] = normalize(r.get("prediction", ""))
            w.writerow(r)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/normalize_fire_predictions.py input.csv output.csv")
        raise SystemExit(2)
    main(sys.argv[1], sys.argv[2])
