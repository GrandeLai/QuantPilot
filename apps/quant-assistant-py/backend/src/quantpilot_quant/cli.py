"""QuantPilot quant-assistant-py 命令行工具."""

import typer
import uvicorn
from loguru import logger

app = typer.Typer(
    name="quantpilot-quant-py",
    help="QuantPilot 量化助手 (Python, Phase A 临时态) CLI",
)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="监听地址"),
    port: int = typer.Option(8002, help="监听端口"),
    reload: bool = typer.Option(False, help="热重载（开发模式）"),
) -> None:
    """启动 quant-py API 服务."""
    logger.info(f"启动 QuantPilot quant-py API 服务于 {host}:{port}")
    uvicorn.run(
        "quantpilot_quant.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def version() -> None:
    """显示版本号."""
    typer.echo("quantpilot-quant 0.1.0 (Phase A 临时态)")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
