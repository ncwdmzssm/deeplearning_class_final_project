#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MINIMIND = ROOT / "minimind"
TOOLS = ROOT / "fire-dsl-data" / "tools"
sys.path.insert(0, str(MINIMIND))
sys.path.insert(0, str(TOOLS))

from model.model_lora import apply_lora, load_lora  # noqa: E402
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM  # noqa: E402
from fire_operator_dsl import make_synthetic_data, verify_expression  # noqa: E402


FENCE_RE = re.compile(r"```+\s*dsl_f*ire[a-z_]*\s*(.*?)\s*```+", flags=re.DOTALL | re.IGNORECASE)


def clean_generation(text: str) -> str:
    text = (text or "").strip()
    text = re.sub(r"</?think>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"```+\s*dsl_f*ire[a-z_]*", "```dsl_fire", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_model(args):
    tokenizer = AutoTokenizer.from_pretrained(args.load_from, trust_remote_code=True)
    if Path(args.load_from).name == "model":
        config = MiniMindConfig(
            hidden_size=args.hidden_size,
            num_hidden_layers=args.num_hidden_layers,
            use_moe=bool(args.use_moe),
            inference_rope_scaling=args.inference_rope_scaling,
        )
        model = MiniMindForCausalLM(config)
        moe_suffix = "_moe" if args.use_moe else ""
        weight_path = ROOT / args.save_dir / f"{args.weight}_{args.hidden_size}{moe_suffix}.pth"
        model.load_state_dict(torch.load(weight_path, map_location=args.device), strict=True)
        if args.lora_weight != "None":
            apply_lora(model)
            lora_path = ROOT / args.save_dir / f"{args.lora_weight}_{args.hidden_size}.pth"
            load_lora(model, str(lora_path))
    else:
        model = AutoModelForCausalLM.from_pretrained(args.load_from, trust_remote_code=True)
    return model.eval().to(args.device), tokenizer


def read_eval(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def extract_first_dsl_block(text: str) -> str:
    text = clean_generation(text)
    block = FENCE_RE.search(text)
    if block:
        body = re.sub(r"^\s*result\s*=\s*", "", block.group(1).strip())
        body = body.split("```", 1)[0].strip()
        return f"```dsl_fire\nresult = {body}\n```"

    line = re.search(r"result\s*=\s*(.+)", text, flags=re.DOTALL)
    if line:
        body = re.sub(r"^\s*result\s*=\s*", "", line.group(1).split("```", 1)[0].strip())
        return f"```dsl_fire\nresult = {body}\n```"

    expr_like = re.search(
        r"\b(?:add|sub|mul|div|neg|pct_change|ts_[a-z_]+|xs_[a-z_]+|group_[a-z_]+|where|mask)\s*\(.+",
        text,
        flags=re.DOTALL,
    )
    if expr_like:
        body = expr_like.group(0).split("```", 1)[0].strip()
        return f"```dsl_fire\nresult = {body}\n```"

    return text


def extract_dsl(text: str) -> str:
    text = text.strip()
    match = re.search(r"```dsl_fire\s*result\s*=\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    if text.startswith("result ="):
        return text.split("=", 1)[1].strip()
    return text


def is_fenced_code(text: str) -> bool:
    return bool(re.search(r"^```dsl_fire\s*result\s*=\s*.+?\s*```$", text.strip(), flags=re.DOTALL | re.IGNORECASE))


def parse_ok(expr: str) -> bool:
    try:
        import ast

        ast.parse(expr, mode="eval")
        return True
    except SyntaxError:
        return False


def verify_ok(expr: str, data) -> bool:
    try:
        verify_expression(expr, data)
        return True
    except Exception:
        return False


def candidate_score(prediction: str, data):
    normalized = extract_first_dsl_block(prediction)
    expr = extract_dsl(normalized)
    fenced = is_fenced_code(normalized)
    parsed = parse_ok(expr)
    verified = parsed and verify_ok(expr, data)
    # Rank by executable > parseable > fenced, then shorter outputs
    score = (
        100 if verified else 0,
        10 if parsed else 0,
        1 if fenced else 0,
        -len(expr),
    )
    return score, normalized, expr, fenced, parsed, verified


@torch.no_grad()
def generate_candidates(model, tokenizer, prompt, args):
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=args.max_input_tokens).to(args.device)

    outputs = []
    for _ in range(args.num_candidates):
        generated = model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs.get("attention_mask"),
            max_new_tokens=args.max_new_tokens,
            do_sample=True,
            temperature=args.temperature,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
        new_tokens = generated[0][inputs["input_ids"].shape[1] :]
        outputs.append(tokenizer.decode(new_tokens, skip_special_tokens=True).strip())
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch inference with verifier rerank for FIRE DSL.")
    parser.add_argument("--eval_jsonl", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--load_from", default=str(MINIMIND / "model"))
    parser.add_argument("--save_dir", default="out")
    parser.add_argument("--weight", required=True)
    parser.add_argument("--lora_weight", default="None")
    parser.add_argument("--hidden_size", type=int, default=128)
    parser.add_argument("--num_hidden_layers", type=int, default=2)
    parser.add_argument("--use_moe", type=int, default=0)
    parser.add_argument("--inference_rope_scaling", action="store_true")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max_input_tokens", type=int, default=768)
    parser.add_argument("--max_new_tokens", type=int, default=192)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--repetition_penalty", type=float, default=1.0)
    parser.add_argument("--num_candidates", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    model, tokenizer = load_model(args)
    data = make_synthetic_data(seed=7, n_days=120, n_assets=10)

    output = Path(args.output_csv)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = read_eval(Path(args.eval_jsonl))
    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
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
        for idx, item in enumerate(rows, 1):
            if args.limit and idx > args.limit:
                break

            candidates = generate_candidates(model, tokenizer, item["prompt"], args)
            scored = [candidate_score(candidate, data) for candidate in candidates]
            best = max(scored, key=lambda x: x[0])
            prediction = best[1]
            notes = json.dumps(
                {
                    "num_candidates": len(candidates),
                    "best_score": list(best[0]),
                    "best_parsed": best[4],
                    "best_verified": best[5],
                },
                ensure_ascii=False,
            )
            writer.writerow(
                {
                    "id": item.get("id", ""),
                    "split_type": item.get("split_type", ""),
                    "family": item.get("family", ""),
                    "prompt": item.get("prompt", ""),
                    "expected_dsl": item.get("expected_dsl", ""),
                    "expected_code": item.get("expected_code", ""),
                    "prediction": prediction,
                    "manual_score": "",
                    "notes": notes,
                }
            )
            print(
                f"[{idx}] {item.get('id', '')}: parsed={best[4]} verified={best[5]} "
                f"{prediction[:120].replace(chr(10), ' ')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
