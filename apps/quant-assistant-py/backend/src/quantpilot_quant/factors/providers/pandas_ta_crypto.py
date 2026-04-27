"""pandas-ta 补充加密因子 provider — CCI / Williams%R / MFI / Stochastic / ROC / DPO."""

from __future__ import annotations

import pandas as pd

from quantpilot_quant.factors.providers.base import BaseFactorProvider


class PandasTaCryptoFactorProvider(BaseFactorProvider):
    """基于 pandas-ta 的补充技术因子集合.

    与 CoreCryptoFactorProvider 相比，新增以下非重叠指标：

    - ``cci_20``:    Commodity Channel Index（偏离均价，超买超卖）
    - ``willr_14``:  Williams %R（超买超卖动量，范围 -100~0）
    - ``mfi_14``:    Money Flow Index（量价加权 RSI，0~100）
    - ``stoch_k``:   Stochastic %K（随机振荡器快线，0~100）
    - ``stoch_d``:   Stochastic %D（随机振荡器慢线，0~100）
    - ``roc_10``:    Rate of Change（10 期价格变化率，动量）
    - ``dpo_20``:    Detrended Price Oscillator（去趋势振荡器，识别短周期）

    输入数据必须包含 ``open_15m``、``high_15m``、``low_15m``、
    ``close_15m``、``volume_15m`` 列（15 分钟为主时间轴）。
    """

    @property
    def name(self) -> str:
        """Provider 名称."""
        return "pandas_ta_crypto"

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        """计算 pandas-ta 补充因子.

        Parameters
        ----------
        frame:
            多周期对齐的研究数据集，需包含 ``*_15m`` OHLCV 列。

        Returns
        -------
        pd.DataFrame
            含 7 列因子：cci_20、willr_14、mfi_14、stoch_k、stoch_d、roc_10、dpo_20。
            前若干行因计算窗口不足，值为 NaN。
        """
        if frame.empty:
            return pd.DataFrame(index=frame.index)

        # pandas-ta 要求列名为 open/high/low/close/volume（不带时间框架后缀）
        ohlcv = pd.DataFrame(
            {
                "open": frame["open_15m"],
                "high": frame["high_15m"],
                "low": frame["low_15m"],
                "close": frame["close_15m"],
                "volume": frame["volume_15m"],
            },
            index=frame.index,
        )

        features = pd.DataFrame(index=frame.index)

        # CCI — 当前价格偏离统计均价的程度，常用 ±100 作为超买超卖阈值
        features["cci_20"] = ohlcv.ta.cci(length=20)

        # Williams %R — 动量振荡器，范围 [-100, 0]，< -80 超卖，> -20 超买
        features["willr_14"] = ohlcv.ta.willr(length=14)

        # MFI — 量价加权 RSI，> 80 超买，< 20 超卖，比 RSI 对成交量更敏感
        features["mfi_14"] = ohlcv.ta.mfi(length=14)

        # Stochastic — 随机振荡器：%K 快线 / %D 慢线（均在 0~100）
        stoch = ohlcv.ta.stoch(k=14, d=3)
        features["stoch_k"] = stoch["STOCHk_14_3_3"]
        features["stoch_d"] = stoch["STOCHd_14_3_3"]

        # ROC — 10 期价格变化率，正值动量向上，负值动量向下
        features["roc_10"] = ohlcv.ta.roc(length=10)

        # DPO — 去趋势振荡器：剔除长期趋势，放大短周期价格波动
        features["dpo_20"] = ohlcv.ta.dpo(length=20)

        return features
