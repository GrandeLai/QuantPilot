"""Stock-assistant FastAPI 主应用入口（apps/stock-assistant/backend）.

覆盖股票 + 期权 + 加密的人决策交易、portfolio、screener、sentiment、
LLM 投顾、agent。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from quantpilot_common.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理：startup / shutdown."""
    settings = get_settings()
    logger.info(f"{settings.app_name} (stock-assistant) v{settings.app_version} 启动中...")

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.strategy_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    from quantpilot_common.redis.client import RedisClient
    try:
        await RedisClient.connect(settings.redis_url)
    except Exception as e:
        logger.warning(f"[Redis] 连接失败（降级运行）: {e}")

    logger.info("Stock-assistant API 启动成功")
    yield

    from quantpilot_common.redis.client import RedisClient as _RedisClient
    await _RedisClient.disconnect()
    logger.info("Stock-assistant API 正在关闭...")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} (Stock Assistant)",
        version=settings.app_version,
        description="QuantPilot 股票交易助手 API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:1420", "http://localhost:5173", "http://localhost:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def include_with_api_alias(router) -> None:
        app.include_router(router)
        app.include_router(router, prefix="/api")

    from quantpilot_stock.api.advisor import router as advisor_router
    from quantpilot_stock.api.alerts import router as alerts_router
    from quantpilot_stock.api.crypto import router as crypto_router
    from quantpilot_stock.api.crypto_derivs import router as crypto_derivs_router
    from quantpilot_stock.api.crypto_research import router as crypto_research_router
    from quantpilot_stock.api.data import router as data_router
    from quantpilot_stock.api.insights import router as insights_router
    from quantpilot_stock.api.llm import router as llm_router
    from quantpilot_stock.api.options import router as options_router
    from quantpilot_stock.api.paper import router as paper_router
    from quantpilot_stock.api.platform import router as platform_router
    from quantpilot_stock.api.plugins import router as plugins_router
    from quantpilot_stock.api.portfolio import router as portfolio_router
    from quantpilot_stock.api.risk import router as risk_router
    from quantpilot_stock.api.screener import router as screener_router
    from quantpilot_stock.api.security import router as security_router
    from quantpilot_stock.api.sentiment import router as sentiment_router
    from quantpilot_stock.api.trading import router as trading_router

    include_with_api_alias(data_router)
    include_with_api_alias(security_router)
    include_with_api_alias(paper_router)
    include_with_api_alias(alerts_router)
    include_with_api_alias(llm_router)
    include_with_api_alias(trading_router)
    include_with_api_alias(options_router)
    include_with_api_alias(portfolio_router)
    include_with_api_alias(plugins_router)
    include_with_api_alias(platform_router)
    include_with_api_alias(sentiment_router)
    include_with_api_alias(insights_router)
    include_with_api_alias(screener_router)
    include_with_api_alias(crypto_router)
    include_with_api_alias(risk_router)
    include_with_api_alias(crypto_derivs_router)
    include_with_api_alias(advisor_router)
    include_with_api_alias(crypto_research_router)

    from quantpilot_stock.api.ws import router as ws_router
    app.include_router(ws_router)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        from quantpilot_common.redis.client import RedisClient
        redis_ok = await RedisClient.ping()
        return {
            "status": "ok",
            "service": "stock-assistant",
            "version": settings.app_version,
            "redis": "connected" if redis_ok else "disconnected",
        }

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"message": "Welcome to QuantPilot Stock Assistant API"}

    return app


app = create_app()
