"""Walk-Forward 窗口切割 golden cases.

实现与 Rust ``apps/quant-assistant/backend/src/walk_forward.rs::build_walk_forward_windows``
和 Python ``quantpilot_quant.research.validation.build_walk_forward_windows``
**逐行对齐**的独立 Python 算法（不 import 任何 app 代码，避免测试自引用）。

走 window 切割路径完全相同：
  cursor = train_size
  while True:
      train_end   = cursor - 1
      test_start  = train_end + 1 + embargo_size
      test_end    = test_start + test_size - 1
      train_start = train_end - train_size + 1
      if train_start < 0 or test_end >= total_rows: break
      windows.append(...)
      cursor += step_size
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int

    def to_dict(self) -> dict[str, int]:
        return {
            "train_start": self.train_start,
            "train_end": self.train_end,
            "test_start": self.test_start,
            "test_end": self.test_end,
        }


def python_build_walk_forward_windows(
    *,
    total_rows: int,
    train_size: int,
    test_size: int,
    step_size: int,
    embargo_size: int = 0,
) -> list[ValidationWindow]:
    """与 Rust build_walk_forward_windows 逐行对齐的 Python 参考实现.

    注意：这是独立实现，不依赖 quantpilot_quant 内部代码。
    """
    windows: list[ValidationWindow] = []
    cursor = train_size

    while True:
        train_end = cursor - 1
        test_start = train_end + 1 + embargo_size
        test_end = test_start + test_size - 1
        train_start = train_end - train_size + 1

        if train_start < 0 or test_end >= total_rows:
            break

        windows.append(
            ValidationWindow(
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        cursor += step_size

    return windows


# ── Fixed test configurations ─────────────────────────────────────────────────

TEST_CONFIGS: list[dict[str, Any]] = [
    # 最基本用例（无 embargo）
    {
        "name": "basic_no_embargo",
        "total_rows": 30,
        "train_size": 10,
        "test_size": 5,
        "step_size": 5,
        "embargo_size": 0,
    },
    # 带 embargo（隔离带）
    {
        "name": "with_embargo",
        "total_rows": 50,
        "train_size": 15,
        "test_size": 8,
        "step_size": 8,
        "embargo_size": 2,
    },
    # 大一点的数据集（接近回测实际使用规模）
    {
        "name": "realistic_100bars",
        "total_rows": 100,
        "train_size": 30,
        "test_size": 15,
        "step_size": 10,
        "embargo_size": 3,
    },
    # 数据不足，预期产出 0 个窗口
    {
        "name": "insufficient_data",
        "total_rows": 20,
        "train_size": 15,
        "test_size": 10,
        "step_size": 5,
        "embargo_size": 0,
    },
]


def generate_walk_forward_splits_basic() -> dict[str, Any]:
    """生成 walk_forward_splits_basic golden case."""
    cases = []
    for cfg in TEST_CONFIGS:
        wins = python_build_walk_forward_windows(
            total_rows=cfg["total_rows"],
            train_size=cfg["train_size"],
            test_size=cfg["test_size"],
            step_size=cfg["step_size"],
            embargo_size=cfg["embargo_size"],
        )
        cases.append(
            {
                "name": cfg["name"],
                "config": {
                    "total_rows": cfg["total_rows"],
                    "train_size": cfg["train_size"],
                    "test_size": cfg["test_size"],
                    "step_size": cfg["step_size"],
                    "embargo_size": cfg["embargo_size"],
                },
                "expected_windows": [w.to_dict() for w in wins],
                "n_windows": len(wins),
            }
        )

    return {
        "case_id": "walk_forward_splits_basic",
        "description": (
            "Walk-forward window splitting — bit-identical index check "
            "across 4 configurations (no tolerance, exact integer match)"
        ),
        "cases": cases,
        "tolerance": {
            "abs": 0,
            "rel": 0,
            "note": "整数索引 bit-identical，无容差",
        },
    }


def main() -> None:
    """生成并写出 walk_forward_splits_basic.json."""
    data = generate_walk_forward_splits_basic()
    out_path = (
        Path(__file__).parents[5]  # repo root: QuantPilot/
        / "common"
        / "data-store"
        / "golden"
        / "expected"
        / "walk_forward_splits_basic.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
