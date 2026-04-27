"""技术指标计算器 — 20 个核心指标（基于 pandas-ta）.

支持指标：
  趋势：MA, EMA, WMA, DEMA, MACD, SAR, ADX, SuperTrend
  震荡：RSI, KDJ, BOLL, CCI, Williams %R, Stochastic
  成交量：OBV, VWAP, CMF
  波动率：ATR, BBands
  其他：ROC
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandas_ta as ta  # type: ignore[import]
from loguru import logger

from quantpilot_common.data.models import OHLCVBar

# 指标注册表：name -> (计算函数参数说明, 默认参数)
INDICATOR_REGISTRY: dict[str, dict[str, Any]] = {
    # ── 趋势指标 ──────────────────────────────────────────────────
    "ma":         {"group": "trend",  "params": {"period": 20}},
    "ema":        {"group": "trend",  "params": {"period": 20}},
    "wma":        {"group": "trend",  "params": {"period": 20}},
    "dema":       {"group": "trend",  "params": {"period": 20}},
    "macd":       {"group": "trend",  "params": {"fast": 12, "slow": 26, "signal": 9}},
    "adx":        {"group": "trend",  "params": {"period": 14}},
    "sar":        {"group": "trend",  "params": {"af0": 0.02, "af": 0.02, "max_af": 0.2}},
    "supertrend": {"group": "trend",  "params": {"period": 7, "multiplier": 3.0}},
    # ── 震荡指标 ──────────────────────────────────────────────────
    "rsi":        {"group": "osc",   "params": {"period": 14}},
    "kdj":        {"group": "osc",   "params": {"k": 9, "d": 3, "j": 3}},
    "cci":        {"group": "osc",   "params": {"period": 20}},
    "willr":      {"group": "osc",   "params": {"period": 14}},
    "stoch":      {"group": "osc",   "params": {"k": 14, "d": 3, "smooth_k": 3}},
    "roc":        {"group": "osc",   "params": {"period": 12}},
    # ── 波动率指标 ────────────────────────────────────────────────
    "bbands":     {"group": "vol",   "params": {"period": 20, "std": 2.0}},
    "atr":        {"group": "vol",   "params": {"period": 14}},
    # ── 成交量指标 ────────────────────────────────────────────────
    "obv":        {"group": "volume", "params": {}},
    "vwap":       {"group": "volume", "params": {}},
    "cmf":        {"group": "volume", "params": {"period": 20}},
    # ── 其他 ──────────────────────────────────────────────────────
    "aroon":      {"group": "trend",  "params": {"period": 25}},
    # ── 新增趋势指标 ──────────────────────────────────────────
    "tema":       {"group": "trend",  "params": {"period": 20}},
    "hma":        {"group": "trend",  "params": {"period": 20}},
    "vwma":       {"group": "trend",  "params": {"period": 20}},
    "zlma":       {"group": "trend",  "params": {"period": 20}},
    "kama":       {"group": "trend",  "params": {"period": 10}},
    # ── 新增震荡指标 ──────────────────────────────────────────
    "stochrsi":   {"group": "osc",   "params": {"period": 14, "rsi_period": 14, "k": 3, "d": 3}},
    "cmo":        {"group": "osc",   "params": {"period": 14}},
    "dpo":        {"group": "osc",   "params": {"period": 20}},
    "uo":         {"group": "osc",   "params": {"fast": 7, "medium": 14, "slow": 28}},
    "trix":       {"group": "osc",   "params": {"period": 18}},
    "ppo":        {"group": "osc",   "params": {"fast": 12, "slow": 26, "signal": 9}},
    "mom":        {"group": "osc",   "params": {"period": 10}},
    # ── 新增波动率指标 ────────────────────────────────────────
    "kc":         {"group": "vol",   "params": {"period": 20, "scalar": 2.0}},
    "donchian":   {"group": "vol",   "params": {"lower_length": 20, "upper_length": 20}},
    "natr":       {"group": "vol",   "params": {"period": 14}},
    "hist_vol":   {"group": "vol",   "params": {"period": 20}},
    # ── 新增成交量指标 ────────────────────────────────────────
    "adosc":      {"group": "volume", "params": {"fast": 3, "slow": 10}},
    "eom":        {"group": "volume", "params": {"period": 14}},
    "mfi":        {"group": "volume", "params": {"period": 14}},
    "pvt":        {"group": "volume", "params": {}},
    "nvi":        {"group": "volume", "params": {}},
}


def bars_to_dataframe(bars: list[OHLCVBar]) -> pd.DataFrame:
    """将 OHLCVBar 列表转换为 pandas DataFrame.

    列名：timestamp, open, high, low, close, volume
    """
    data = [
        {
            "timestamp": b.timestamp,
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
        }
        for b in bars
    ]
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values("timestamp").reset_index(drop=True)
    return df


class IndicatorCalculator:
    """技术指标计算器，基于 pandas-ta 实现 20 个核心指标."""

    def calculate(
        self,
        bars: list[OHLCVBar],
        indicator: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, list[float | None]]:
        """计算单个技术指标.

        Args:
            bars: K 线数据列表
            indicator: 指标名称（小写，见 INDICATOR_REGISTRY）
            params: 指标参数（None 则使用默认值）

        Returns:
            dict，key 为指标字段名，value 为与 bars 等长的数值列表
        """
        if indicator not in INDICATOR_REGISTRY:
            msg = f"不支持的指标: {indicator}，支持列表: {list(INDICATOR_REGISTRY.keys())}"
            raise ValueError(msg)

        default_params = INDICATOR_REGISTRY[indicator]["params"].copy()
        if params:
            default_params.update(params)

        df = bars_to_dataframe(bars)
        if df.empty or len(df) < 2:
            return {}

        try:
            return self._dispatch(df, indicator, default_params)
        except Exception as e:
            logger.error(f"指标 {indicator} 计算失败: {e}")
            raise

    def calculate_batch(
        self,
        bars: list[OHLCVBar],
        indicators: list[str],
    ) -> dict[str, dict[str, list[float | None]]]:
        """批量计算多个指标.

        Returns:
            {indicator_name: {field_name: [values]}}
        """
        results: dict[str, dict[str, list[float | None]]] = {}
        for ind in indicators:
            try:
                results[ind] = self.calculate(bars, ind)
            except Exception as e:
                logger.warning(f"跳过指标 {ind}: {e}")
        return results

    # ── 分发逻辑 ──────────────────────────────────────────────────────────────

    def _dispatch(
        self, df: pd.DataFrame, indicator: str, params: dict[str, Any]
    ) -> dict[str, list[float | None]]:
        handler = getattr(self, f"_calc_{indicator}", None)
        if handler is None:
            msg = f"指标 {indicator} 计算方法未实现"
            raise NotImplementedError(msg)
        return handler(df, **params)

    @staticmethod
    def _to_list(series: pd.Series) -> list[float | None]:
        """将 pandas Series 转为 Python list，NaN 转为 None."""
        return [None if pd.isna(v) else float(v) for v in series]

    # ── 趋势指标 ──────────────────────────────────────────────────────────────

    def _calc_ma(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.sma(df["close"], length=period)
        return {"ma": self._to_list(result)}

    def _calc_ema(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.ema(df["close"], length=period)
        return {"ema": self._to_list(result)}

    def _calc_wma(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.wma(df["close"], length=period)
        return {"wma": self._to_list(result)}

    def _calc_dema(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.dema(df["close"], length=period)
        return {"dema": self._to_list(result)}

    def _calc_macd(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> dict[str, list[float | None]]:
        result = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)
        if result is None or result.empty:
            return {}
        return {
            "macd": self._to_list(result.iloc[:, 0]),
            "macd_signal": self._to_list(result.iloc[:, 2]),
            "macd_hist": self._to_list(result.iloc[:, 1]),
        }

    def _calc_adx(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.adx(df["high"], df["low"], df["close"], length=period)
        if result is None or result.empty:
            return {}
        return {
            "adx": self._to_list(result.iloc[:, 0]),
            "dmp": self._to_list(result.iloc[:, 1]),
            "dmn": self._to_list(result.iloc[:, 2]),
        }

    def _calc_sar(
        self, df: pd.DataFrame, af0: float = 0.02, af: float = 0.02, max_af: float = 0.2
    ) -> dict[str, list[float | None]]:
        result = ta.psar(df["high"], df["low"], df["close"], af0=af0, af=af, max_af=max_af)
        if result is None or result.empty:
            return {}
        # psar 返回多列，取第一列（long/short SAR）
        col = result.columns[0]
        return {"sar": self._to_list(result[col])}

    def _calc_supertrend(
        self, df: pd.DataFrame, period: int = 7, multiplier: float = 3.0
    ) -> dict[str, list[float | None]]:
        result = ta.supertrend(
            df["high"], df["low"], df["close"], length=period, multiplier=multiplier
        )
        if result is None or result.empty:
            return {}
        # supertrend 返回 SUPERT_{period}_{mult} 列
        supert_col = [c for c in result.columns if c.startswith("SUPERT_") and "d" not in c.lower()]
        if not supert_col:
            return {}
        return {"supertrend": self._to_list(result[supert_col[0]])}

    def _calc_aroon(self, df: pd.DataFrame, period: int = 25) -> dict[str, list[float | None]]:
        result = ta.aroon(df["high"], df["low"], length=period)
        if result is None or result.empty:
            return {}
        return {
            "aroon_up": self._to_list(result.iloc[:, 0]),
            "aroon_down": self._to_list(result.iloc[:, 1]),
        }

    # ── 震荡指标 ──────────────────────────────────────────────────────────────

    def _calc_rsi(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.rsi(df["close"], length=period)
        return {"rsi": self._to_list(result)}

    def _calc_kdj(
        self, df: pd.DataFrame, k: int = 9, d: int = 3, j: int = 3
    ) -> dict[str, list[float | None]]:
        result = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d, smooth_k=j)
        if result is None or result.empty:
            return {}
        stoch_k = self._to_list(result.iloc[:, 0])
        stoch_d = self._to_list(result.iloc[:, 1])
        stoch_j = [
            None if (kv is None or dv is None) else 3 * kv - 2 * dv
            for kv, dv in zip(stoch_k, stoch_d, strict=True)
        ]
        return {"k": stoch_k, "d": stoch_d, "j": stoch_j}

    def _calc_cci(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.cci(df["high"], df["low"], df["close"], length=period)
        return {"cci": self._to_list(result)}

    def _calc_willr(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.willr(df["high"], df["low"], df["close"], length=period)
        return {"willr": self._to_list(result)}

    def _calc_stoch(
        self, df: pd.DataFrame, k: int = 14, d: int = 3, smooth_k: int = 3
    ) -> dict[str, list[float | None]]:
        result = ta.stoch(df["high"], df["low"], df["close"], k=k, d=d, smooth_k=smooth_k)
        if result is None or result.empty:
            return {}
        return {
            "stoch_k": self._to_list(result.iloc[:, 0]),
            "stoch_d": self._to_list(result.iloc[:, 1]),
        }

    def _calc_roc(self, df: pd.DataFrame, period: int = 12) -> dict[str, list[float | None]]:
        result = ta.roc(df["close"], length=period)
        return {"roc": self._to_list(result)}

    # ── 波动率指标 ────────────────────────────────────────────────────────────

    def _calc_bbands(
        self, df: pd.DataFrame, period: int = 20, std: float = 2.0
    ) -> dict[str, list[float | None]]:
        result = ta.bbands(df["close"], length=period, std=std)
        if result is None or result.empty:
            return {}
        # pandas-ta bbands 列名：BBL_period_std, BBM_period_std, BBU_period_std, BBB_, BBP_
        cols = result.columns.tolist()
        lower_col = next((c for c in cols if c.startswith("BBL_")), cols[0])
        mid_col   = next((c for c in cols if c.startswith("BBM_")), cols[1])
        upper_col = next((c for c in cols if c.startswith("BBU_")), cols[2])
        return {
            "bb_upper": self._to_list(result[upper_col]),
            "bb_mid":   self._to_list(result[mid_col]),
            "bb_lower": self._to_list(result[lower_col]),
        }

    def _calc_atr(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.atr(df["high"], df["low"], df["close"], length=period)
        return {"atr": self._to_list(result)}

    # ── 成交量指标 ────────────────────────────────────────────────────────────

    def _calc_obv(self, df: pd.DataFrame) -> dict[str, list[float | None]]:
        result = ta.obv(df["close"], df["volume"])
        return {"obv": self._to_list(result)}

    def _calc_vwap(self, df: pd.DataFrame) -> dict[str, list[float | None]]:
        df_indexed = df.set_index(pd.DatetimeIndex(df["timestamp"]))
        result = ta.vwap(df_indexed["high"], df_indexed["low"], df_indexed["close"], df_indexed["volume"])
        return {"vwap": self._to_list(result)}

    def _calc_cmf(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.cmf(df["high"], df["low"], df["close"], df["volume"], length=period)
        return {"cmf": self._to_list(result)}

    # ── 新增趋势指标 ──────────────────────────────────────────────────────────

    def _calc_tema(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.tema(df["close"], length=period)
        return {"tema": self._to_list(result)}

    def _calc_hma(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.hma(df["close"], length=period)
        return {"hma": self._to_list(result)}

    def _calc_vwma(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.vwma(df["close"], df["volume"], length=period)
        return {"vwma": self._to_list(result)}

    def _calc_zlma(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.zlma(df["close"], length=period)
        return {"zlma": self._to_list(result)}

    def _calc_kama(self, df: pd.DataFrame, period: int = 10) -> dict[str, list[float | None]]:
        result = ta.kama(df["close"], length=period)
        return {"kama": self._to_list(result)}

    # ── 新增震荡指标 ──────────────────────────────────────────────────────────

    def _calc_stochrsi(
        self, df: pd.DataFrame, period: int = 14, rsi_period: int = 14, k: int = 3, d: int = 3
    ) -> dict[str, list[float | None]]:
        result = ta.stochrsi(df["close"], length=period, rsi_length=rsi_period, k=k, d=d)
        if result is None or result.empty:
            return {}
        return {
            "stochrsi_k": self._to_list(result.iloc[:, 0]),
            "stochrsi_d": self._to_list(result.iloc[:, 1]),
        }

    def _calc_cmo(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.cmo(df["close"], length=period)
        return {"cmo": self._to_list(result)}

    def _calc_dpo(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        result = ta.dpo(df["close"], length=period)
        return {"dpo": self._to_list(result)}

    def _calc_uo(
        self, df: pd.DataFrame, fast: int = 7, medium: int = 14, slow: int = 28
    ) -> dict[str, list[float | None]]:
        result = ta.uo(df["high"], df["low"], df["close"], fast=fast, medium=medium, slow=slow)
        return {"uo": self._to_list(result)}

    def _calc_trix(self, df: pd.DataFrame, period: int = 18) -> dict[str, list[float | None]]:
        result = ta.trix(df["close"], length=period)
        if result is None:
            return {}
        # trix may return a DataFrame or Series; take first column if DataFrame
        if hasattr(result, "iloc"):
            series = result.iloc[:, 0] if result.ndim == 2 else result
        else:
            series = result
        return {"trix": self._to_list(series)}

    def _calc_ppo(
        self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> dict[str, list[float | None]]:
        result = ta.ppo(df["close"], fast=fast, slow=slow, signal=signal)
        if result is None or result.empty:
            return {}
        return {
            "ppo": self._to_list(result.iloc[:, 0]),
            "ppo_signal": self._to_list(result.iloc[:, 1]),
            "ppo_hist": self._to_list(result.iloc[:, 2]),
        }

    def _calc_mom(self, df: pd.DataFrame, period: int = 10) -> dict[str, list[float | None]]:
        result = ta.mom(df["close"], length=period)
        return {"mom": self._to_list(result)}

    # ── 新增波动率指标 ────────────────────────────────────────────────────────

    def _calc_kc(
        self, df: pd.DataFrame, period: int = 20, scalar: float = 2.0
    ) -> dict[str, list[float | None]]:
        result = ta.kc(df["high"], df["low"], df["close"], length=period, scalar=scalar)
        if result is None or result.empty:
            return {}
        return {
            "kc_upper": self._to_list(result.iloc[:, 0]),
            "kc_mid": self._to_list(result.iloc[:, 1]),
            "kc_lower": self._to_list(result.iloc[:, 2]),
        }

    def _calc_donchian(
        self, df: pd.DataFrame, lower_length: int = 20, upper_length: int = 20
    ) -> dict[str, list[float | None]]:
        result = ta.donchian(df["high"], df["low"], lower_length=lower_length, upper_length=upper_length)
        if result is None or result.empty:
            return {}
        return {
            "dc_upper": self._to_list(result.iloc[:, 0]),
            "dc_mid": self._to_list(result.iloc[:, 1]),
            "dc_lower": self._to_list(result.iloc[:, 2]),
        }

    def _calc_natr(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.natr(df["high"], df["low"], df["close"], length=period)
        return {"natr": self._to_list(result)}

    def _calc_hist_vol(self, df: pd.DataFrame, period: int = 20) -> dict[str, list[float | None]]:
        import numpy as np
        log_ret = np.log(df["close"] / df["close"].shift(1))
        hvol = log_ret.rolling(period).std() * np.sqrt(252) * 100
        return {"hist_vol": self._to_list(hvol)}

    # ── 新增成交量指标 ────────────────────────────────────────────────────────

    def _calc_adosc(
        self, df: pd.DataFrame, fast: int = 3, slow: int = 10
    ) -> dict[str, list[float | None]]:
        result = ta.adosc(df["high"], df["low"], df["close"], df["volume"], fast=fast, slow=slow)
        return {"adosc": self._to_list(result)}

    def _calc_eom(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.eom(df["high"], df["low"], df["close"], df["volume"], length=period)
        return {"eom": self._to_list(result)}

    def _calc_mfi(self, df: pd.DataFrame, period: int = 14) -> dict[str, list[float | None]]:
        result = ta.mfi(df["high"], df["low"], df["close"], df["volume"], length=period)
        return {"mfi": self._to_list(result)}

    def _calc_pvt(self, df: pd.DataFrame) -> dict[str, list[float | None]]:
        result = ta.pvt(df["close"], df["volume"])
        return {"pvt": self._to_list(result)}

    def _calc_nvi(self, df: pd.DataFrame) -> dict[str, list[float | None]]:
        result = ta.nvi(df["close"], df["volume"])
        return {"nvi": self._to_list(result)}
