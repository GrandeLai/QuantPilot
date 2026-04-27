"""Golden generator CLI (Phase A skeleton).

Phase B+ 时实现：
- generate: 跑 quantpilot_quant.{indicators, factors, walk_forward, backtest} 在固定输入上，
  写期望输出到 common/data-store/golden/expected/
- verify-python: 重跑 generate 并断言与已有 expected 一致

当前为占位，仅暴露 CLI 结构供后续扩展。
"""

import typer

app = typer.Typer(
    name="golden-generator",
    help="QuantPilot 跨语言行为等价基准数据集生成器（Phase A skeleton）",
)


@app.command()
def generate(
    case_id: str = typer.Option("all", help="case 标识，'all' 为全部"),
) -> None:
    """生成黄金期望输出（Phase B+ 实现）."""
    typer.echo(f"[golden-generator] generate(case_id={case_id}) — Phase A skeleton, not yet implemented")
    typer.echo("Phase B+ 时此命令调 quant-py 的回测/因子函数，写 common/data-store/golden/expected/")


@app.command()
def verify_python(
    case_id: str = typer.Option("all", help="case 标识"),
) -> None:
    """验证 Python 实现仍符合 golden expected（Phase B+ 实现）."""
    typer.echo(f"[golden-generator] verify-python(case_id={case_id}) — Phase A skeleton, not yet implemented")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
