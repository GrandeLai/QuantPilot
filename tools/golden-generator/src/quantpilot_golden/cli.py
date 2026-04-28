"""Golden generator CLI.

Phase B 起 generate 命令实际生效：跑 case 模块的 generator 函数，
写期望输出到 ``common/data-store/golden/expected/``。
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from loguru import logger

app = typer.Typer(
    name="golden-generator",
    help="QuantPilot 跨语言行为等价基准数据集生成器",
)


def _repo_root() -> Path:
    """从此文件回溯到仓库根 (Users/bytedance/code/QuantPilot)."""
    p = Path(__file__).resolve()
    for parent in (p, *p.parents):
        if (parent / "common" / "data-store").is_dir() and (parent / "tools").is_dir():
            return parent
    raise RuntimeError("Failed to locate repo root from golden-generator")


def _expected_dir() -> Path:
    return _repo_root() / "common" / "data-store" / "golden" / "expected"


def _write_case(case_id: str, payload: dict) -> Path:
    out_dir = _expected_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{case_id}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


@app.command()
def generate(
    case_id: str = typer.Option("all", help="case 标识，'all' 为全部"),
) -> None:
    """生成黄金期望输出."""
    cases_to_run: list[str]
    if case_id == "all":
        cases_to_run = ["ma_crossover_basic"]
    else:
        cases_to_run = [case_id]

    for cid in cases_to_run:
        if cid == "ma_crossover_basic":
            from quantpilot_golden.cases.ma_crossover import generate_ma_crossover_basic

            payload = generate_ma_crossover_basic()
            out_path = _write_case(cid, payload)
            logger.info(f"[golden] {cid} → {out_path}")
            typer.echo(f"✓ {cid} → {out_path.relative_to(_repo_root())}")
        else:
            typer.echo(f"unknown case: {cid}", err=True)
            raise typer.Exit(code=1)


@app.command()
def verify_python(
    case_id: str = typer.Option("all", help="case 标识"),
) -> None:
    """验证 Python 实现仍符合 golden expected.

    重跑 generate 并对比当前 expected JSON；浮点容差按 case 内 tolerance 字段。
    """
    cases_to_check: list[str]
    if case_id == "all":
        cases_to_check = ["ma_crossover_basic"]
    else:
        cases_to_check = [case_id]

    for cid in cases_to_check:
        out_path = _expected_dir() / f"{cid}.json"
        if not out_path.exists():
            typer.echo(f"{cid}: expected file missing — run `generate` first", err=True)
            raise typer.Exit(code=1)

        existing = json.loads(out_path.read_text(encoding="utf-8"))

        if cid == "ma_crossover_basic":
            from quantpilot_golden.cases.ma_crossover import generate_ma_crossover_basic

            fresh = generate_ma_crossover_basic()
        else:
            typer.echo(f"unknown case: {cid}", err=True)
            raise typer.Exit(code=1)

        # Compare equity_curve element-wise
        diff = max(
            abs(a - b)
            for a, b in zip(
                existing["expected"]["equity_curve"],
                fresh["expected"]["equity_curve"],
                strict=True,
            )
        )
        if diff > existing["tolerance"]["abs"]:
            typer.echo(f"{cid}: DRIFT detected (max abs diff = {diff:.3e})", err=True)
            raise typer.Exit(code=1)
        typer.echo(f"✓ {cid}: stable (max abs diff = {diff:.3e})")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
