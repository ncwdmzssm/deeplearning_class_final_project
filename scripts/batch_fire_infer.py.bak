import argparse
import csv
import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[1]
MINIMIND = ROOT / "minimind"
sys.path.insert(0, str(MINIMIND))

from model.model_lora import apply_lora, load_lora  # noqa: E402
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM  # noqa: E402


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


@torch.no_grad()
def generate_one(model, tokenizer, prompt, args):
    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=args.max_input_tokens).to(args.device)
    generated = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs.get("attention_mask"),
        max_new_tokens=args.max_new_tokens,
        do_sample=args.temperature > 0,
        temperature=args.temperature if args.temperature > 0 else None,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
    new_tokens = generated[0][inputs["input_ids"].shape[1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch inference for FIRE DSL eval JSONL.")
    parser.add_argument("--eval_jsonl", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--load_from", default=str(MINIMIND / "model"))
    parser.add_argument("--save_dir", default="out")
    parser.add_argument("--weight", default="fire_dsl_baseline")
    parser.add_argument("--lora_weight", default="None")
    parser.add_argument("--hidden_size", type=int, default=128)
    parser.add_argument("--num_hidden_layers", type=int, default=2)
    parser.add_argument("--use_moe", type=int, default=0)
    parser.add_argument("--inference_rope_scaling", action="store_true")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--max_input_tokens", type=int, default=768)
    parser.add_argument("--max_new_tokens", type=int, default=128)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--repetition_penalty", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit for smoke tests.")
    args = parser.parse_args()

    model, tokenizer = load_model(args)
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
            prediction = generate_one(model, tokenizer, item["prompt"], args)
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
                    "notes": "",
                }
            )
            print(f"[{idx}] {item.get('id', '')}: {prediction[:120].replace(chr(10), ' ')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
