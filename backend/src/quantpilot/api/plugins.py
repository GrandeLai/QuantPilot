"""插件管理 API.

端点:
  GET  /plugins           列出已注册插件
  POST /plugins/reload    热加载指定模块中的插件
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from quantpilot.plugins.manager import PluginManager

router = APIRouter(prefix="/plugins", tags=["插件系统"])

_manager = PluginManager()


class ReloadRequest(BaseModel):
    module_name: str


@router.get("")
def list_plugins() -> dict[str, Any]:
    """列出所有已注册插件."""
    return {"plugins": _manager.list_plugins(), "count": len(_manager.list_plugins())}


@router.post("/reload")
def reload_module(req: ReloadRequest) -> dict[str, Any]:
    """从指定 Python 模块热加载插件."""
    _manager.load_module(req.module_name)
    return {"message": f"模块 '{req.module_name}' 插件已热加载", "plugins": _manager.list_plugins()}
