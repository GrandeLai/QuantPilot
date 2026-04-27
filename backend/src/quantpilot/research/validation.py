"""时间序列验证窗口构建器.

数据契约（TimeSeriesValidationConfig、ValidationWindow）已下沉到
``quantpilot_common.contracts.validation``；构建函数 ``build_walk_forward_windows``
仍是量化模块的内部实现。
"""

from __future__ import annotations

from quantpilot_common.contracts.validation import (
    TimeSeriesValidationConfig,
    ValidationWindow,
)

__all__ = [
    "TimeSeriesValidationConfig",
    "ValidationWindow",
    "build_walk_forward_windows",
]


def build_walk_forward_windows(
    *,
    total_rows: int,
    config: TimeSeriesValidationConfig,
) -> list[ValidationWindow]:
    """按时间顺序构建 walk-forward 窗口."""
    windows: list[ValidationWindow] = []
    cursor = config.train_size

    while True:
        train_end = cursor - 1
        test_start = train_end + 1 + config.embargo_size
        test_end = test_start + config.test_size - 1
        train_start = train_end - config.train_size + 1

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
        cursor += config.step_size

    return windows
