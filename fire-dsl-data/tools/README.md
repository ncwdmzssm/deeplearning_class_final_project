# FIRE Operator DSL Python Reference

This folder contains a small pandas reference implementation for the FIRE operator DSL used in the course dataset.

It is intended for teaching, debugging, and dataset/model-output checks. It is not a CUDA performance implementation.

## Files

- `fire_operator_dsl.py`: standard Python implementation of the allowed fields, operators, parser whitelist, synthetic data generator, and expression verifier.
- `demo_verify_dsl.py`: runnable examples showing how to validate and execute DSL expressions.

## Quick Test

From this folder:

```bash
python demo_verify_dsl.py
```

Or from the student package root:

```bash
python tools/demo_verify_dsl.py
```

## Minimal Usage

```python
from tools.fire_operator_dsl import make_synthetic_data, safe_eval_dsl, verify_expression

data = make_synthetic_data(seed=7, n_days=120, n_assets=10)
expr = "ts_mean(pct_change(close, 1), 20)"

verify_expression(expr, data)
result = safe_eval_dsl(expr, data)
print(result.tail())
```

## Supported Fields

Value fields:

```text
open, close, high, low, volume, vwap, pb, market_cap
```

Category field:

```text
industry
```

## Notes

- Use function-style DSL only, for example `div(sub(close, open), open)`.
- Do not use Python arithmetic syntax such as `close - open`.
- The evaluator intentionally whitelists only course operators and fields.
- All operators return pandas `DataFrame` values aligned by date and asset, except `industry`, which is used as a grouping label.
