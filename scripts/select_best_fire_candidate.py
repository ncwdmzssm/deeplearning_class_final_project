import ast, csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "fire-dsl-data" / "tools"))
from fire_operator_dsl import make_synthetic_data, verify_expression

def normalize(text):
    t = (text or "").replace("\r", "\n").strip()
    t = re.sub(r"</?think>", "", t)
    t = re.sub(r"<\|.*?\|>", "", t)
    t = re.sub(r"dsl[_\s-]*f+i+r+e+", "dsl_fire", t, flags=re.I)
    block = re.search(r"```(?:\s*dsl_fire|\s*fire|\s*code|\s*python)?\s*(.*?)```", t, flags=re.S | re.I)
    body = block.group(1).strip() if block else t
    m = re.search(r"result\s*=\s*(.+)", body, flags=re.S | re.I)
    expr = m.group(1) if m else body
    expr = expr.split("```")[0].replace("`", "").strip()
    expr = re.sub(r"\s+", " ", expr).rstrip("。；;，, ")
    return f"```dsl_fire\nresult = {expr}\n```", expr

def parse_ok(expr):
    try:
        ast.parse(expr, mode="eval")
        return True
    except Exception:
        return False

def main(out_path, in_paths):
    data = make_synthetic_data(seed=7, n_days=120, n_assets=10)
    tables = []
    for p in in_paths:
        with Path(p).open("r", encoding="utf-8-sig", newline="") as f:
            tables.append(list(csv.DictReader(f)))

    fields = list(tables[0][0].keys())
    for x in ["selected_candidate", "candidate_scores"]:
        if x not in fields:
            fields.append(x)

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()

        for idx in range(len(tables[0])):
            base = dict(tables[0][idx])
            best = None
            notes = []

            for ci, table in enumerate(tables, 1):
                norm, expr = normalize(table[idx].get("prediction", ""))
                parsed = parse_ok(expr)
                executable = False

                if parsed:
                    try:
                        verify_expression(expr, data)
                        executable = True
                    except Exception:
                        pass

                score = (100 if executable else 0) + (20 if parsed else 0)
                notes.append(f"c{ci}:score={score},parse={parsed},exec={executable}")

                if best is None or score > best[0]:
                    best = (score, ci, norm)

            base["prediction"] = best[2]
            base["selected_candidate"] = best[1]
            base["candidate_scores"] = " | ".join(notes)
            w.writerow(base)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
