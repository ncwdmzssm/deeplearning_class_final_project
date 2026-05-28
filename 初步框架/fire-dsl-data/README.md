# FIRE DSL Student Training Data

This folder contains the recommended training data for the MiniMind final project:
translate natural-language financial factor ideas into normalized FIRE operator DSL.

## Recommended Files

Use this file as the default SFT dataset:

```text
train/fire_operator_dsl_sft_code.jsonl
```

This file includes the original validated course data plus additional proxy-mapped rows from `ideas(1).json`.
The augmentation-only rows are also available as:

```text
train/fire_operator_dsl_sft_code_ideas_augmented.jsonl
```

The target answer format is always:

```dsl_fire
result = div(sub(close, open), open)
```

Use this file for held-out/stress evaluation:

```text
eval/fire_operator_dsl_eval_code_generalization.jsonl
```

Use this file only for seen-style prompt checking:

```text
eval/fire_operator_dsl_eval_code_public.jsonl
```

## Optional Files

- `train/fire_operator_dsl_pretrain_domain.jsonl`: short domain/operator text for continued pretraining.
- `train/fire_operator_dsl_sft_train.jsonl`: auxiliary SFT data where the answer is only the bare DSL expression, not a code block.
- `train/fire_operator_dsl_sft_reasoning_short.jsonl`: optional short-reasoning data.
- `train/*_ideas_augmented.jsonl`: augmentation-only rows mapped from `ideas(1).json`.
- `docs/operator_catalog.csv`: normalized operator list.
- `docs/operator_dsl_case_library.csv`: validated source DSL case library.
- `docs/dataset_card.md`: detailed dataset notes.
- `docs/validation_report.json`: validation and coverage summary.
- `docs/ideas_dsl_augmentation_report.json`: summary of mapped and skipped rows from `ideas(1).json`.
- `docs/ideas_dsl_augmentation_mapped.csv`: mapped idea-to-DSL records.
- `docs/ideas_dsl_augmentation_skipped.csv`: skipped ideas and reasons.
- `tools/fire_operator_dsl.py`: pandas reference implementation of all course DSL operators, plus parser validation and synthetic demo data.
- `tools/demo_verify_dsl.py`: small runnable script for testing example DSL expressions.

## Field Standard

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
pct_change(close, 20)
where(gt(volume, ts_mean(volume, 20)), pct_change(close, 5), 0.0)
```

Do not use Python arithmetic syntax or old aliases.

## Important Note

This package intentionally excludes the current DPO/RLAIF/RLVR files because those files are not in the default fenced `dsl_fire` code-block answer format. They can be used later after format conversion or custom reward/evaluation code is prepared.

This package is the final course standard. Older exploratory notebooks in the parent workspace may use an earlier DSL with `rank`, `ts_returns`, `safe_div`, `open_price`, or `pb_ratio`. Do not use those names as answers for this final project.

## Local DSL Testing

Students can test generated DSL expressions without MiniMind training:

```bash
cd student_data
python tools/demo_verify_dsl.py
```

Minimal Python usage:

```python
from tools.fire_operator_dsl import make_synthetic_data, safe_eval_dsl, verify_expression

data = make_synthetic_data(seed=7, n_days=120, n_assets=10)
expr = "ts_mean(pct_change(close, 1), 20)"

verify_expression(expr, data)
result = safe_eval_dsl(expr, data)
print(result.tail())
```

The implementation in `tools/fire_operator_dsl.py` is a teaching/reference pandas implementation. It is designed for correctness checks and small demos, not high-performance CUDA execution.
