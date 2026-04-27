"""QuantPilot legacy backend FastAPI 主应用入口.

Phase A 过渡态：仅注册尚未迁出的量化路由（backtest, factors, ml, signals,
strategy, optimize, reports, pipeline, indicators, advisor, crypto_research,
portfolio）。这些将在 PR 5 时迁到 ``apps/quant-assistant-py/``，本文件届时删除。

人决策类路由（trading, paper, sentiment, screener, options, crypto, alerts,
security, ws, platform, plugins, data, insights, llm）已迁到
``apps/stock-assistant/backend/src/quantpilot_stock/main.py``（Phase A PR 4）.
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
    logger.info(f"{settings.app_name} (legacy/quant) v{settings.app_version} 启动中...")

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.strategy_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    from quantpilot_common.redis.client import RedisClient
    try:
        await RedisClient.connect(settings.redis_url)
    except Exception as e:
        logger.warning(f"[Redis] 连接失败（降级运行）: {e}")

    logger.info("QuantPilot legacy API 启动成功")
    yield

    from quantpilot_common.redis.client import RedisClient as _RedisClient
    await _RedisClient.disconnect()
    logger.info("QuantPilot legacy API 正在关闭...")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} (legacy/quant)",
        version=settings.app_version,
        description="QuantPilot legacy backend — Phase A 过渡态，仅含量化路由",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:1420", "http://localhost:5173", "http://localhost:5175"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def include_with_api_alias(router) -> None:
        app.include_router(router)
        app.include_router(router, prefix="/api")

    # 量化路由（PR 5 将迁到 apps/quant-assistant-py/）
    from quantpilot.api.advisor import router as advisor_router
    from quantpilot.api.backtest import router as backtest_router
    from quantpilot.api.crypto_research import router as crypto_research_router
    from quantpilot.api.factors import router as factors_router
    from quantpilot.api.indicators import router as indicators_router
    from quantpilot.api.ml import router as ml_router
    from quantpilot.api.optimize import router as optimize_router
    from quantpilot.api.pipeline import router as pipeline_router
    from quantpilot.api.reports import router as reports_router
    from quantpilot.api.signals import router as signals_router
    from quantpilot.api.strategy import router as strategy_router

    include_with_api_alias(strategy_router)
    include_with_api_alias(backtest_router)
    include_with_api_alias(indicators_router)
    include_with_api_alias(reports_router)
    include_with_api_alias(factors_router)
    include_with_api_alias(optimize_router)
    include_with_api_alias(ml_router)
    include_with_api_alias(signals_router)
    include_with_api_alias(advisor_router)
    include_with_api_alias(crypto_research_router)
    include_with_api_alias(pipeline_router)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        from quantpilot_common.redis.client import RedisClient
        redis_ok = await RedisClient.ping()
        return {
            "status": "ok",
            "service": "legacy-quant",
            "version": settings.app_version,
            "redis": "connected" if redis_ok else "disconnected",
        }

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"message": "Welcome to QuantPilot legacy backend (quant routes only; PR 5 will move these)"}

    return app


app = create_app()
