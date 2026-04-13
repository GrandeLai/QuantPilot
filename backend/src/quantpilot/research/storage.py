"""加密研究结果缓存存储（SQLite）."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from quantpilot.config import get_settings
from quantpilot.research.models import CryptoResearchTrainSummary


def _default_db_path() -> Path:
    """Return the default on-disk cache path for crypto research results."""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir / "crypto_research.sqlite"


class CryptoResearchStorage:
    """保存和读取最新研究结果摘要."""

    def __init__(self, db_path: Path | None = None) -> None:
        self._path = db_path or _default_db_path()
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS crypto_research_results (
                    symbol TEXT NOT NULL,
                    base_timeframe TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (symbol, base_timeframe)
                )
                """
            )
            self._conn.commit()

    def save_latest(self, summary: CryptoResearchTrainSummary) -> None:
        """保存最新研究结果摘要."""
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO crypto_research_results (symbol, base_timeframe, payload)
                VALUES (?, ?, ?)
                """,
                (summary.symbol, summary.base_timeframe, summary.model_dump_json()),
            )
            self._conn.commit()

    def load_latest(self, *, symbol: str, base_timeframe: str) -> CryptoResearchTrainSummary | None:
        """读取指定标的与基础周期的最新研究结果."""
        with self._lock:
            row = self._conn.execute(
                """
                SELECT payload
                FROM crypto_research_results
                WHERE symbol = ? AND base_timeframe = ?
                """,
                (symbol, base_timeframe),
            ).fetchone()
        if row is None:
            return None
        return CryptoResearchTrainSummary.model_validate_json(row[0])
