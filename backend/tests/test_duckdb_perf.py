"""DuckDB 性能验证 — T-0.2 验收测试.

验收标准：千万级 K 线数据，聚合查询耗时 < 500ms（目标 < 100ms）
"""

import time

import duckdb
import pytest


@pytest.fixture
def duckdb_with_10m_bars(tmp_path: pytest.TempPathFactory) -> duckdb.DuckDBPyConnection:
    """创建包含 1000 万条 K 线数据的 DuckDB 连接."""
    db_path = str(tmp_path / "bench.duckdb")
    conn = duckdb.connect(db_path)

    print("\n正在生成 1000 万条 K 线数据...")
    t_start = time.perf_counter()

    conn.execute("""
        CREATE TABLE market_data AS
        SELECT
            TIMESTAMP '2020-01-01' + INTERVAL (i) MINUTE AS timestamp,
            CASE (i % 3)
                WHEN 0 THEN 'BTC/USDT'
                WHEN 1 THEN 'ETH/USDT'
                ELSE 'BNB/USDT'
            END AS symbol,
            10000.0 + (random() - 0.5) * 1000 AS open,
            10000.0 + random() * 1000        AS high,
            10000.0 - random() * 1000        AS low,
            10000.0 + (random() - 0.5) * 1000 AS close,
            random() * 1000000               AS volume
        FROM range(10000000) t(i)
    """)

    t_insert = (time.perf_counter() - t_start) * 1000
    row_count = conn.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]  # type: ignore[index]
    print(f"✓ 写入 {row_count:,} 条记录，耗时 {t_insert:.0f}ms")

    yield conn
    conn.close()


def test_10m_bars_count(duckdb_with_10m_bars: duckdb.DuckDBPyConnection) -> None:
    """验证数据量：1000 万条 K 线."""
    count = duckdb_with_10m_bars.execute("SELECT COUNT(*) FROM market_data").fetchone()[0]  # type: ignore[index]
    assert count == 10_000_000, f"期望 10,000,000 条，实际 {count:,} 条"


def test_single_symbol_range_query(duckdb_with_10m_bars: duckdb.DuckDBPyConnection) -> None:
    """验证单标的时间范围查询性能（全表扫描）."""
    conn = duckdb_with_10m_bars

    t_start = time.perf_counter()
    result = conn.execute("""
        SELECT COUNT(*), MIN(close), MAX(close), AVG(close)
        FROM market_data
        WHERE symbol = 'BTC/USDT'
    """).fetchone()
    elapsed_ms = (time.perf_counter() - t_start) * 1000

    print(f"\n单标的全表聚合查询耗时: {elapsed_ms:.2f}ms")
    print(f"  结果: count={result[0]:,}, min={result[1]:.2f}, max={result[2]:.2f}, avg={result[3]:.2f}")  # type: ignore[index]

    assert result[0] > 0, "查询结果为空"
    # 目标 < 100ms，验收门槛宽松到 500ms
    assert elapsed_ms < 500, f"查询耗时 {elapsed_ms:.2f}ms，超过 500ms 阈值"


def test_ohlcv_daily_aggregation(duckdb_with_10m_bars: duckdb.DuckDBPyConnection) -> None:
    """验证 OHLCV 日级聚合查询（分钟->日线）性能."""
    conn = duckdb_with_10m_bars

    t_start = time.perf_counter()
    result = conn.execute("""
        SELECT
            date_trunc('day', timestamp) AS day,
            FIRST(open ORDER BY timestamp) AS open,
            MAX(high)                       AS high,
            MIN(low)                        AS low,
            LAST(close ORDER BY timestamp)  AS close,
            SUM(volume)                     AS volume
        FROM market_data
        WHERE symbol = 'BTC/USDT'
        GROUP BY day
        ORDER BY day
        LIMIT 100
    """).fetchall()
    elapsed_ms = (time.perf_counter() - t_start) * 1000

    print(f"\nOHLCV 日级聚合查询耗时: {elapsed_ms:.2f}ms，返回 {len(result)} 行")

    assert len(result) > 0, "聚合查询无结果"
    assert elapsed_ms < 500, f"聚合查询耗时 {elapsed_ms:.2f}ms，超过 500ms 阈值"


def test_latest_n_bars_query(duckdb_with_10m_bars: duckdb.DuckDBPyConnection) -> None:
    """验证获取最新 N 条 K 线的查询性能（实盘常用查询）."""
    conn = duckdb_with_10m_bars

    t_start = time.perf_counter()
    result = conn.execute("""
        SELECT timestamp, open, high, low, close, volume
        FROM market_data
        WHERE symbol = 'BTC/USDT'
        ORDER BY timestamp DESC
        LIMIT 500
    """).fetchall()
    elapsed_ms = (time.perf_counter() - t_start) * 1000

    print(f"\n获取最新 500 条 K 线耗时: {elapsed_ms:.2f}ms")

    assert len(result) == 500, f"期望 500 条，实际 {len(result)} 条"
    assert elapsed_ms < 200, f"查询耗时 {elapsed_ms:.2f}ms，超过 200ms 阈值"
