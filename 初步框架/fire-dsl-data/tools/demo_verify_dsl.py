#!/usr/bin/env python
from __future__ import annotations

from fire_operator_dsl import make_synthetic_data, safe_eval_dsl, verify_expression


EXAMPLES = [
    "pct_change(close, 20)",
    "ts_mean(pct_change(close, 1), 20)",
    "div(sub(recip(pb), xs_mean(recip(pb))), xs_std(recip(pb)))",
    "where(gt(volume, ts_mean(volume, 20)), pct_change(close, 5), pct_change(close, 20))",
    "div(sub(log(market_cap), group_mean(log(market_cap), industry)), group_std(log(market_cap), industry))",
]


def main() -> None:
    data = make_synthetic_data(seed=42, n_days=120, n_assets=10)
    for expr in EXAMPLES:
        print("=" * 80)
        print(expr)
        stats = verify_expression(expr, data, min_finite_ratio=0.20)
        result = safe_eval_dsl(expr, data)
        print("stats:", stats)
        print("tail sample:")
        print(result.tail(3).round(4))


if __name__ == "__main__":
    main()
