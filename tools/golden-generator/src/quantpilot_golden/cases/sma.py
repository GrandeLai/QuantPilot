"""SMA / EMA golden cases.

实现与 Rust ``apps/quant-assistant/backend/src/indicators.rs``
**逐行对齐**的 Python 算法（不使用 pandas-ta，避免库版本差异）。
用于跨语言 bit-equivalent 验证（容差 < 1e-12）。
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


# ── Pure Python implementations (aligned with Rust) ──────────────────────────


def python_sma(closes: list[float], period: int) -> list[float | None]:
    """与 Rust ``indicators::sma`` 逐行对齐.

    对索引 i：
    - i < period - 1: None
    - i >= period - 1: mean(closes[i-period+1 .. i+1])  （左闭右闭）
    """
    assert period >= 1
    n = len(closes)
    out: list[float | None] = [None] * n
    for i in range(period - 1, n):
        window = closes[i + 1 - period : i + 1]  # same slice as Rust
        s = sum(window)
        out[i] = s / period
    return out


def python_ema(closes: list[float], period: int) -> list[float | None]:
    """与 Rust ``indicators::ema`` 逐行对齐.

    seed = SMA of closes[0..period]；
    k = 2 / (period + 1)；
    ema[i] = closes[i] * k + ema[i-1] * (1 - k)
    """
    assert period >= 1
    n = len(closes)
    out: list[float | None] = [None] * n
    if n < period:
        return out

    # seed = sum(closes[0..period]) / period
    seed = sum(closes[:period]) / period
    out[period - 1] = seed

    k = 2.0 / (period + 1)
    prev = seed
    for i in range(period, n):
        v = closes[i] * k + prev * (1 - k)
        out[i] = v
        prev = v
    return out


# ── Fixed fixture ─────────────────────────────────────────────────────────────

FIXTURE_CLOSES: list[float] = [
    100.0, 101.0, 102.0, 103.0,  99.0,  98.0, 100.0, 105.0, 107.0, 110.0,
    112.0, 108.0, 106.0, 104.0, 102.0, 100.0,  98.0,  99.0, 101.0, 103.0,
    105.0, 107.0, 109.0, 111.0, 113.0,
]


def _none_to_null(v: float | None) -> float | None:
    """Keep None as JSON null; finite floats as-is."""
    return v


def generate_sma_basic() -> dict[str, Any]:
    """生成 sma_basic golden case.

    包含 SMA(3)、SMA(7)、EMA(3)、EMA(7) 四条序列，
    输入为 25 根固定 K 线（与 ma_crossover_basic 同款）。
    """
    closes = FIXTURE_CLOSES
    sma3  = python_sma(closes, 3)
    sma7  = python_sma(closes, 7)
    ema3  = python_ema(closes, 3)
    ema7  = python_ema(closes, 7)

    return {
        "case_id": "sma_basic",
        "description": (
            "SMA/EMA on 25-bar mock series; "
            "cross-language bit-equivalent check (max |Δ| < 1e-12)"
        ),
        "input": {
            "closes": closes,
            "sma_periods": [3, 7],
            "ema_periods": [3, 7],
        },
        "expected": {
            "sma_3": sma3,
            "sma_7": sma7,
            "ema_3": ema3,
            "ema_7": ema7,
        },
        "tolerance": {
            "abs": 1e-12,
            "rel": 0.0,
            "note": "单步指标 bit-equivalent；NaN/null 值必须位置一致",
        },
    }


# ── CLI entry point ───────────────────────────────────────────────────────────


def main() -> None:
    """生成并写出 sma_basic.json."""
    case = generate_sma_basic()
    out_path = (
        Path(__file__).parents[5]  # repo root: QuantPilot/
        / "common"
        / "data-store"
        / "golden"
        / "expected"
        / "sma_basic.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(case, f, indent=2, ensure_ascii=False)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
