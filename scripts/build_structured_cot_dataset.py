#!/usr/bin/env python3
import argparse
import json
import math
import random
import re
from pathlib import Path


FIELDS = "open, close, high, low, volume, vwap, pb, market_cap, industry"
CODEBLOCK_SYSTEM = (
    "你是一个金融量化因子 DSL 代码生成器。用户会给出自然语言金融想法。"
    "请先给出 4 行以内的结构化分析，再输出一个 Markdown fenced code block。"
    "代码块语言标记必须是 dsl_fire。代码块内只写一行 result = <合法 FIRE DSL 表达式>。"
    f"字段只能使用 {FIELDS}。"
)
CODEBLOCK_SUFFIX = (
    "\n\n请先给出 4 行以内结构化分析，格式固定为“字段 / 算子 / 窗口 / 方向”，"
    "然后输出 Markdown fenced code block，语言标记必须是 dsl_fire，"
    "代码块内只写一行 result = <DSL表达式>。"
)


def load_jsonl(path: Path):
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def dump_jsonl(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def strip_numbering(text: str) -> str:
    return re.sub(r"^\s*\d+\.\s*", "", text.strip())


def clean_value(text: str) -> str:
    value = text.strip().strip("。")
    value = value.replace("使用 ", "").replace("使用", "")
    value = value.replace("核心算子包括 ", "").replace("核心算子包括", "")
    value = value.replace("窗口参数包括 ", "").replace("窗口参数包括", "")
    value = value.replace("通常表示", "")
    value = value.replace("原始信号。", "原始信号")
    value = re.sub(r"\s+", " ", value)
    return value.strip("。 ").strip()


def parse_reasoning_text(reasoning_text: str):
    field_value = "未知"
    operator_value = "未知"
    window_value = "无"
    direction_value = "原始/正向"

    for raw_line in reasoning_text.splitlines():
        line = strip_numbering(raw_line)
        if not line:
            continue
        if "字段选择" in line:
            _, _, tail = line.partition("：")
            field_value = clean_value(tail) or field_value
        elif "算子选择" in line:
            _, _, tail = line.partition("：")
            parts = [p.strip() for p in tail.split("。") if p.strip()]
            for part in parts:
                if "核心算子包括" in part:
                    operator_value = clean_value(part) or operator_value
                elif "窗口参数包括" in part:
                    window_value = clean_value(part) or window_value
        elif "方向判断" in line:
            _, _, tail = line.partition("：")
            tail = clean_value(tail)
            if "没有显式 neg" in tail or "正向暴露或原始信号" in tail:
                direction_value = "原始/正向"
            elif tail:
                direction_value = tail

    return {
        "字段": field_value,
        "算子": operator_value,
        "窗口": window_value,
        "方向": direction_value,
    }


def normalize_expression(text: str) -> str:
    text = (text or "").strip()
    block = re.search(r"```(?:dsl_fire)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if block:
        text = block.group(1).strip()
    text = re.sub(r"^\s*result\s*=\s*", "", text)
    return text.strip()


def make_codeblock(expr: str) -> str:
    expr = normalize_expression(expr)
    return f"```dsl_fire\nresult = {expr}\n```"


def make_structured_cot_record(record):
    conversations = record["conversations"]
    user_text = conversations[1]["content"].strip()
    expr = conversations[-1]["content"].strip()
    reasoning_text = conversations[-1].get("reasoning_content", "")
    slots = parse_reasoning_text(reasoning_text)
    assistant_content = "\n".join(
        [
            f"字段: {slots['字段']}",
            f"算子: {slots['算子']}",
            f"窗口: {slots['窗口']}",
            f"方向: {slots['方向']}",
            "",
            make_codeblock(expr),
        ]
    )
    return {
        "conversations": [
            {"role": "system", "content": CODEBLOCK_SYSTEM, "reasoning_content": "", "tools": "", "tool_calls": ""},
            {
                "role": "user",
                "content": user_text + CODEBLOCK_SUFFIX,
                "reasoning_content": "",
                "tools": "",
                "tool_calls": "",
            },
            {"role": "assistant", "content": assistant_content, "reasoning_content": "", "tools": "", "tool_calls": ""},
        ]
    }


def build_structured_cot(reasoning_records):
    return [make_structured_cot_record(record) for record in reasoning_records]


def build_mixed_dataset(code_records, cot_records, cot_ratio: float, seed: int):
    if not 0 < cot_ratio < 1:
        raise ValueError("cot_ratio must be between 0 and 1.")
    rng = random.Random(seed)
    cot_needed = min(len(cot_records), math.ceil(len(code_records) * cot_ratio / (1.0 - cot_ratio)))
    cot_pool = cot_records[:]
    rng.shuffle(cot_pool)
    mixed = code_records + cot_pool[:cot_needed]
    rng.shuffle(mixed)
    return mixed, cot_needed


def main():
    parser = argparse.ArgumentParser(description="Build structured CoT and mixed SFT datasets for FIRE DSL.")
    parser.add_argument("--code_jsonl", required=True)
    parser.add_argument("--reasoning_jsonl", required=True)
    parser.add_argument("--structured_output", required=True)
    parser.add_argument("--mixed_output", required=True)
    parser.add_argument("--cot_ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    code_records = load_jsonl(Path(args.code_jsonl))
    reasoning_records = load_jsonl(Path(args.reasoning_jsonl))
    structured_cot = build_structured_cot(reasoning_records)
    mixed_records, cot_used = build_mixed_dataset(code_records, structured_cot, args.cot_ratio, args.seed)

    dump_jsonl(Path(args.structured_output), structured_cot)
    dump_jsonl(Path(args.mixed_output), mixed_records)

    print(f"plain_sft_records={len(code_records)}")
    print(f"structured_cot_records={len(structured_cot)}")
    print(f"mixed_records={len(mixed_records)}")
    print(f"cot_ratio_target={args.cot_ratio:.2f}")
    print(f"cot_records_used={cot_used}")


if __name__ == "__main__":
    main()
