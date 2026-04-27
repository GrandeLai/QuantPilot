"""LLM 工具定义 — Function Calling 接口."""
from __future__ import annotations

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """返回 OpenAI function calling 格式的工具列表."""
    return [
        {
            "type": "function",
            "function": {
                "name": "fetch_bars",
                "description": "获取指定标的的历史K线数据（OHLCV）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "标的代码，如 AAPL, 600519"},
                        "timeframe": {"type": "string", "description": "K线周期: 1m/5m/15m/1h/4h/1d/1w"},
                        "limit": {"type": "integer", "description": "返回条数，默认100", "default": 100},
                    },
                    "required": ["symbol"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "calculate_indicator",
                "description": "计算技术指标，如 RSI、MACD、布林带等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                        "timeframe": {"type": "string"},
                        "indicator": {"type": "string", "description": "指标名: rsi/macd/bbands/ema/..."},
                        "params": {"type": "object", "description": "指标参数，如 {period: 14}"},
                    },
                    "required": ["symbol", "indicator"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_strategies",
                "description": "列出所有已保存的策略",
                "parameters": {"type": "object", "properties": {}},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_market_summary",
                "description": "获取标的最新行情摘要（最新价、涨跌幅、成交量）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string"},
                    },
                    "required": ["symbol"],
                },
            },
        },
    ]


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """执行工具调用并返回结果字符串."""
    try:
        if tool_name == "fetch_bars":
            from quantpilot_common.config import get_settings
            from quantpilot_common.data.storage import MarketDataStorage

            settings = get_settings()
            storage = MarketDataStorage(settings.duckdb_path)
            symbol = arguments["symbol"]
            timeframe = arguments.get("timeframe", "1d")
            limit = arguments.get("limit", 100)
            df = storage.query_bars(symbol, timeframe, limit=limit)
            if df.is_empty():
                return f"暂无 {symbol} 的 {timeframe} 数据"
            return f"{symbol} {timeframe} 最近 {len(df)} 根K线，最新收盘价: {df['close'][-1]:.4f}"

        if tool_name == "list_strategies":
            from quantpilot_common.config import get_settings
            from quantpilot.strategy.storage import StrategyStorage

            settings = get_settings()
            storage = StrategyStorage(settings.strategy_dir)
            metas = storage.list_all()
            if not metas:
                return "暂无保存的策略"
            return "策略列表:\n" + "\n".join(f"- {m.name} (id: {m.id})" for m in metas)

        return f"工具 {tool_name} 执行结果: {arguments}"
    except Exception as e:
        return f"工具执行失败: {e}"
