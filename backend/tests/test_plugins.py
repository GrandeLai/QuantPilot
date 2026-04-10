"""插件系统测试 — T-4.1 验收."""
from __future__ import annotations

import sys
import types

from quantpilot.plugins.manager import PluginManager
from quantpilot.plugins.spec import QuantPilotSpec


class ConcretePlugin:
    """实现所有钩子的测试插件."""

    @QuantPilotSpec.hookimpl
    def on_bar(self, symbol: str, close: float) -> str:
        return f"bar:{symbol}:{close}"

    @QuantPilotSpec.hookimpl
    def on_signal(self, symbol: str, signal: str) -> str:
        return f"sig:{symbol}:{signal}"

    @QuantPilotSpec.hookimpl
    def on_alert(self, message: str) -> str:
        return f"alert:{message}"


class TestQuantPilotSpec:
    def test_hookimpl_marker_exists(self) -> None:
        assert hasattr(QuantPilotSpec, "hookimpl")

    def test_hookspec_methods_defined(self) -> None:
        spec = QuantPilotSpec()
        assert callable(spec.on_bar)
        assert callable(spec.on_signal)
        assert callable(spec.on_alert)


class TestPluginManager:
    def test_register_and_list(self) -> None:
        pm = PluginManager()
        plugin = ConcretePlugin()
        pm.register(plugin, name="test_plugin")
        plugins = pm.list_plugins()
        assert any(p["name"] == "test_plugin" for p in plugins)

    def test_fire_on_bar(self) -> None:
        pm = PluginManager()
        pm.register(ConcretePlugin(), name="p1")
        results = pm.fire_on_bar("AAPL", 150.0)
        assert "bar:AAPL:150.0" in results

    def test_fire_on_signal(self) -> None:
        pm = PluginManager()
        pm.register(ConcretePlugin(), name="p1")
        results = pm.fire_on_signal("AAPL", "buy")
        assert "sig:AAPL:buy" in results

    def test_fire_on_alert(self) -> None:
        pm = PluginManager()
        pm.register(ConcretePlugin(), name="p1")
        results = pm.fire_on_alert("price spike")
        assert "alert:price spike" in results

    def test_hot_reload_module(self) -> None:
        mod_name = "fake_plugin_mod"
        src = (
            "from quantpilot.plugins.spec import QuantPilotSpec\n"
            "class FakePlugin:\n"
            "    @QuantPilotSpec.hookimpl\n"
            "    def on_alert(self, message: str) -> str:\n"
            "        return f'fake:{message}'\n"
        )
        mod = types.ModuleType(mod_name)
        exec(compile(src, mod_name, "exec"), mod.__dict__)  # noqa: S102
        sys.modules[mod_name] = mod

        pm = PluginManager()
        pm.load_module(mod_name)
        plugins = pm.list_plugins()
        assert any("fake" in p["name"].lower() or "FakePlugin" in p["name"] for p in plugins)

    def test_unregister_plugin(self) -> None:
        pm = PluginManager()
        plugin = ConcretePlugin()
        pm.register(plugin, name="removable")
        pm.unregister("removable")
        plugins = pm.list_plugins()
        assert not any(p["name"] == "removable" for p in plugins)
