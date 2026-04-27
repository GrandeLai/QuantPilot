"""Markdown 复盘报告生成器."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from quantpilot_quant.backtest.engine import BacktestResult


class ReportGenerator:
    """使用 Jinja2 模板生成 Markdown 回测复盘报告."""

    def __init__(self) -> None:
        template_dir = Path(__file__).parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, result: BacktestResult) -> str:
        """生成 Markdown 报告字符串."""
        template = self._env.get_template("backtest_report.md.j2")
        return template.render(
            config=result.config,
            metrics=result.metrics,
            trades=result.trades,
            bars_processed=result.bars_processed,
            generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

    def save(self, result: BacktestResult, path: Path) -> None:
        """生成报告并写入文件."""
        content = self.generate(result)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
