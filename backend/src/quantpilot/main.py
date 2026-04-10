"""QuantPilot FastAPI 主应用入口."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from quantpilot.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理：startup / shutdown."""
    settings = get_settings()
    logger.info(f"{settings.app_name} v{settings.app_version} 启动中...")

    # 确保数据目录存在
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.strategy_dir.mkdir(parents=True, exist_ok=True)
    settings.log_dir.mkdir(parents=True, exist_ok=True)

    # 连接 Redis
    from quantpilot.redis.client import RedisClient
    try:
        await RedisClient.connect(settings.redis_url)
    except Exception as e:
        logger.warning(f"[Redis] 连接失败（降级运行）: {e}")

    logger.info("QuantPilot API 启动成功")
    yield

    # 断开 Redis
    from quantpilot.redis.client import RedisClient as _RedisClient
    await _RedisClient.disconnect()
    logger.info("QuantPilot API 正在关闭...")


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="本地优先的个人量化交易平台 API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:1420", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 注册 API 路由 ────────────────────────────────────────────────────────
    from quantpilot.api.backtest import router as backtest_router
    from quantpilot.api.data import router as data_router
    from quantpilot.api.indicators import router as indicators_router
    from quantpilot.api.security import router as security_router
    from quantpilot.api.strategy import router as strategy_router

    app.include_router(data_router)
    app.include_router(indicators_router)
    app.include_router(strategy_router)
    app.include_router(backtest_router)
    app.include_router(security_router)

    from quantpilot.api.alerts import router as alerts_router
    from quantpilot.api.llm import router as llm_router
    from quantpilot.api.paper import router as paper_router
    from quantpilot.api.reports import router as reports_router
    app.include_router(paper_router)
    app.include_router(alerts_router)
    app.include_router(reports_router)
    app.include_router(llm_router)

    from quantpilot.api.factors import router as factors_router
    from quantpilot.api.optimize import router as optimize_router
    from quantpilot.api.options import router as options_router
    from quantpilot.api.portfolio import router as portfolio_router
    app.include_router(factors_router)
    app.include_router(options_router)
    app.include_router(optimize_router)
    app.include_router(portfolio_router)

    from quantpilot.api.plugins import router as plugins_router
    app.include_router(plugins_router, prefix="/api")

    from quantpilot.api.sentiment import router as sentiment_router
    app.include_router(sentiment_router, prefix="/api")

    from quantpilot.api.ml import router as ml_router
    app.include_router(ml_router, prefix="/api")

    from quantpilot.api.signals import router as signals_router
    app.include_router(signals_router, prefix="/api")

    from quantpilot.api.insights import router as insights_router
    app.include_router(insights_router, prefix="/api")

    from quantpilot.api.ws import router as ws_router
    app.include_router(ws_router)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """健康检查端点."""
        from quantpilot.redis.client import RedisClient
        redis_ok = await RedisClient.ping()
        return {
            "status": "ok",
            "version": settings.app_version,
            "redis": "connected" if redis_ok else "disconnected",
        }

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        """根路径."""
        return {"message": f"Welcome to {settings.app_name} API"}

    return app


app = create_app()
