"""QuantPilot 命令行工具."""

import typer
import uvicorn
from loguru import logger

app = typer.Typer(
    name="quantpilot",
    help="QuantPilot — 本地优先的个人量化交易平台 CLI",
)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="监听地址"),
    port: int = typer.Option(8000, help="监听端口"),
    reload: bool = typer.Option(False, help="热重载（开发模式）"),
) -> None:
    """启动 API 服务."""
    logger.info(f"启动 QuantPilot API 服务于 {host}:{port}")
    uvicorn.run(
        "quantpilot.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def version() -> None:
    """显示版本信息."""
    from quantpilot import __version__

    typer.echo(f"QuantPilot v{__version__}")


if __name__ == "__main__":
    app()
