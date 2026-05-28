from __future__ import annotations

import ast
import re
from typing import Any

import numpy as np
import pandas as pd


EPS = 1e-12

VALUE_FIELDS = (
    "open",
    "close",
    "high",
    "low",
    "volume",
    "vwap",
    "pb",
    "market_cap",
)

CATEGORY_FIELDS = ("industry",)

OPERATOR_SPECS = {
    "absolute": ("对输入信号逐元素取绝对值。", "DVM Pack + FactorSearch"),
    "add": ("对两个同类型信号或信号与常数逐元素相加。", "DVM Pack + FactorSearch"),
    "cbrt": ("对 Value 信号逐元素取立方根。", "FactorSearch"),
    "diff": ("计算时间窗口内的差分变化。", "DVM Pack + FactorSearch"),
    "div": ("对两个信号逐元素相除，常用于构造比值或比例因子。", "DVM Pack + FactorSearch"),
    "eq": ("判断两个输入是否逐元素相等，输出布尔条件信号。", "DVM Pack + FactorSearch"),
    "exp": ("对 Value 信号逐元素做指数变换。", "FactorSearch"),
    "ge": ("判断第一个输入是否逐元素大于等于第二个输入。", "DVM Pack + FactorSearch"),
    "group_mean": ("按类别分组计算均值或组内统计值。", "FactorSearch"),
    "group_std": ("按类别分组计算标准差或组内标准化统计。", "DVM Pack + FactorSearch"),
    "gt": ("判断第一个输入是否逐元素大于第二个输入。", "DVM Pack + FactorSearch"),
    "le": ("判断第一个输入是否逐元素小于等于第二个输入。", "DVM Pack + FactorSearch"),
    "log": ("对正值信号逐元素取自然对数。", "DVM Pack + FactorSearch"),
    "log10": ("对正值信号逐元素取以 10 为底的对数。", "FactorSearch"),
    "log1p": ("对输入逐元素计算 log(1 + x)，适合处理小幅变化或非负值。", "FactorSearch"),
    "logical_and": ("对两个布尔信号逐元素执行逻辑与。", "DVM Pack + FactorSearch"),
    "logical_not": ("对布尔信号逐元素取反。", "FactorSearch"),
    "logical_or": ("对两个布尔信号逐元素执行逻辑或。", "DVM Pack + FactorSearch"),
    "logical_xor": ("对两个布尔信号逐元素执行逻辑异或。", "FactorSearch"),
    "lt": ("判断第一个输入是否逐元素小于第二个输入。", "DVM Pack + FactorSearch"),
    "mask": ("根据布尔条件保留、替换或屏蔽对应位置的数值。", "DVM Pack + FactorSearch"),
    "maximum": ("对两个输入逐元素取较大值。", "DVM Pack"),
    "minimum": ("对两个输入逐元素取较小值。", "DVM Pack"),
    "mod": ("对两个同类型 Value 信号逐元素取模。", "FactorSearch"),
    "mul": ("对两个信号或信号与常数逐元素相乘。", "DVM Pack + FactorSearch"),
    "ne": ("判断两个输入是否逐元素不相等，输出布尔条件信号。", "DVM Pack + FactorSearch"),
    "neg": ("对输入信号逐元素取负。", "DVM Pack + FactorSearch"),
    "pct_change": ("计算时间窗口内的百分比变化或收益率。", "DVM Pack + FactorSearch"),
    "pos": ("提取输入信号的正向部分或正值变换。", "FactorSearch"),
    "power": ("对输入信号逐元素做幂运算。", "DVM Pack + FactorSearch"),
    "recip": ("对输入信号逐元素取倒数。", "FactorSearch"),
    "shift": ("将时间序列信号按窗口或步长滞后，用于引用历史值。", "DVM Pack + FactorSearch"),
    "sign": ("对输入信号逐元素取符号。", "FactorSearch"),
    "sqrt": ("对非负 Value 信号逐元素取平方根。", "DVM Pack + FactorSearch"),
    "square": ("对输入信号逐元素平方。", "FactorSearch"),
    "sub": ("对两个信号或信号与常数逐元素相减。", "DVM Pack + FactorSearch"),
    "ts_argmax": ("在时间窗口内寻找最大值对应的位置或序号。", "FactorSearch"),
    "ts_argmaxmin": ("在时间窗口内比较最大值与最小值位置关系或相关序号统计。", "FactorSearch"),
    "ts_argmin": ("在时间窗口内寻找最小值对应的位置或序号。", "FactorSearch"),
    "ts_corr": ("在时间窗口内计算两个信号的滚动相关性。", "FactorSearch"),
    "ts_last": ("取时间窗口内最后一个有效观测值。", "FactorSearch"),
    "ts_max": ("计算时间窗口内的滚动最大值。", "FactorSearch"),
    "ts_mean": ("计算时间窗口内均值，也可用于分钟数据聚合到日频。", "DVM Pack + FactorSearch"),
    "ts_min": ("计算时间窗口内的滚动最小值。", "DVM Pack + FactorSearch"),
    "ts_prod": ("计算时间窗口内的滚动乘积。", "FactorSearch"),
    "ts_quantile": ("计算时间窗口内的滚动分位数。", "FactorSearch"),
    "ts_reg_res": ("在时间窗口内做滚动回归并输出残差。", "FactorSearch"),
    "ts_std": ("计算时间窗口内的滚动标准差。", "DVM Pack + FactorSearch"),
    "ts_sum": ("计算时间窗口内求和，也可用于分钟数据聚合到日频。", "DVM Pack + FactorSearch"),
    "ts_var": ("计算时间窗口内的滚动方差。", "FactorSearch"),
    "ts_win_cumsum": ("在分钟窗口内做累计求和，并可桥接输出到日频。", "FactorSearch"),
    "where": ("根据布尔条件在两个候选值之间逐元素选择。", "DVM Pack + FactorSearch"),
    "xs_corr": ("在横截面上计算两个信号之间的相关性。", "FactorSearch"),
    "xs_mean": ("按日期做横截面均值聚合。", "DVM Pack + FactorSearch"),
    "xs_median": ("按日期做横截面中位数聚合。", "FactorSearch"),
    "xs_prod": ("按日期做横截面乘积聚合。", "FactorSearch"),
    "xs_quantile": ("按日期做横截面分位数聚合。", "FactorSearch"),
    "xs_std": ("按日期做横截面标准差聚合。", "DVM Pack + FactorSearch"),
    "xs_sum": ("按日期做横截面求和聚合。", "FactorSearch"),
}

OPERATORS = tuple(OPERATOR_SPECS.keys())
ALLOWED_NAMES = set(VALUE_FIELDS) | set(CATEGORY_FIELDS) | set(OPERATORS)


class DSLValidationError(ValueError):
    pass


def normalize_space(expr: str) -> str:
    return re.sub(r"\s+", " ", str(expr)).strip()


def _first_frame(*values: Any) -> pd.DataFrame:
    for value in values:
        if isinstance(value, pd.DataFrame):
            return value
    raise TypeError("At least one argument must be a pandas DataFrame.")


def _to_frame(value: Any, reference: pd.DataFrame) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.reindex(index=reference.index, columns=reference.columns)
    return pd.DataFrame(value, index=reference.index, columns=reference.columns)


def _binary_frames(x: Any, y: Any) -> tuple[pd.DataFrame, pd.DataFrame]:
    reference = _first_frame(x, y)
    return _to_frame(x, reference), _to_frame(y, reference)


def _bool_frame(value: Any, reference: pd.DataFrame | None = None) -> pd.DataFrame:
    if reference is None:
        reference = _first_frame(value)
    return _to_frame(value, reference).fillna(False).astype(bool)


def _safe_denom(y: pd.DataFrame, eps: float = EPS) -> pd.DataFrame:
    return y.where(y.abs() > eps)


def _broadcast_series(series: pd.Series, reference: pd.DataFrame) -> pd.DataFrame:
    values = np.repeat(series.to_numpy(dtype=float)[:, None], reference.shape[1], axis=1)
    return pd.DataFrame(values, index=reference.index, columns=reference.columns)


def absolute(x: Any) -> pd.DataFrame:
    return _first_frame(x).abs()


def add(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x + y


def cbrt(x: Any) -> pd.DataFrame:
    return np.cbrt(_first_frame(x))


def diff(x: pd.DataFrame, period: int = 1) -> pd.DataFrame:
    return x.diff(int(period))


def div(x: Any, y: Any, eps: float = EPS) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.divide(_safe_denom(y, eps))


def eq(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.eq(y)


def exp(x: pd.DataFrame) -> pd.DataFrame:
    return np.exp(x.clip(lower=-50, upper=50))


def ge(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.ge(y)


def _group_transform(x: pd.DataFrame, group: Any, kind: str) -> pd.DataFrame:
    if isinstance(group, pd.DataFrame):
        out = pd.DataFrame(index=x.index, columns=x.columns, dtype=float)
        for idx in x.index:
            row = x.loc[idx]
            labels = group.loc[idx]
            if kind == "mean":
                out.loc[idx] = row.groupby(labels).transform("mean")
            elif kind == "std":
                out.loc[idx] = row.groupby(labels).transform(lambda s: s.std(ddof=0))
            else:
                raise ValueError(kind)
        return out

    if isinstance(group, dict):
        group = pd.Series(group)
    if not isinstance(group, pd.Series):
        raise TypeError("group must be a pandas Series, dict, or DataFrame.")

    labels = group.reindex(x.columns)
    if labels.isna().any():
        missing = labels[labels.isna()].index.tolist()
        raise ValueError(f"Missing group labels for columns: {missing[:5]}")
    grouped = x.T.groupby(labels)
    if kind == "mean":
        return grouped.transform("mean").T
    if kind == "std":
        return grouped.transform(lambda s: s.std(ddof=0)).T.replace(0, np.nan)
    raise ValueError(kind)


def group_mean(x: pd.DataFrame, group: Any) -> pd.DataFrame:
    return _group_transform(x, group, "mean")


def group_std(x: pd.DataFrame, group: Any) -> pd.DataFrame:
    return _group_transform(x, group, "std")


def gt(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.gt(y)


def le(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.le(y)


def log(x: pd.DataFrame) -> pd.DataFrame:
    return np.log(x.where(x > 0))


def log10(x: pd.DataFrame) -> pd.DataFrame:
    return np.log10(x.where(x > 0))


def log1p(x: pd.DataFrame) -> pd.DataFrame:
    return np.log1p(x.where(x > -1))


def logical_and(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return _bool_frame(x, x) & _bool_frame(y, x)


def logical_not(x: Any) -> pd.DataFrame:
    reference = _first_frame(x)
    return ~_bool_frame(x, reference)


def logical_or(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return _bool_frame(x, x) | _bool_frame(y, x)


def logical_xor(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return _bool_frame(x, x) ^ _bool_frame(y, x)


def lt(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.lt(y)


def mask(x: Any, cond: Any, fill: Any = np.nan) -> pd.DataFrame:
    reference = _first_frame(x, cond)
    x = _to_frame(x, reference)
    cond = _bool_frame(cond, reference)
    fill = _to_frame(fill, reference)
    return x.where(cond, fill)


def maximum(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return pd.DataFrame(np.maximum(x, y), index=x.index, columns=x.columns)


def minimum(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return pd.DataFrame(np.minimum(x, y), index=x.index, columns=x.columns)


def mod(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.mod(_safe_denom(y))


def mul(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x * y


def ne(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x.ne(y)


def neg(x: pd.DataFrame) -> pd.DataFrame:
    return -x


def pct_change(x: pd.DataFrame, period: int = 1) -> pd.DataFrame:
    lagged = shift(x, int(period))
    return div(sub(x, lagged), lagged)


def pos(x: pd.DataFrame) -> pd.DataFrame:
    return x.where(x > 0, 0.0)


def power(x: pd.DataFrame, exponent: float) -> pd.DataFrame:
    return x.pow(float(exponent))


def recip(x: pd.DataFrame, eps: float = EPS) -> pd.DataFrame:
    return div(1.0, x, eps=eps)


def shift(x: pd.DataFrame, period: int = 1) -> pd.DataFrame:
    return x.shift(int(period))


def sign(x: pd.DataFrame) -> pd.DataFrame:
    return np.sign(x)


def sqrt(x: pd.DataFrame) -> pd.DataFrame:
    return np.sqrt(x.where(x >= 0))


def square(x: pd.DataFrame) -> pd.DataFrame:
    return x.pow(2)


def sub(x: Any, y: Any) -> pd.DataFrame:
    x, y = _binary_frames(x, y)
    return x - y


def _nanarg(func, values: np.ndarray) -> float:
    if np.isnan(values).all():
        return np.nan
    return float(func(values) + 1)


def ts_argmax(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).apply(lambda a: _nanarg(np.nanargmax, a), raw=True)


def ts_argmin(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).apply(lambda a: _nanarg(np.nanargmin, a), raw=True)


def ts_argmaxmin(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return sub(ts_argmax(x, window), ts_argmin(x, window))


def ts_corr(x: pd.DataFrame, y: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).corr(y)


def _last_valid(values: np.ndarray) -> float:
    valid = values[np.isfinite(values)]
    return float(valid[-1]) if valid.size else np.nan


def ts_last(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window), min_periods=1).apply(_last_valid, raw=True)


def ts_max(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).max()


def ts_mean(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).mean()


def ts_min(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).min()


def ts_prod(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).apply(np.prod, raw=True)


def ts_quantile(x: pd.DataFrame, window: int = 10, q: float = 0.5) -> pd.DataFrame:
    return x.rolling(int(window)).quantile(float(q))


def ts_reg_res(y: pd.DataFrame, x: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    window = int(window)
    y, x = _binary_frames(y, x)
    mean_x = x.rolling(window, min_periods=3).mean()
    mean_y = y.rolling(window, min_periods=3).mean()
    var_x = x.rolling(window, min_periods=3).var()
    cov_xy = x.rolling(window, min_periods=3).cov(y)
    beta = cov_xy / var_x.replace(0.0, np.nan)
    alpha = mean_y - beta * mean_x
    return y - (alpha + beta * x)


def ts_std(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).std()


def ts_sum(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).sum()


def ts_var(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return x.rolling(int(window)).var()


def ts_win_cumsum(x: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    return ts_sum(x, window)


def where(cond: Any, x: Any, y: Any) -> pd.DataFrame:
    reference = _first_frame(cond, x, y)
    cond = _bool_frame(cond, reference)
    x = _to_frame(x, reference)
    y = _to_frame(y, reference)
    return x.where(cond, y)


def xs_corr(x: pd.DataFrame, y: pd.DataFrame) -> pd.DataFrame:
    corr = x.corrwith(y, axis=1)
    return _broadcast_series(corr, x)


def xs_mean(x: pd.DataFrame) -> pd.DataFrame:
    return _broadcast_series(x.mean(axis=1), x)


def xs_median(x: pd.DataFrame) -> pd.DataFrame:
    return _broadcast_series(x.median(axis=1), x)


def xs_prod(x: pd.DataFrame) -> pd.DataFrame:
    return _broadcast_series(x.prod(axis=1), x)


def xs_quantile(x: pd.DataFrame, q: float = 0.5) -> pd.DataFrame:
    return _broadcast_series(x.quantile(float(q), axis=1), x)


def xs_std(x: pd.DataFrame) -> pd.DataFrame:
    return _broadcast_series(x.std(axis=1).replace(0, np.nan), x)


def xs_sum(x: pd.DataFrame) -> pd.DataFrame:
    return _broadcast_series(x.sum(axis=1), x)


OPERATOR_ENV = {name: globals()[name] for name in OPERATORS}


class DSLValidator(ast.NodeVisitor):
    def generic_visit(self, node: ast.AST) -> None:
        allowed = (
            ast.Expression,
            ast.Call,
            ast.Name,
            ast.Load,
            ast.Constant,
            ast.UnaryOp,
            ast.UAdd,
            ast.USub,
        )
        if not isinstance(node, allowed):
            raise DSLValidationError(f"Disallowed syntax node: {type(node).__name__}")
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id not in ALLOWED_NAMES:
            raise DSLValidationError(f"Disallowed name: {node.id}")

    def visit_Constant(self, node: ast.Constant) -> None:
        if not isinstance(node.value, (int, float, bool)):
            raise DSLValidationError(f"Disallowed constant: {node.value!r}")

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        if not isinstance(node.op, (ast.UAdd, ast.USub)):
            raise DSLValidationError("Only numeric unary +/- constants are allowed.")
        if not isinstance(node.operand, ast.Constant) or not isinstance(node.operand.value, (int, float)):
            raise DSLValidationError("Unary +/- is only allowed for numeric constants.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if not isinstance(node.func, ast.Name):
            raise DSLValidationError("Only direct function calls are allowed.")
        if node.func.id not in OPERATORS:
            raise DSLValidationError(f"Disallowed function: {node.func.id}")
        if node.keywords:
            raise DSLValidationError("Keyword arguments are not allowed in this DSL subset.")
        self.generic_visit(node)


def validate_dsl(expr: str) -> bool:
    expr = normalize_space(expr)
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise DSLValidationError(f"Syntax error: {exc}") from exc
    DSLValidator().visit(tree)
    return True


def safe_eval_dsl(expr: str, data_env: dict[str, Any]) -> pd.DataFrame:
    validate_dsl(expr)
    tree = ast.parse(normalize_space(expr), mode="eval")
    env = {**OPERATOR_ENV, **data_env}
    result = eval(compile(tree, "<fire-operator-dsl>", "eval"), {"__builtins__": {}}, env)
    if not isinstance(result, pd.DataFrame):
        reference = next(v for v in data_env.values() if isinstance(v, pd.DataFrame))
        result = _to_frame(result, reference)
    return result


def operators_in_expr(expr: str) -> list[str]:
    tree = ast.parse(normalize_space(expr), mode="eval")
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in OPERATORS:
            found.append(node.func.id)
    return found


def names_in_expr(expr: str) -> list[str]:
    tree = ast.parse(normalize_space(expr), mode="eval")
    return sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)})


def make_synthetic_data(seed: int = 7, n_days: int = 180, n_assets: int = 24) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    index = pd.bdate_range("2020-01-01", periods=n_days)
    columns = [f"STK{i:03d}" for i in range(n_assets)]

    stock_scale = rng.lognormal(mean=0.0, sigma=0.25, size=n_assets)
    log_ret = rng.normal(0.0005, 0.02, size=(n_days, n_assets))
    close_arr = 50.0 * stock_scale * np.exp(np.cumsum(log_ret, axis=0))
    close = pd.DataFrame(close_arr, index=index, columns=columns)

    overnight = rng.normal(0.0, 0.008, size=(n_days, n_assets))
    open = close.shift(1).fillna(close.iloc[0]).mul(1.0 + overnight)
    intraday_spread = np.abs(rng.normal(0.012, 0.006, size=(n_days, n_assets)))
    high = pd.DataFrame(
        np.maximum(open.to_numpy(), close.to_numpy()) * (1.0 + intraday_spread),
        index=index,
        columns=columns,
    )
    low = pd.DataFrame(
        np.minimum(open.to_numpy(), close.to_numpy()) * (1.0 - intraday_spread),
        index=index,
        columns=columns,
    ).clip(lower=0.01)
    vwap_noise = rng.normal(0.0, 0.002, size=(n_days, n_assets))
    vwap = add(div(add(add(open, close), add(high, low)), 4.0), mul(close, vwap_noise))
    vwap = maximum(vwap, 0.01)

    volume_base = rng.lognormal(mean=13.5, sigma=0.45, size=(1, n_assets))
    volume_noise = rng.lognormal(mean=0.0, sigma=0.35, size=(n_days, n_assets))
    volume = pd.DataFrame(volume_base * volume_noise, index=index, columns=columns)
    pb = pd.DataFrame(
        rng.lognormal(mean=0.65, sigma=0.35, size=(n_days, n_assets)),
        index=index,
        columns=columns,
    )
    market_cap = pd.DataFrame(
        rng.lognormal(mean=22.5, sigma=0.8, size=(1, n_assets))
        * (close.to_numpy() / close.iloc[0].to_numpy()),
        index=index,
        columns=columns,
    )

    industries = pd.Series(
        [f"industry_{i % 6}" for i in range(n_assets)],
        index=columns,
        name="industry",
    )
    return {
        "open": open,
        "close": close,
        "high": high,
        "low": low,
        "volume": volume,
        "vwap": vwap,
        "pb": pb,
        "market_cap": market_cap,
        "industry": industries,
    }


def result_quality(result: pd.DataFrame, reference: pd.DataFrame) -> dict[str, Any]:
    if not isinstance(result, pd.DataFrame):
        raise TypeError("DSL result is not a DataFrame.")
    if result.shape != reference.shape:
        raise ValueError(f"Unexpected result shape {result.shape}; expected {reference.shape}.")
    numeric = result.astype(float)
    values = numeric.to_numpy()
    finite = np.isfinite(values)
    finite_ratio = float(finite.mean())
    finite_values = values[finite]
    nonconstant = bool(finite_values.size > 1 and np.nanstd(finite_values) > 1e-12)
    return {
        "shape": list(result.shape),
        "finite_ratio": finite_ratio,
        "nonconstant": nonconstant,
        "mean": float(np.nanmean(finite_values)) if finite_values.size else np.nan,
        "std": float(np.nanstd(finite_values)) if finite_values.size else np.nan,
    }


def verify_expression(expr: str, data_env: dict[str, Any], min_finite_ratio: float = 0.25) -> dict[str, Any]:
    reference = next(v for v in data_env.values() if isinstance(v, pd.DataFrame))
    result = safe_eval_dsl(expr, data_env)
    quality = result_quality(result, reference)
    if quality["finite_ratio"] < min_finite_ratio:
        raise ValueError(f"finite_ratio too low: {quality['finite_ratio']:.3f} for {expr}")
    if not quality["nonconstant"]:
        raise ValueError(f"Expression appears constant or all-missing: {expr}")
    return quality
