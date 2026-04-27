"""策略类加载器."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

def load_strategy_class(name: str) -> type | None:
    """按策略名称加载策略类.

    支持两类来源：
    - 内置模板策略
    - 本地保存的用户策略（按 strategy_id 读取 .py 文件）
    """
    from quantpilot_quant.strategy.builtin import BUILTIN_STRATEGIES
    from quantpilot_quant.strategy.storage import StrategyStorage
    from quantpilot_quant.strategy.base import BaseStrategy
    from quantpilot_common.config import get_settings

    builtin = BUILTIN_STRATEGIES.get(name)
    if builtin is not None:
        return builtin

    strategy_dir: Path = get_settings().strategy_dir
    storage = StrategyStorage(strategy_dir)
    if not storage.exists(name):
        return None

    code_path = strategy_dir / f"{name}.py"
    if not code_path.exists():
        return None

    module_name = f"quantpilot_user_strategy_{name}"
    spec = importlib.util.spec_from_file_location(module_name, code_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for _, cls in inspect.getmembers(module, inspect.isclass):
        if (
            issubclass(cls, BaseStrategy)
            and cls is not BaseStrategy
            and cls.__module__ == module_name
        ):
            return cls

    return None
