"""RollingQuantileFilter 单元测试."""

from __future__ import annotations

import numpy as np
import pytest

from quantpilot_quant.signals.quantile_filter import FilterResult, RollingQuantileFilter


# ── 测试夹具 ───────────────────────────────────────────────────────────────────


def _fill_buffer(
    flt: RollingQuantileFilter,
    values: list[float],
    symbol: str = "BTC",
    source: str = "test",
) -> None:
    """向过滤器缓冲区写入一批历史 confidence 值（action="buy"）."""
    for v in values:
        flt.filter(symbol=symbol, source=source, confidence=v, action="buy")


# ── 热身期 ────────────────────────────────────────────────────────────────────


class TestWarmup:
    def test_always_passes_during_warmup(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=5)
        for i in range(4):  # < min_periods=5
            r = flt.filter(symbol="BTC", source="s", confidence=0.01, action="buy")
            assert r.passed, f"第 {i} 次热身期应放行"
            assert r.threshold == 0.0
            assert r.filtered_action == "buy"

    def test_warmup_reason_contains_label(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        r = flt.filter(symbol="BTC", source="s", confidence=0.5, action="buy")
        assert "warmup" in r.reason.lower() or "热身" in r.reason

    def test_warmup_accumulates_in_buffer(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.5, min_periods=3)
        _fill_buffer(flt, [0.3, 0.5])  # 2 values, still warming up
        stats = flt.buffer_stats("BTC", "test")
        assert stats["size"] == 2


# ── 过滤逻辑 ──────────────────────────────────────────────────────────────────


class TestFilterLogic:
    def test_filters_below_quantile(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        # Buffer: [0.6, 0.7, 0.8, 0.9, 1.0] → q75 ≈ 0.9
        _fill_buffer(flt, [0.6, 0.7, 0.8, 0.9, 1.0])
        r = flt.filter(symbol="BTC", source="test", confidence=0.3, action="buy")
        assert not r.passed
        assert r.filtered_action == "hold"
        assert r.original_action == "buy"

    def test_passes_above_quantile(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        # Buffer: [0.1, 0.2, 0.3] → q75 ≈ 0.25
        _fill_buffer(flt, [0.1, 0.2, 0.3])
        r = flt.filter(symbol="BTC", source="test", confidence=0.9, action="sell")
        assert r.passed
        assert r.filtered_action == "sell"

    def test_boundary_strict_greater_than(self) -> None:
        """confidence == threshold 时应被过滤（严格大于）."""
        flt = RollingQuantileFilter(window=10, quantile=0.5, min_periods=3)
        _fill_buffer(flt, [0.4, 0.5, 0.6])  # q50 = 0.5
        # q50([0.4, 0.5, 0.6]) = 0.5
        r = flt.filter(symbol="BTC", source="test", confidence=0.5, action="buy")
        # 0.5 is NOT > 0.5, should be filtered
        assert not r.passed

    def test_reason_contains_confidence_and_threshold(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        _fill_buffer(flt, [0.3, 0.5, 0.7])
        r = flt.filter(symbol="BTC", source="test", confidence=0.2, action="buy")
        assert "0.2" in r.reason or "0.20" in r.reason
        assert "q75" in r.reason


# ── 前视防止 ──────────────────────────────────────────────────────────────────


class TestNoLookahead:
    def test_threshold_computed_before_append(self) -> None:
        """阈值必须在追加本次 confidence 前计算（防止前视）."""
        flt = RollingQuantileFilter(window=10, quantile=0.5, min_periods=3)
        # 三个值：[0.3, 0.4, 0.5] → q50 = 0.4
        _fill_buffer(flt, [0.3, 0.4, 0.5])
        # 本次 confidence=0.45，如果先追加再算 q50([0.3,0.4,0.45,0.5])=0.425，
        # 但正确做法是先算 q50([0.3,0.4,0.5])=0.4，再追加
        r = flt.filter(symbol="BTC", source="test", confidence=0.45, action="buy")
        assert abs(r.threshold - 0.4) < 1e-9, (
            f"阈值应为 0.4（追加前的 q50），实际 {r.threshold}"
        )
        assert r.passed  # 0.45 > 0.4


# ── hold 动作绕过 ─────────────────────────────────────────────────────────────


class TestHoldBypass:
    def test_hold_action_always_passes(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        # 填充高值使阈值很高
        _fill_buffer(flt, [0.8, 0.9, 0.95, 1.0])
        # action='hold' 即便 confidence 极低也放行
        r = flt.filter(symbol="BTC", source="test", confidence=0.01, action="hold")
        assert r.passed
        assert r.filtered_action == "hold"
        assert r.threshold == 0.0

    def test_hold_still_updates_buffer(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.5, min_periods=1)
        r = flt.filter(symbol="BTC", source="test", confidence=0.7, action="hold")
        stats = flt.buffer_stats("BTC", "test")
        assert stats["size"] == 1  # hold 也更新缓冲区


# ── symbol/source 隔离 ────────────────────────────────────────────────────────


class TestIsolation:
    def test_different_symbol_independent_buffer(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        # BTC 缓冲区有高值
        _fill_buffer(flt, [0.8, 0.9, 0.95], symbol="BTC")
        # ETH 缓冲区为空 → 热身期
        r = flt.filter(symbol="ETH", source="test", confidence=0.01, action="buy")
        assert r.passed
        assert r.threshold == 0.0

    def test_different_source_independent_buffer(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        _fill_buffer(flt, [0.8, 0.9, 0.95], symbol="BTC", source="lgbm")
        r = flt.filter(symbol="BTC", source="ensemble", confidence=0.01, action="buy")
        assert r.passed  # ensemble 缓冲区为空


# ── 重置功能 ──────────────────────────────────────────────────────────────────


class TestReset:
    def test_reset_specific_key(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        _fill_buffer(flt, [0.7, 0.8, 0.9], symbol="BTC")
        flt.reset(symbol="BTC", source="test")
        # 重置后回到热身期
        r = flt.filter(symbol="BTC", source="test", confidence=0.99, action="buy")
        assert r.threshold == 0.0

    def test_reset_by_symbol_only(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=3)
        for src in ["lgbm", "ensemble"]:
            _fill_buffer(flt, [0.7, 0.8, 0.9], symbol="BTC", source=src)
        flt.reset(symbol="BTC")
        sizes = flt.all_buffer_sizes()
        btc_keys = [k for k in sizes if k.startswith("BTC")]
        assert all(sizes[k] == 0 for k in btc_keys) or len(btc_keys) == 0

    def test_reset_all(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=1)
        for sym in ["BTC", "ETH", "SOL"]:
            _fill_buffer(flt, [0.5, 0.6], symbol=sym)
        flt.reset()
        assert flt.all_buffer_sizes() == {}


# ── 缓冲区统计 ────────────────────────────────────────────────────────────────


class TestBufferStats:
    def test_stats_fields(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.75, min_periods=1)
        _fill_buffer(flt, [0.2, 0.4, 0.6, 0.8])
        stats = flt.buffer_stats("BTC", "test")
        assert stats["size"] == 4
        assert abs(stats["mean"] - 0.5) < 1e-9
        assert "q75" in stats
        assert "min" in stats
        assert "max" in stats

    def test_empty_buffer_stats(self) -> None:
        flt = RollingQuantileFilter()
        stats = flt.buffer_stats("UNKNOWN", "none")
        assert stats == {"size": 0}

    def test_buffer_wraps_at_maxlen(self) -> None:
        flt = RollingQuantileFilter(window=3, quantile=0.5, min_periods=1)
        _fill_buffer(flt, [0.1, 0.2, 0.3, 0.4, 0.5])  # 5 值，maxlen=3
        stats = flt.buffer_stats("BTC", "test")
        assert stats["size"] == 3
        assert abs(stats["mean"] - 0.4) < 1e-9  # 最后 3 个：0.3, 0.4, 0.5


# ── 参数合法性 ────────────────────────────────────────────────────────────────


class TestParamValidation:
    def test_invalid_window(self) -> None:
        with pytest.raises(ValueError):
            RollingQuantileFilter(window=0)

    def test_invalid_quantile_zero(self) -> None:
        with pytest.raises(ValueError):
            RollingQuantileFilter(quantile=0.0)

    def test_invalid_quantile_one(self) -> None:
        with pytest.raises(ValueError):
            RollingQuantileFilter(quantile=1.0)

    def test_min_periods_default(self) -> None:
        flt = RollingQuantileFilter(window=20)
        assert flt.min_periods == 5  # max(1, 20 // 4)

    def test_min_periods_custom(self) -> None:
        flt = RollingQuantileFilter(window=20, min_periods=10)
        assert flt.min_periods == 10


# ── FilterResult 完整性 ────────────────────────────────────────────────────────


class TestFilterResult:
    def test_result_fields_on_pass(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.5, min_periods=3)
        _fill_buffer(flt, [0.2, 0.3, 0.4])
        r = flt.filter(symbol="BTC", source="test", confidence=0.9, action="buy")
        assert isinstance(r, FilterResult)
        assert r.passed is True
        assert r.original_action == "buy"
        assert r.filtered_action == "buy"
        assert r.confidence == 0.9
        assert r.threshold > 0.0
        assert r.buffer_size == 3

    def test_result_fields_on_filter(self) -> None:
        flt = RollingQuantileFilter(window=10, quantile=0.5, min_periods=3)
        _fill_buffer(flt, [0.8, 0.9, 1.0])
        r = flt.filter(symbol="BTC", source="test", confidence=0.1, action="sell")
        assert r.passed is False
        assert r.original_action == "sell"
        assert r.filtered_action == "hold"
        assert r.confidence == 0.1
        assert r.threshold > 0.1
