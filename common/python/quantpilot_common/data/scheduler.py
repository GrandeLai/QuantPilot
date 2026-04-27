"""APScheduler 定时数据更新调度器.

负责自动拉取最新 K 线数据、更新数据库。
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from quantpilot_common.data.fetchers.yfinance_fetcher import YFinanceFetcher

if TYPE_CHECKING:
    from quantpilot_common.data.storage import MarketDataStorage


class DataScheduler:
    """数据定时更新调度器.

    根据配置的标的列表，定时从数据源拉取最新 K 线并写入 DuckDB。
    """

    def __init__(self, storage: MarketDataStorage) -> None:
        self._storage = storage
        self._yf = YFinanceFetcher()
        self._scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self._watch_list: list[dict[str, str]] = []  # [{symbol, timeframe, source}]

    def add_symbol(
        self, symbol: str, timeframe: str = "1d", source: str = "yfinance"
    ) -> None:
        """添加标的到定时更新列表."""
        entry = {"symbol": symbol, "timeframe": timeframe, "source": source}
        if entry not in self._watch_list:
            self._watch_list.append(entry)
            logger.info(f"[Scheduler] 添加监控标的: {symbol} {timeframe} ({source})")

    def remove_symbol(self, symbol: str, timeframe: str = "1d") -> None:
        """从定时更新列表移除标的."""
        self._watch_list = [
            e for e in self._watch_list
            if not (e["symbol"] == symbol and e["timeframe"] == timeframe)
        ]

    def _update_symbol(self, symbol: str, timeframe: str, source: str) -> None:
        """执行单个标的的数据更新."""
        import asyncio
        try:
            # 查找最新数据时间
            _, latest = self._storage.get_date_range(symbol, timeframe)
            start = (latest.date() if latest else date.today() - timedelta(days=365))

            if source == "yfinance":
                bars = self._yf.fetch_ohlcv(symbol, timeframe, start=start)
            else:
                logger.warning(f"[Scheduler] 未知数据源: {source}")
                return

            if bars:
                written = self._storage.upsert_bars(bars)
                logger.info(f"[Scheduler] {symbol} {timeframe} 更新 {written} 条")

                # 更新 Redis 价格缓存（最新收盘价）
                latest_bar = bars[-1]
                try:
                    from quantpilot_common.redis.client import RedisClient
                    from quantpilot_common.redis.price_cache import PriceCache
                    if RedisClient._instance is not None:
                        loop = asyncio.new_event_loop()
                        loop.run_until_complete(PriceCache().set_price(symbol, latest_bar.close))
                        loop.close()
                except Exception as e:
                    logger.debug(f"[Scheduler] 价格缓存更新跳过: {e}")

                # 发布到 Redis pub/sub（行情实时推送）
                try:
                    from quantpilot_common.redis.client import RedisClient
                    from quantpilot_common.redis.pubsub import BarPublisher
                    if RedisClient._instance is not None:
                        publisher = BarPublisher()
                        loop = asyncio.new_event_loop()
                        for bar in bars[-5:]:  # 只推最新几根，避免大量历史数据 flooding
                            loop.run_until_complete(publisher.publish(bar))
                        loop.close()
                except Exception as e:
                    logger.debug(f"[Scheduler] bar 发布跳过: {e}")
        except Exception as e:
            logger.error(f"[Scheduler] {symbol} 更新失败: {e}")

    def _run_all_updates(self) -> None:
        """执行所有监控标的的数据更新."""
        logger.info(f"[Scheduler] 开始定时更新，共 {len(self._watch_list)} 个标的")
        for entry in self._watch_list:
            self._update_symbol(entry["symbol"], entry["timeframe"], entry["source"])
        logger.info("[Scheduler] 本轮更新完成")

    def start(self) -> None:
        """启动定时调度.

        计划：
        - 工作日 09:35 更新 A 股数据（收盘后）
        - 每天 06:00 更新美股/加密货币数据（UTC+8）
        """
        # 日线数据：工作日 21:00 更新（覆盖 A 股收盘后 + 美股盘前）
        self._scheduler.add_job(
            self._run_all_updates,
            trigger=CronTrigger(hour=21, minute=0, day_of_week="mon-fri"),
            id="daily_update",
            replace_existing=True,
            name="日线数据定时更新",
        )

        self._scheduler.start()
        logger.info("[Scheduler] 定时调度器已启动")

    def stop(self) -> None:
        """停止定时调度."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("[Scheduler] 定时调度器已停止")

    def trigger_update(self, symbol: str | None = None, timeframe: str = "1d") -> None:
        """手动触发一次更新（用于 API 调用）."""
        if symbol:
            entry = next(
                (e for e in self._watch_list if e["symbol"] == symbol), None
            )
            source = entry["source"] if entry else "yfinance"
            self._update_symbol(symbol, timeframe, source)
        else:
            self._run_all_updates()
