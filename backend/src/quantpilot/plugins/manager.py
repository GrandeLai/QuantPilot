"""QuantPilot 插件管理器 — pluggy 封装 + 热加载."""
from __future__ import annotations

import importlib
import inspect

import pluggy
from loguru import logger

from quantpilot.plugins.spec import QuantPilotSpec


class PluginManager:
    """管理所有已注册的 QuantPilot 插件."""

    def __init__(self) -> None:
        self._pm = pluggy.PluginManager("quantpilot")
        self._pm.add_hookspecs(QuantPilotSpec)
        self._registry: dict[str, object] = {}

    def register(self, plugin: object, name: str) -> None:
        """注册插件实例."""
        self._pm.register(plugin, name=name)
        self._registry[name] = plugin
        logger.info(f"[Plugins] 插件 '{name}' 已注册")

    def unregister(self, name: str) -> None:
        """注销插件."""
        plugin = self._registry.pop(name, None)
        if plugin is not None:
            self._pm.unregister(plugin)
            logger.info(f"[Plugins] 插件 '{name}' 已注销")

    def load_module(self, module_name: str) -> None:
        """从模块名热加载插件（importlib 重新加载）."""
        mod = importlib.import_module(module_name)
        # Only reload if the module has a real file-backed spec; dynamically
        # constructed modules (e.g., in tests) have no spec and cannot be reloaded.
        if getattr(mod, "__spec__", None) is not None:
            importlib.reload(mod)
        for attr_name, obj in inspect.getmembers(mod, inspect.isclass):
            if attr_name.startswith("_"):
                continue
            instance = obj()
            full_name = f"{module_name}.{attr_name}"
            self.register(instance, name=full_name)

    def list_plugins(self) -> list[dict[str, str]]:
        """返回所有已注册插件列表."""
        return [{"name": name, "type": type(p).__name__} for name, p in self._registry.items()]

    def fire_on_bar(self, symbol: str, close: float) -> list[str]:
        """触发 on_bar 钩子."""
        results: list[str] = self._pm.hook.on_bar(symbol=symbol, close=close)
        return [r for r in results if r is not None]

    def fire_on_signal(self, symbol: str, signal: str) -> list[str]:
        """触发 on_signal 钩子."""
        results: list[str] = self._pm.hook.on_signal(symbol=symbol, signal=signal)
        return [r for r in results if r is not None]

    def fire_on_alert(self, message: str) -> list[str]:
        """触发 on_alert 钩子."""
        results: list[str] = self._pm.hook.on_alert(message=message)
        return [r for r in results if r is not None]
