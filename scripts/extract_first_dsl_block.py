#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path


FENCE_RE = re.compile(r"```+\s*dsl_f*ire[a-z_]*\s*(.*?)\s*```+", flags=re.DOTALL | re.IGNORECASE)


def clean_generation(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"</?think>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"```+\s*dsl_f*ire[a-z_]*", "```dsl_fire", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_expression(text: str) -> str:
    text = clean_generation(text)
    text = re.sub(r"^```dsl_fire\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = re.sub(r"^\s*result\s*=\s*", "", text)
    text = text.split("```", 1)[0]
    return text.strip()


def extract_first_dsl_block(text: str) -> str:
    text = clean_generation(text)
    block = FENCE_RE.search(text)
    if block:
        expr = normalize_expression(block.group(1))
        return f"```dsl_fire\nresult = {expr}\n```"

    line = re.search(r"result\s*=\s*(.+)", text, flags=re.DOTALL)
    if line:
        expr = normalize_expression(line.group(1).split("```", 1)[0])
        return f"```dsl_fire\nresult = {expr}\n```"

    expr_like = re.search(
        r"\b(?:add|sub|mul|div|neg|pct_change|ts_[a-z_]+|xs_[a-z_]+|group_[a-z_]+|where|mask)\s*\(.+",
        text,
        flags=re.DOTALL,
    )
    if expr_like:
        expr = normalize_expression(expr_like.group(0))
        return f"```dsl_fire\nresult = {expr}\n```"

    return text


def main():
    parser = argparse.ArgumentParser(description="Extract the first fenced dsl_fire block from prediction CSV.")
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--column", default="prediction")
    args = parser.parse_args()

    src = Path(args.input_csv)
    dst = Path(args.output_csv)
    dst.parent.mkdir(parents=True, exist_ok=True)

    with src.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = []
        for row in reader:
            row = dict(row)
            row[args.column] = extract_first_dsl_block(row.get(args.column, ""))
            rows.append(row)

    with dst.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"rows={len(rows)}")
    print(f"output={dst}")


if __name__ == "__main__":
    main()
