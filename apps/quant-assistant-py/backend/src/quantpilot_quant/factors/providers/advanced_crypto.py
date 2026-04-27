"""高级加密因子 provider — VWAP 乖离率 / 偏度 / 峰度 / 极值插针 / 跨周期共振."""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantpilot_quant.factors.providers.base import BaseFactorProvider

# 跨周期共振支持的时间框架（从快到慢），compute 时按此顺序检测可用列
_MTF_TIMEFRAMES: tuple[str, ...] = ("1m", "5m", "15m", "1h", "4h", "1d")


class AdvancedCryptoFactorProvider(BaseFactorProvider):
    """高级加密因子集合，基于 15m 为主时间轴的多周期对齐数据集。

    包含以下因子（均通过独立私有方法实现，互不依赖）：

    1. VWAP 乖离率（vwap_dev_{window}）
       衡量当前价格与滚动 VWAP 的百分比偏离。

    2. 收益率偏度（skewness_{window}）
       滚动窗口内对数收益率的 skewness，捕捉分布不对称性。

    3. 收益率峰度（kurtosis_{window}）
       滚动窗口内对数收益率的超额峰度（excess kurtosis），捕捉肥尾程度。

    4. 极值插针（upper_shadow_ratio / lower_shadow_ratio / pin_score）
       通过上下影线与实体的比率捕捉插针行为（锤子线 / 射击之星）。

    5. 跨周期共振（mtf_resonance）
       多时间框架动量方向一致性得分，范围 [-1, 1]。
    """

    @property
    def name(self) -> str:
        return "advanced_crypto"

    def compute(self, frame: pd.DataFrame) -> pd.DataFrame:
        """计算所有高级因子。

        Parameters
        ----------
        frame:
            多周期对齐的研究数据集（由 ``MultiTimeframeDatasetBuilder.build()`` 生成）。
            列命名规范：``{ohlcv}_{timeframe}``，如 ``close_15m``、``high_1h``。
            必须包含 ``open_15m``、``high_15m``、``low_15m``、``close_15m``、``volume_15m``。

        Returns
        -------
        pd.DataFrame
            与 ``frame`` 行索引完全对齐的因子 DataFrame，含以下列：

            - ``vwap_dev_20``、``vwap_dev_60``
            - ``skewness_20``、``skewness_60``
            - ``kurtosis_20``、``kurtosis_60``
            - ``upper_shadow_ratio``、``lower_shadow_ratio``、``pin_score``
            - ``mtf_resonance``
        """
        if frame.empty:
            return pd.DataFrame(index=frame.index)

        close = frame["close_15m"]
        high = frame["high_15m"]
        low = frame["low_15m"]
        open_ = frame["open_15m"]
        volume = frame["volume_15m"]

        features = pd.DataFrame(index=frame.index)

        # 对数收益率（因子 2、3 共用）
        log_returns = np.log(close / close.shift(1))

        for window in (20, 60):
            # 因子 1：VWAP 乖离率
            features[f"vwap_dev_{window}"] = self._vwap_deviation(
                high=high, low=low, close=close, volume=volume, window=window
            )
            # 因子 2：收益率偏度
            features[f"skewness_{window}"] = self._rolling_skewness(log_returns, window=window)
            # 因子 3：收益率峰度
            features[f"kurtosis_{window}"] = self._rolling_kurtosis(log_returns, window=window)

        # 因子 4：极值插针（返回 3 列 DataFrame，直接 concat 合并）
        pin_df = self._pin_bar(open_=open_, high=high, low=low, close=close)
        features = pd.concat([features, pin_df], axis=1)

        # 因子 5：跨周期共振
        features["mtf_resonance"] = self._mtf_resonance(frame)

        return features

    # ── 因子 1：VWAP 乖离率 ───────────────────────────────────────────────────

    def _vwap_deviation(
        self,
        *,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        volume: pd.Series,
        window: int,
    ) -> pd.Series:
        """VWAP 乖离率：当前收盘价与滚动 VWAP 的百分比偏离。

        滚动 VWAP 定义（典型价格加权）：
            typical_price = (high + low + close) / 3
            vwap_N = Σ(typical_price × volume, N 期) / Σ(volume, N 期)

        乖离率：
            vwap_dev = (close - vwap_N) / vwap_N × 100

        正值表示价格高于 VWAP（相对强势 / 超买偏离），
        负值表示价格低于 VWAP（相对弱势 / 超卖偏离）。

        注意：此处采用"滚动 VWAP"而非传统会话内 VWAP，
        因此更适合跨会话、跨日的中低频因子研究场景。

        Parameters
        ----------
        high, low, close, volume:
            同一时间框架的 OHLCV 列。
        window:
            滚动窗口大小（根 K 线数量）。

        Returns
        -------
        pd.Series
            VWAP 乖离率（单位 %），与输入行索引对齐；
            前 ``window - 1`` 行因数据不足返回 NaN。
        """
        typical_price = (high + low + close) / 3
        tp_vol_sum = (typical_price * volume).rolling(window, min_periods=window).sum()
        vol_sum = volume.rolling(window, min_periods=window).sum()
        vwap = tp_vol_sum / vol_sum.replace(0, np.nan)
        return (close - vwap) / vwap * 100

    # ── 因子 2：收益率偏度 ────────────────────────────────────────────────────

    def _rolling_skewness(self, log_returns: pd.Series, *, window: int) -> pd.Series:
        """滚动窗口收益率偏度（Fisher-Pearson skewness）。

        衡量 N 期对数收益率分布的不对称性：
            正偏度（> 0）：右尾较长，偶发大涨概率高于大跌；
            负偏度（< 0）：左尾较长，偶发大跌风险更高；
            接近 0：近似对称分布。

        偏度可用于捕捉市场情绪异常、流动性冲击预警等信号，
        在衍生品定价偏差及尾部风险管理中应用广泛。

        Parameters
        ----------
        log_returns:
            对数收益率序列：log(close_t / close_{t-1})。
        window:
            滚动窗口大小。

        Returns
        -------
        pd.Series
            滚动偏度，与输入行索引对齐；
            前 ``window - 1`` 行返回 NaN。
        """
        return log_returns.rolling(window, min_periods=window).skew()

    # ── 因子 3：收益率峰度 ────────────────────────────────────────────────────

    def _rolling_kurtosis(self, log_returns: pd.Series, *, window: int) -> pd.Series:
        """滚动窗口收益率超额峰度（excess kurtosis，Fischer 定义）。

        衡量 N 期对数收益率分布的尾部厚重程度，以正态分布为基准（=0）：
            超额峰度 > 0（尖峰肥尾）：极端收益率出现频率高于正态分布，
                                      常见于流动性危机、重大新闻冲击等情景；
            超额峰度 < 0（低峰瘦尾）：收益率集中，极端事件概率低。

        在加密市场中，高峰度周期往往伴随高波动率聚集，
        可作为波动率预测及风险预警的辅助信号。

        Parameters
        ----------
        log_returns:
            对数收益率序列：log(close_t / close_{t-1})。
        window:
            滚动窗口大小。

        Returns
        -------
        pd.Series
            滚动超额峰度（正态分布基准为 0），与输入行索引对齐；
            前 ``window - 1`` 行返回 NaN。
        """
        return log_returns.rolling(window, min_periods=window).kurt()

    # ── 因子 4：极值插针 ──────────────────────────────────────────────────────

    def _pin_bar(
        self,
        *,
        open_: pd.Series,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
    ) -> pd.DataFrame:
        """极值插针因子：通过上下影线与实体比率捕捉插针行为。

        K 线结构拆解：
            body        = |close - open|          （实体长度）
            upper_wick  = high - max(open, close) （上影线）
            lower_wick  = min(open, close) - low  （下影线）

        派生因子：
            upper_shadow_ratio = upper_wick / (body + ε)
                上影线相对实体的倍数，值越大代表上方卖压越强
                （射击之星、乌云盖顶形态的核心特征）。

            lower_shadow_ratio = lower_wick / (body + ε)
                下影线相对实体的倍数，值越大代表下方买盘越强
                （锤子线、倒锤子线形态的核心特征）。

            pin_score = (lower_wick - upper_wick) / (high - low + ε) ∈ [-1, 1]
                综合方向性的插针强度得分：
                    接近 +1：强下影线（锤子线型，潜在看涨反转）；
                    接近 -1：强上影线（射击之星型，潜在看跌反转）；
                    接近  0：实体主导或上下影线均衡。

        Parameters
        ----------
        open_:
            开盘价序列（使用 ``open_`` 命名以避免遮蔽 Python 内置函数 ``open``）。
        high, low, close:
            同一 K 线的最高、最低、收盘价序列。

        Returns
        -------
        pd.DataFrame
            含 3 列：``upper_shadow_ratio``、``lower_shadow_ratio``、``pin_score``，
            与输入行索引对齐；单行计算，无前置 NaN。
        """
        _eps = 1e-8
        body = (close - open_).abs()

        candle_top = pd.concat([open_, close], axis=1).max(axis=1)
        candle_bottom = pd.concat([open_, close], axis=1).min(axis=1)
        upper_wick = (high - candle_top).clip(lower=0.0)
        lower_wick = (candle_bottom - low).clip(lower=0.0)
        candle_range = (high - low).replace(0, np.nan)

        return pd.DataFrame(
            {
                "upper_shadow_ratio": upper_wick / (body + _eps),
                "lower_shadow_ratio": lower_wick / (body + _eps),
                "pin_score": (lower_wick - upper_wick) / (candle_range + _eps),
            },
            index=open_.index,
        )

    # ── 因子 5：跨周期共振 ────────────────────────────────────────────────────

    def _mtf_resonance(self, frame: pd.DataFrame, *, lookback: int = 1) -> pd.Series:
        """跨周期动量共振因子：多时间框架动量方向一致性得分。

        算法：
            1. 遍历 ``_MTF_TIMEFRAMES`` （1m / 5m / 15m / 1h / 4h / 1d），
               提取 frame 中实际存在的 ``close_{tf}`` 列；
            2. 对每个周期计算 ``lookback`` 期动量方向：
               direction_{tf} = sign(close_{tf,t} - close_{tf,t-lookback})
               ∈ {-1, 0, +1}；
            3. 对所有可用周期的方向取均值：
               mtf_resonance = mean(direction_{tf}) ∈ [-1, 1]。

        解读：
            +1.0  所有可用周期均向上（强看涨共振，趋势方向高度一致）；
            -1.0  所有可用周期均向下（强看跌共振）；
             0.0  各周期方向完全分歧，信号无效；
            (0, 1) 多数周期向上，但存在分歧（弱共振）。

        注意事项：
            - 数据集至少需包含 2 个可识别的 ``close_{tf}`` 列，否则返回全 NaN 序列。
            - 对于多周期对齐的数据集，高周期列（如 ``close_1h``）采用
              ``merge_asof`` 前向填充，shift 操作在填充数据上进行。
              因此 ``lookback=1`` 对 ``close_1h`` 意味着"当前 15m Bar 所属 1h Bar
              与上一个 1h Bar 的方向"，语义合理。

        Parameters
        ----------
        frame:
            多周期对齐 DataFrame，需含至少 2 个 ``close_{tf}`` 列。
        lookback:
            动量回溯周期数，默认 1（相邻两个 Bar 的方向）。

        Returns
        -------
        pd.Series
            跨周期共振得分，范围 [-1, 1]，与 ``frame`` 行索引对齐。
            若可用周期不足 2 个则返回全 NaN 序列。
        """
        directions: list[pd.Series] = []
        for tf in _MTF_TIMEFRAMES:
            col = f"close_{tf}"
            if col in frame.columns:
                close_tf = frame[col]
                # 计算 lookback 期价格变化方向；首行 shift 产生的 NaN 视为无信号（置 0）
                direction = np.sign(close_tf - close_tf.shift(lookback)).fillna(0.0)
                directions.append(direction)

        if len(directions) < 2:
            return pd.Series(np.nan, index=frame.index, name="mtf_resonance")

        return pd.concat(directions, axis=1).mean(axis=1).rename("mtf_resonance")
