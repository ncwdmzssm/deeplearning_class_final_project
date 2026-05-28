# FIRE Operator DSL Dataset

This is a fast, trainable course dataset for MiniMind. It teaches the model to translate natural-language financial factor ideas into normalized FIRE operator DSL.

## Recommended Training Entry

Use this file first:

```text
train/fire_operator_dsl_sft_code.jsonl
```

This file now includes:

- the original validated course SFT rows;
- additional rows mapped from `ideas(1).json`.

The augmentation-only rows are kept separately as `train/fire_operator_dsl_sft_code_ideas_augmented.jsonl` for inspection.

The assistant answer is always a fenced `dsl_fire` code block:

```dsl_fire
result = div(sub(close, open), open)
```

Use `train/fire_operator_dsl_sft_train.jsonl` only when you want the model to output the bare expression:

```text
div(sub(close, open), open)
```

The mixed-format DPO/RLAIF/RLVR files from the full internal dataset are intentionally not included in this student package. They are not the default code-block SFT target.

This package is the final project standard. Older exploratory notebooks may mention `rank`, `ts_returns`, `safe_div`, `open_price`, or `pb_ratio`; those names are not valid answers for this dataset.

## Field And DSL Standard

Allowed value fields:

```text
open, close, high, low, volume, vwap, pb, market_cap
```

Allowed category field:

```text
industry
```

Use function-style DSL only:

```text
div(sub(close, open), open)
neg(pct_change(close, 5))
where(gt(volume, ts_mean(volume, 20)), pct_change(close, 5), 0.0)
```

Do not use Python arithmetic syntax, legacy field aliases, non-standard helper names, return aliases, or unsupported ranking syntax.

## File Guide

- `train/fire_operator_dsl_pretrain_domain.jsonl`: domain/operator reading text, format `{"text": ...}`.
- `train/fire_operator_dsl_sft_code.jsonl`: default MiniMind SFT data for fenced `dsl_fire` code-block generation.
- `train/fire_operator_dsl_sft_train.jsonl`: auxiliary plain-expression SFT data.
- `train/fire_operator_dsl_sft_reasoning_short.jsonl`: compact reasoning SFT data derived from the validated reasoning file.
- `train/fire_operator_dsl_sft_code_ideas_augmented.jsonl`: code-block SFT rows mapped from `ideas(1).json`.
- `train/fire_operator_dsl_sft_train_ideas_augmented.jsonl`: plain-expression augmentation-only SFT rows.
- `train/fire_operator_dsl_sft_reasoning_short_ideas_augmented.jsonl`: short-reasoning augmentation-only SFT rows.
- `train/fire_operator_dsl_pretrain_domain_ideas_augmented.jsonl`: domain text derived from mapped ideas.
- `eval/fire_operator_dsl_eval_code_public.jsonl`: visible/seen-style evaluation prompts. Use this to check whether training learned the format and common mappings.
- `eval/fire_operator_dsl_eval_code_generalization.jsonl`: held-out/stress evaluation prompts with unseen DSL combinations. Use this as the main generalization check.
- `docs/operator_dsl_case_library.csv`: source natural-language ideas and DSL expressions.
- `docs/operator_catalog.csv`: normalized operator list.
- `docs/validation_report.json`: validation counts and execution metadata.
- `tools/fire_operator_dsl.py`: pandas reference implementation of the course DSL operators and validator.
- `tools/demo_verify_dsl.py`: example script that validates and executes several representative DSL expressions.

## Practical Course Recommendation

For the first student run:

```text
SFT: train/fire_operator_dsl_sft_code.jsonl
Seen eval: eval/fire_operator_dsl_eval_code_public.jsonl
Held-out/stress eval: eval/fire_operator_dsl_eval_code_generalization.jsonl
Optional: train/fire_operator_dsl_sft_reasoning_short.jsonl
```

The existing DSL expressions were parsed and executed on synthetic OHLCV-style data during dataset construction. This fast version avoids re-running the expensive full candidate-generation pipeline and packages the already validated data into a stable training format.

## Ideas Augmentation

`ideas(1).json` contains broad factor research ideas. Many ideas mention information that is not available in the course field set, such as market indexes, accounting fundamentals, analyst forecasts, news sentiment, options, or order-book data.

For this package, those ideas were handled conservatively:

- ideas that can be represented with `open, close, high, low, volume, vwap, pb, market_cap, industry` were converted to executable DSL;
- ideas requiring unavailable data were either skipped or mapped to an explicit price/volume/value/size/industry proxy;
- every generated DSL expression was parsed and executed on synthetic OHLCV-style data before being added.

Inspection files:

```text
docs/ideas_dsl_augmentation_report.json
docs/ideas_dsl_augmentation_mapped.csv
docs/ideas_dsl_augmentation_skipped.csv
```

## Operator Reference Implementation

The student package includes a small Python implementation for testing generated expressions:

```bash
python tools/demo_verify_dsl.py
```

Example:

```python
from tools.fire_operator_dsl import make_synthetic_data, safe_eval_dsl, verify_expression

data = make_synthetic_data(seed=7, n_days=120, n_assets=10)
expr = "where(gt(volume, ts_mean(volume, 20)), pct_change(close, 5), pct_change(close, 20))"

verify_expression(expr, data)
result = safe_eval_dsl(expr, data)
```

This reference implementation is for teaching, debugging, and local validation. It is not intended to be numerically identical to every CUDA kernel detail in FIRE-Ops.
