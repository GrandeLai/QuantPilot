"""复盘报告 API.

端点:
  POST /reports/backtest   根据回测结果生成 Markdown 报告（返回纯文本）
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from quantpilot.backtest.engine import BacktestConfig, BacktestResult
from quantpilot.backtest.metrics import BacktestMetrics, TradeRecord
from quantpilot.reports.generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["复盘报告"])
_gen = ReportGenerator()


class BacktestReportRequest(BaseModel):
    """回测报告生成请求体."""

    config: BacktestConfig
    metrics: BacktestMetrics
    trades: list[TradeRecord] = []
    bars_processed: int = 0


@router.post("/backtest", response_class=PlainTextResponse)
def generate_backtest_report(req: BacktestReportRequest) -> str:
    """生成回测 Markdown 复盘报告."""
    result = BacktestResult(
        config=req.config,
        metrics=req.metrics,
        trades=req.trades,
        bars_processed=req.bars_processed,
    )
    return _gen.generate(result)


class PushFeishuRequest(BaseModel):
    """推送飞书文档请求."""

    config: BacktestConfig
    metrics: BacktestMetrics
    trades: list[TradeRecord] = []
    bars_processed: int = 0
    feishu_app_id: str
    feishu_app_secret: str
    doc_title: str = "QuantPilot 回测报告"


@router.post("/push-feishu")
async def push_feishu_report(req: PushFeishuRequest) -> dict[str, str]:
    """生成回测报告并推送至飞书云文档."""
    from quantpilot.reports.feishu_doc import FeishuDocPusher

    result = BacktestResult(
        config=req.config,
        metrics=req.metrics,
        trades=req.trades,
        bars_processed=req.bars_processed,
    )
    markdown = _gen.generate(result)
    pusher = FeishuDocPusher(app_id=req.feishu_app_id, app_secret=req.feishu_app_secret)
    doc = await pusher.push_markdown(markdown, req.doc_title)
    return {"document_id": doc.document_id, "url": doc.url, "title": doc.title}
