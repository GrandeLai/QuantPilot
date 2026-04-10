"""技术指标计算测试 — T-1.2 验收（20 个核心指标）."""

from datetime import UTC, datetime, timedelta

import pytest

from quantpilot.data.models import OHLCVBar
from quantpilot.indicators.calculator import INDICATOR_REGISTRY, IndicatorCalculator


def _make_bars(n: int = 100) -> list[OHLCVBar]:
    """生成 n 根模拟 K 线（简单趋势+震荡）."""
    import math

    bars = []
    base_price = 100.0
    for i in range(n):
        price = base_price + i * 0.5 + math.sin(i * 0.3) * 5
        bars.append(
            OHLCVBar(
                symbol="TEST",
                timeframe="1d",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC) + timedelta(days=i),
                open=price,
                high=price * 1.02,
                low=price * 0.98,
                close=price + 0.1,
                volume=1_000_000.0 + i * 1000,
            )
        )
    return bars


@pytest.fixture
def bars() -> list[OHLCVBar]:
    return _make_bars(100)


@pytest.fixture
def calc() -> IndicatorCalculator:
    return IndicatorCalculator()


class TestIndicatorRegistry:
    def test_has_20_indicators(self) -> None:
        assert len(INDICATOR_REGISTRY) >= 20, f"指标数量不足: {len(INDICATOR_REGISTRY)}"

    def test_all_have_group(self) -> None:
        for name, info in INDICATOR_REGISTRY.items():
            assert "group" in info, f"指标 {name} 缺少 group"
            assert info["group"] in ("trend", "osc", "vol", "volume")

    def test_all_have_params(self) -> None:
        for name, info in INDICATOR_REGISTRY.items():
            assert "params" in info, f"指标 {name} 缺少 params"


class TestTrendIndicators:
    def test_ma(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "ma", {"period": 20})
        assert "ma" in result
        assert len(result["ma"]) == len(bars)
        # 前 19 个为 None（需要 20 期数据）
        assert result["ma"][0] is None
        assert result["ma"][19] is not None

    def test_ema(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "ema", {"period": 20})
        assert "ema" in result
        assert len(result["ema"]) == len(bars)
        assert result["ema"][-1] is not None

    def test_wma(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "wma", {"period": 10})
        assert "wma" in result
        assert result["wma"][-1] is not None

    def test_dema(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "dema", {"period": 10})
        assert "dema" in result

    def test_macd(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "macd")
        assert "macd" in result
        assert "macd_signal" in result
        assert "macd_hist" in result
        assert len(result["macd"]) == len(bars)

    def test_adx(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "adx")
        assert "adx" in result
        # ADX 值在 0-100 之间
        valid = [v for v in result["adx"] if v is not None]
        assert all(0 <= v <= 100 for v in valid)

    def test_sar(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "sar")
        assert "sar" in result

    def test_aroon(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "aroon")
        assert "aroon_up" in result
        assert "aroon_down" in result


class TestOscillatorIndicators:
    def test_rsi(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "rsi", {"period": 14})
        assert "rsi" in result
        assert len(result["rsi"]) == len(bars)
        valid = [v for v in result["rsi"] if v is not None]
        assert all(0 <= v <= 100 for v in valid)

    def test_kdj(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "kdj")
        assert "k" in result
        assert "d" in result
        assert "j" in result

    def test_cci(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "cci")
        assert "cci" in result

    def test_willr(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "willr")
        assert "willr" in result
        valid = [v for v in result["willr"] if v is not None]
        assert all(-100 <= v <= 0 for v in valid)

    def test_stoch(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "stoch")
        assert "stoch_k" in result
        assert "stoch_d" in result

    def test_roc(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "roc")
        assert "roc" in result


class TestVolatilityIndicators:
    def test_bbands(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "bbands")
        assert "bb_upper" in result
        assert "bb_mid" in result
        assert "bb_lower" in result
        # 上轨 >= 中轨 >= 下轨
        for up, mid, low in zip(result["bb_upper"], result["bb_mid"], result["bb_lower"], strict=True):
            if up is not None and mid is not None and low is not None:
                assert up >= mid >= low

    def test_atr(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "atr")
        assert "atr" in result
        valid = [v for v in result["atr"] if v is not None]
        assert all(v > 0 for v in valid)


class TestVolumeIndicators:
    def test_obv(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "obv")
        assert "obv" in result
        assert len(result["obv"]) == len(bars)

    def test_vwap(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "vwap")
        assert "vwap" in result

    def test_cmf(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "cmf")
        assert "cmf" in result


class TestBatchCalculation:
    def test_batch_returns_all(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        inds = ["ma", "ema", "rsi", "macd", "bbands"]
        result = calc.calculate_batch(bars, inds)
        for ind in inds:
            assert ind in result

    def test_invalid_indicator_skipped(
        self, bars: list[OHLCVBar], calc: IndicatorCalculator
    ) -> None:
        result = calc.calculate_batch(bars, ["ma", "INVALID"])
        assert "ma" in result
        assert "INVALID" not in result


class TestEdgeCases:
    def test_unknown_indicator_raises(
        self, bars: list[OHLCVBar], calc: IndicatorCalculator
    ) -> None:
        with pytest.raises(ValueError, match="不支持的指标"):
            calc.calculate(bars, "unknown_indicator")

    def test_empty_bars_returns_empty(self, calc: IndicatorCalculator) -> None:
        result = calc.calculate([], "ma")
        assert result == {}


class TestNewIndicators:
    def test_tema(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "tema")
        assert "tema" in result
        assert len(result["tema"]) == len(bars)

    def test_hma(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "hma")
        assert "hma" in result

    def test_stochrsi(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "stochrsi")
        assert "stochrsi_k" in result
        assert "stochrsi_d" in result

    def test_cmo(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "cmo")
        assert "cmo" in result

    def test_kc(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "kc")
        assert "kc_upper" in result and "kc_lower" in result

    def test_donchian(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "donchian")
        assert "dc_upper" in result and "dc_lower" in result

    def test_mfi(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "mfi")
        assert "mfi" in result

    def test_hist_vol(self, bars: list[OHLCVBar], calc: IndicatorCalculator) -> None:
        result = calc.calculate(bars, "hist_vol")
        assert "hist_vol" in result

    def test_registry_has_40_plus(self) -> None:
        from quantpilot.indicators.calculator import INDICATOR_REGISTRY
        assert len(INDICATOR_REGISTRY) >= 40
