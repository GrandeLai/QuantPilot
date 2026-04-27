"""滚动分位数阈值过滤器.

插入位置（信号生成流水线）：

  ML 模型 predict_proba
      ↓  confidence ∈ [0, 1]
  *** RollingQuantileFilter.filter() ***     ← 在此处过滤
      ↓  FilterResult.passed == True 时放行
  SignalBroadcaster.publish(signal)
      ↓  action="hold" 时信号被标记但不执行
  SQLite 持久化 + Redis pub/sub

过滤算法
--------
1. 每个 ``(symbol, source)`` 键维护一个独立的 ``deque(maxlen=window)`` 缓冲区，
   存储最近 N 次该来源对该品种的 confidence 历史值；
2. 每次新信号到来时，**先用已有缓冲区**计算第 ``quantile`` 百分位阈值，
   再将本次 confidence 追加到缓冲区（严格防止前视偏差）；
3. 当且仅当 ``confidence > threshold`` 时，信号放行；否则标记为"观望"；
4. 缓冲区样本不足 ``min_periods`` 时进入热身期，直接放行（避免冷启动全过滤）。

典型用法::

    flt = RollingQuantileFilter(window=20, quantile=0.75)

    result = flt.filter(
        symbol="BTC-USDT", source="lgbm_strategy",
        confidence=0.81, action="buy",
    )
    if result.passed:
        await broadcaster.publish(signal)
    # 或者直接在 SignalBroadcaster.publish() 内部调用（推荐，见 broadcaster.py）
"""

from __future__ import annotations

import collections
from dataclasses import dataclass

import numpy as np
from loguru import logger


# ── 过滤结果 ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FilterResult:
    """滚动分位数过滤的单次结果.

    Attributes
    ----------
    passed:
        ``True`` 表示信号通过，应执行交易；``False`` 表示被过滤，标记为观望。
    original_action:
        过滤前的原始动作（``"buy"`` / ``"sell"`` / ``"hold"`` 等）。
    filtered_action:
        过滤后的动作：通过时与 ``original_action`` 相同；被过滤时为 ``"hold"``。
    confidence:
        本次信号的预测概率（输入值，值域 [0, 1]）。
    threshold:
        本次计算的滚动分位数阈值；热身期内为 ``0.0``。
    buffer_size:
        追加本次 confidence **之前**缓冲区的实际样本数。
    reason:
        可读性说明，例如 ``"confidence=0.81 > q75=0.74 [N=18/20]"``。
    """

    passed: bool
    original_action: str
    filtered_action: str
    confidence: float
    threshold: float
    buffer_size: int
    reason: str


# ── 过滤器 ────────────────────────────────────────────────────────────────────


class RollingQuantileFilter:
    """滚动分位数阈值过滤器.

    对每个 ``(symbol, source)`` 键独立维护滚动缓冲区，互不干扰。
    可作为单例注入 ``SignalBroadcaster``，也可在任意上层逻辑中独立调用。

    Parameters
    ----------
    window:
        滚动回看窗口大小（以信号次数计，非时间），默认 20。
        超出的旧值自动淘汰（``deque(maxlen=window)``）。
    quantile:
        分位数阈值，取值 ``(0, 1)``，默认 ``0.75``（75th 百分位）。
        仅当 ``confidence > threshold`` 时信号通过（严格大于）。
        - ``0.5``：信号强度需高于中位数才放行（中等过滤）
        - ``0.75``：信号强度需进入历史前 25%（较严格过滤）
        - ``0.9``：只允许历史最强的 10% 信号通过（极严格过滤）
    min_periods:
        热身期最小样本数。缓冲区样本不足此值时直接放行（避免冷启动全过滤）。
        默认为 ``max(1, window // 4)``（窗口的四分之一）。
    """

    def __init__(
        self,
        window: int = 20,
        quantile: float = 0.75,
        min_periods: int | None = None,
    ) -> None:
        if window < 1:
            raise ValueError(f"window 须 >= 1，实际: {window}")
        if not 0.0 < quantile < 1.0:
            raise ValueError(f"quantile 须在 (0, 1) 之间，实际: {quantile}")
        self.window = window
        self.quantile = quantile
        self.min_periods: int = (
            min_periods if min_periods is not None else max(1, window // 4)
        )
        self._buffers: dict[tuple[str, str], collections.deque[float]] = (
            collections.defaultdict(lambda: collections.deque(maxlen=window))
        )

    # ── 主接口 ────────────────────────────────────────────────────────────────

    def filter(
        self,
        *,
        symbol: str,
        source: str,
        confidence: float,
        action: str,
    ) -> FilterResult:
        """过滤单个信号.

        **计算顺序（严格防止前视）**：先算阈值，再追加 confidence 到缓冲区。

        Parameters
        ----------
        symbol:
            交易对符号，如 ``"BTC-USDT"``。
        source:
            信号来源标识，如 ``"lgbm_strategy"`` / ``"ensemble"``。
            与 ``symbol`` 联合构成缓冲区 key，不同来源互不干扰。
        confidence:
            模型预测概率，值域 [0, 1]。通常为最高类别的 predict_proba。
        action:
            原始交易动作，如 ``"buy"`` / ``"sell"``。
            若已为 ``"hold"``，仍更新缓冲区但直接放行（不叠加过滤）。

        Returns
        -------
        FilterResult
            含过滤决策及可读理由。
        """
        key = (symbol, source)
        buf = self._buffers[key]
        n = len(buf)
        q_label = f"q{int(self.quantile * 100)}"

        # 已经是观望信号 → 更新缓冲区，直接放行
        if action == "hold":
            buf.append(confidence)
            return FilterResult(
                passed=True,
                original_action=action,
                filtered_action=action,
                confidence=confidence,
                threshold=0.0,
                buffer_size=n,
                reason="action 已为 hold，跳过过滤",
            )

        # 热身期 → 直接放行，积累样本
        if n < self.min_periods:
            buf.append(confidence)
            return FilterResult(
                passed=True,
                original_action=action,
                filtered_action=action,
                confidence=confidence,
                threshold=0.0,
                buffer_size=n,
                reason=f"热身期 [{n}/{self.min_periods}]，直接放行",
            )

        # 先计算阈值（不含本次，防止前视）
        threshold = float(np.quantile(list(buf), self.quantile))
        passed = confidence > threshold

        # 再追加本次 confidence
        buf.append(confidence)

        if passed:
            reason = (
                f"confidence={confidence:.4f} > {q_label}={threshold:.4f}"
                f" [N={n}/{self.window}]"
            )
        else:
            reason = (
                f"confidence={confidence:.4f} ≤ {q_label}={threshold:.4f}"
                f" [N={n}/{self.window}]，标记为观望"
            )

        result = FilterResult(
            passed=passed,
            original_action=action,
            filtered_action=action if passed else "hold",
            confidence=confidence,
            threshold=threshold,
            buffer_size=n,
            reason=reason,
        )
        logger.debug(
            "[QuantileFilter] {}/{}: {} → {} | {}",
            symbol, source, action, result.filtered_action, reason,
        )
        return result

    # ── 辅助方法 ──────────────────────────────────────────────────────────────

    def reset(
        self,
        symbol: str | None = None,
        source: str | None = None,
    ) -> None:
        """清空缓冲区（用于测试或重新热身）.

        - 两者均为 ``None``：清空全部缓冲区；
        - 仅指定 ``symbol``：清空该品种所有来源的缓冲区；
        - 两者均指定：只清空该 ``(symbol, source)`` key 的缓冲区。
        """
        if symbol is None and source is None:
            self._buffers.clear()
        elif symbol is not None and source is not None:
            self._buffers.pop((symbol, source), None)
        else:
            keys = [
                k for k in list(self._buffers)
                if (symbol is None or k[0] == symbol)
                and (source is None or k[1] == source)
            ]
            for k in keys:
                del self._buffers[k]

    def buffer_stats(self, symbol: str, source: str) -> dict[str, float | int]:
        """返回缓冲区当前统计信息（用于调试/监控端点）.

        Returns
        -------
        dict
            包含 ``size``, ``mean``, ``std``, ``q{N}``, ``min``, ``max``。
            若缓冲区为空，只返回 ``{"size": 0}``。
        """
        buf = list(self._buffers.get((symbol, source), []))
        if not buf:
            return {"size": 0}
        arr = np.array(buf, dtype=float)
        q_label = f"q{int(self.quantile * 100)}"
        return {
            "size": len(buf),
            "mean": float(arr.mean()),
            "std": float(arr.std()),
            q_label: float(np.quantile(arr, self.quantile)),
            "min": float(arr.min()),
            "max": float(arr.max()),
        }

    def all_buffer_sizes(self) -> dict[str, int]:
        """返回所有活跃缓冲区的大小（供监控使用）."""
        return {f"{sym}/{src}": len(buf) for (sym, src), buf in self._buffers.items()}
