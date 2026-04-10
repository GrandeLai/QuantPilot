"""策略管理 API 路由.

端点：
  GET  /strategies/templates   列出内置模板策略
  GET  /strategies             列出所有用户策略
  POST /strategies             创建策略
  GET  /strategies/{id}        获取策略详情
  PUT  /strategies/{id}        更新策略
  DELETE /strategies/{id}      删除策略
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from quantpilot.strategy.storage import StrategyMeta, StrategyRecord, StrategyStorage
from quantpilot.strategy.templates import TEMPLATE_STRATEGIES

router = APIRouter(prefix="/strategies", tags=["策略管理"])


def _get_storage() -> StrategyStorage:
    from quantpilot.config import get_settings
    settings = get_settings()
    return StrategyStorage(settings.strategy_dir)


class CreateStrategyRequest(BaseModel):
    name: str
    description: str = ""
    code: str
    tags: list[str] = []
    params: dict[str, object] = {}


class UpdateStrategyRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    code: str | None = None
    tags: list[str] | None = None
    params: dict[str, object] | None = None


@router.get("/templates")
def list_templates() -> dict[str, object]:
    """列出所有内置策略模板."""
    templates = []
    for key, cls in TEMPLATE_STRATEGIES.items():
        templates.append({
            "id": key,
            "name": cls.name,
            "description": cls.description,
            "version": cls.version,
            "default_params": cls.default_params,
        })
    return {"count": len(templates), "templates": templates}


@router.get("/templates/{template_id}/code")
def get_template_code(template_id: str) -> dict[str, str]:
    """获取模板策略源代码."""
    import inspect

    if template_id not in TEMPLATE_STRATEGIES:
        raise HTTPException(status_code=404, detail=f"模板不存在: {template_id}")
    cls = TEMPLATE_STRATEGIES[template_id]
    return {"template_id": template_id, "code": inspect.getsource(cls)}


@router.get("")
def list_strategies() -> dict[str, object]:
    """列出所有用户策略."""
    storage = _get_storage()
    metas = storage.list_all()
    return {"count": len(metas), "strategies": [m.model_dump() for m in metas]}


@router.post("")
def create_strategy(req: CreateStrategyRequest) -> dict[str, object]:
    """创建新策略."""
    storage = _get_storage()
    strategy_id = str(uuid.uuid4())[:8]
    record = StrategyRecord(
        meta=StrategyMeta(
            id=strategy_id,
            name=req.name,
            description=req.description,
            tags=req.tags,
            params=req.params,
        ),
        code=req.code,
    )
    storage.save(record)
    return {"id": strategy_id, "message": "策略创建成功", "meta": record.meta.model_dump()}


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str) -> dict[str, object]:
    """获取策略详情（含代码）."""
    storage = _get_storage()
    record = storage.load(strategy_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
    return record.model_dump()


@router.put("/{strategy_id}")
def update_strategy(strategy_id: str, req: UpdateStrategyRequest) -> dict[str, object]:
    """更新策略."""
    storage = _get_storage()
    record = storage.load(strategy_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")

    if req.name is not None:
        record.meta.name = req.name
    if req.description is not None:
        record.meta.description = req.description
    if req.code is not None:
        record.code = req.code
    if req.tags is not None:
        record.meta.tags = req.tags
    if req.params is not None:
        record.meta.params = req.params

    storage.save(record)
    return {"message": "策略更新成功", "meta": record.meta.model_dump()}


@router.delete("/{strategy_id}")
def delete_strategy(strategy_id: str) -> dict[str, str]:
    """删除策略."""
    storage = _get_storage()
    if not storage.delete(strategy_id):
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
    return {"message": f"策略 {strategy_id} 已删除"}


@router.get("/{strategy_id}/history")
def get_strategy_history(strategy_id: str) -> dict[str, object]:
    """获取策略的 Git 版本历史."""
    storage = _get_storage()
    record = storage.load(strategy_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"策略不存在: {strategy_id}")
    try:
        from quantpilot.config import get_settings
        from quantpilot.strategy.git_manager import GitManager
        gm = GitManager(get_settings().strategy_dir)
        history = gm.log(f"{strategy_id}.py")
    except Exception:
        history = []
    return {"strategy_id": strategy_id, "history": history}


@router.get("/{strategy_id}/versions/{sha}")
def get_strategy_version(strategy_id: str, sha: str) -> dict[str, str]:
    """获取策略指定版本的代码."""
    try:
        from quantpilot.config import get_settings
        from quantpilot.strategy.git_manager import GitManager
        gm = GitManager(get_settings().strategy_dir)
        code = gm.get_version(f"{strategy_id}.py", sha)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    if not code:
        raise HTTPException(status_code=404, detail="版本不存在")
    return {"strategy_id": strategy_id, "sha": sha, "code": code}
