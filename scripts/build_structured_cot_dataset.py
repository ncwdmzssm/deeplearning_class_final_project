#!/usr/bin/env python3
import argparse
import ast
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
ARITY_SYSTEM = (
    "你是一个金融量化因子 DSL 代码生成器。用户会给出自然语言金融想法。"
    "请先给出 6 行以内的结构化分析，再输出一个 Markdown fenced code block。"
    "分析必须覆盖字段、算子、参数、窗口/常数、合法性和方向。"
    "代码块语言标记必须是 dsl_fire。代码块内只写一行 result = <合法 FIRE DSL 表达式>。"
    f"字段只能使用 {FIELDS}，算子只能使用课程给定的 FIRE DSL 函数名。"
)
ARITY_SUFFIX = (
    "\n\n请先给出 6 行以内结构化分析，格式固定为“字段 / 算子 / 参数 / 窗口或常数 / 合法性 / 方向”，"
    "其中“参数”要检查每个算子的参数个数是否匹配 FIRE DSL 函数签名。"
    "然后输出 Markdown fenced code block，语言标记必须是 dsl_fire，"
    "代码块内只写一行 result = <DSL表达式>。"
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPERATOR_SOURCE = ROOT / "fire-dsl-data" / "tools" / "fire_operator_dsl.py"


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


def ordered_unique(values):
    seen = set()
    out = []
    for value in values:
        if value not in seen:
            out.append(value)
            seen.add(value)
    return out


def load_operator_signatures(path: Path):
    """Read FIRE DSL operator signatures without importing pandas-heavy runtime code."""
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    operator_names = set()
    signatures = {}

    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OPERATOR_SPECS":
                    if isinstance(node.value, ast.Dict):
                        for key in node.value.keys:
                            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                operator_names.add(key.value)

    for node in module.body:
        if not isinstance(node, ast.FunctionDef) or node.name not in operator_names:
            continue
        positional = list(node.args.posonlyargs) + list(node.args.args)
        max_args = len(positional)
        min_args = max_args - len(node.args.defaults)
        signatures[node.name] = (min_args, max_args)

    return signatures


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


def describe_expression(expr: str, operator_signatures: dict[str, tuple[int, int]]):
    expr = normalize_expression(expr)
    fallback = {
        "fields": [],
        "operators": [],
        "constants": [],
        "arity": "表达式解析失败",
        "validity": "Python 解析失败，需要修正括号或逗号",
        "direction": "原始/正向",
    }
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        return fallback

    fields = []
    operators = []
    constants = []
    arity_parts = []
    issues = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in FIELDS.replace(", ", ",").split(","):
                fields.append(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            constants.append(str(node.value))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                op = node.func.id
            else:
                op = ast.unparse(node.func)
            operators.append(op)
            actual = len(node.args) + len(node.keywords)
            if op not in operator_signatures:
                arity_parts.append(f"{op}: 未知算子")
                issues.append(f"未知算子 {op}")
                continue
            min_args, max_args = operator_signatures[op]
            expected = str(min_args) if min_args == max_args else f"{min_args}-{max_args}"
            ok = min_args <= actual <= max_args
            arity_parts.append(f"{op}: {actual}/{expected}{' OK' if ok else ' 错'}")
            if not ok:
                issues.append(f"{op} 参数个数 {actual} 不在 {expected} 范围")

    fields = ordered_unique(fields)
    operators = ordered_unique(operators)
    constants = ordered_unique(constants)
    direction = "包含 neg/反向" if "neg" in operators else "原始/正向"
    validity = "仅使用已知 FIRE 算子，参数数量匹配" if not issues else "；".join(issues[:3])

    return {
        "fields": fields,
        "operators": operators,
        "constants": constants,
        "arity": "；".join(arity_parts) if arity_parts else "无函数调用",
        "validity": validity,
        "direction": direction,
    }


def make_codeblock(expr: str) -> str:
    expr = normalize_expression(expr)
    return f"```dsl_fire\nresult = {expr}\n```"


def make_structured_cot_record(record, cot_style: str, operator_signatures: dict[str, tuple[int, int]]):
    conversations = record["conversations"]
    user_text = conversations[1]["content"].strip()
    expr = conversations[-1]["content"].strip()
    reasoning_text = conversations[-1].get("reasoning_content", "")
    slots = parse_reasoning_text(reasoning_text)
    if cot_style == "basic":
        system_text = CODEBLOCK_SYSTEM
        suffix = CODEBLOCK_SUFFIX
        assistant_lines = [
            f"字段: {slots['字段']}",
            f"算子: {slots['算子']}",
            f"窗口: {slots['窗口']}",
            f"方向: {slots['方向']}",
        ]
    elif cot_style == "arity":
        system_text = ARITY_SYSTEM
        suffix = ARITY_SUFFIX
        info = describe_expression(expr, operator_signatures)
        assistant_lines = [
            f"字段: {', '.join(info['fields']) if info['fields'] else slots['字段']}",
            f"算子: {', '.join(info['operators']) if info['operators'] else slots['算子']}",
            f"参数: {info['arity']}",
            f"窗口/常数: {', '.join(info['constants']) if info['constants'] else slots['窗口']}",
            f"合法性: {info['validity']}",
            f"方向: {info['direction'] or slots['方向']}",
        ]
    else:
        raise ValueError(f"Unknown cot_style: {cot_style}")

    assistant_content = "\n".join(assistant_lines + ["", make_codeblock(expr)])
    return {
        "conversations": [
            {"role": "system", "content": system_text, "reasoning_content": "", "tools": "", "tool_calls": ""},
            {
                "role": "user",
                "content": user_text + suffix,
                "reasoning_content": "",
                "tools": "",
                "tool_calls": "",
            },
            {"role": "assistant", "content": assistant_content, "reasoning_content": "", "tools": "", "tool_calls": ""},
        ]
    }


def build_structured_cot(reasoning_records, cot_style: str, operator_signatures: dict[str, tuple[int, int]]):
    return [make_structured_cot_record(record, cot_style, operator_signatures) for record in reasoning_records]


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
    parser.add_argument("--cot_style", choices=["basic", "arity"], default="basic")
    parser.add_argument("--operator_source", default=str(DEFAULT_OPERATOR_SOURCE))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    code_records = load_jsonl(Path(args.code_jsonl))
    reasoning_records = load_jsonl(Path(args.reasoning_jsonl))
    operator_signatures = load_operator_signatures(Path(args.operator_source))
    structured_cot = build_structured_cot(reasoning_records, args.cot_style, operator_signatures)
    mixed_records, cot_used = build_mixed_dataset(code_records, structured_cot, args.cot_ratio, args.seed)

    dump_jsonl(Path(args.structured_output), structured_cot)
    dump_jsonl(Path(args.mixed_output), mixed_records)

    print(f"plain_sft_records={len(code_records)}")
    print(f"structured_cot_records={len(structured_cot)}")
    print(f"mixed_records={len(mixed_records)}")
    print(f"cot_style={args.cot_style}")
    print(f"cot_ratio_target={args.cot_ratio:.2f}")
    print(f"cot_records_used={cot_used}")


if __name__ == "__main__":
    main()
