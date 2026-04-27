"""Quant-assistant-py FastAPI 主应用入口（apps/quant-assistant-py/backend）.

Phase A 临时态——量化研究 + 规则化执行后端，端口 8002。
Step 4（Rust quant 对齐）后整目录删除。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from quantpilot_common.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(f"{settings.app_name} (quant-py) v{settings.app_version} 启动中...")

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.strategy_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    from quantpilot_common.redis.client import RedisClient
    try:
        await RedisClient.connect(settings.redis_url)
    except Exception as e:
        logger.warning(f"[Redis] 连接失败（降级运行）: {e}")

    logger.info("Quant-py API 启动成功")
    yield

    from quantpilot_common.redis.client import RedisClient as _RedisClient
    await _RedisClient.disconnect()
    logger.info("Quant-py API 正在关闭...")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} (Quant Assistant Py)",
        version=settings.app_version,
        description="QuantPilot 量化助手 Python 临时态后端",
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

    from quantpilot_quant.api.advisor import router as advisor_router
    from quantpilot_quant.api.backtest import router as backtest_router
    from quantpilot_quant.api.crypto_research import router as crypto_research_router
    from quantpilot_quant.api.factors import router as factors_router
    from quantpilot_quant.api.indicators import router as indicators_router
    from quantpilot_quant.api.ml import router as ml_router
    from quantpilot_quant.api.optimize import router as optimize_router
    from quantpilot_quant.api.pipeline import router as pipeline_router
    from quantpilot_quant.api.reports import router as reports_router
    from quantpilot_quant.api.signals import router as signals_router
    from quantpilot_quant.api.strategy import router as strategy_router

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
            "service": "quant-assistant-py",
            "version": settings.app_version,
            "redis": "connected" if redis_ok else "disconnected",
        }

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"message": "Welcome to QuantPilot Quant Assistant (Python, transitional)"}

    return app


app = create_app()
