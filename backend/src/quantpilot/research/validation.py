"""时间序列验证窗口构建器."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimeSeriesValidationConfig:
    """Walk-forward / embargo 验证参数."""

    train_size: int
    test_size: int
    step_size: int
    embargo_size: int = 0


@dataclass(frozen=True, slots=True)
class ValidationWindow:
    """单个时间序列训练/验证窗口."""

    train_start: int
    train_end: int
    test_start: int
    test_end: int


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
