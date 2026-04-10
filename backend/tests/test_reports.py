"""Markdown 复盘报告测试 — T-2.5 验收."""
from __future__ import annotations

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from quantpilot.backtest.engine import BacktestConfig, BacktestResult
from quantpilot.backtest.metrics import BacktestMetrics, TradeRecord
from quantpilot.reports.generator import ReportGenerator


def _make_result() -> BacktestResult:
    config = BacktestConfig(symbol="AAPL", timeframe="1d", initial_cash=100_000.0)
    metrics = BacktestMetrics(
        total_return=0.25,
        annual_return=0.18,
        sharpe_ratio=1.45,
        sortino_ratio=1.80,
        calmar_ratio=2.1,
        max_drawdown=-0.12,
        max_drawdown_duration=15,
        win_rate=0.58,
        profit_factor=1.9,
        total_trades=42,
        win_trades=24,
        loss_trades=18,
        avg_win=0.006,
    )
    trades = [
        TradeRecord(
            symbol="AAPL",
            entry_price=150.0,
            exit_price=165.0,
            quantity=100,
            entry_time=datetime(2024, 1, 10, tzinfo=UTC),
            exit_time=datetime(2024, 2, 5, tzinfo=UTC),
            side="long",
            commission=5.0,
        )
    ]
    return BacktestResult(config=config, metrics=metrics, trades=trades, bars_processed=250)


class TestReportGenerator:
    def test_generate_returns_string(self) -> None:
        gen = ReportGenerator()
        md = gen.generate(_make_result())
        assert isinstance(md, str)
        assert len(md) > 100

    def test_report_contains_symbol(self) -> None:
        gen = ReportGenerator()
        md = gen.generate(_make_result())
        assert "AAPL" in md

    def test_report_contains_sharpe(self) -> None:
        gen = ReportGenerator()
        md = gen.generate(_make_result())
        assert "1.45" in md

    def test_report_contains_max_drawdown(self) -> None:
        gen = ReportGenerator()
        md = gen.generate(_make_result())
        assert "12.00%" in md

    def test_report_contains_total_trades(self) -> None:
        gen = ReportGenerator()
        md = gen.generate(_make_result())
        assert "42" in md

    def test_report_has_markdown_headers(self) -> None:
        gen = ReportGenerator()
        md = gen.generate(_make_result())
        assert "# " in md
        assert "## " in md

    def test_save_to_file(self) -> None:
        gen = ReportGenerator()
        result = _make_result()
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            out_path = Path(f.name)
        gen.save(result, out_path)
        assert out_path.exists()
        content = out_path.read_text()
        assert "AAPL" in content
        out_path.unlink()
