"""AutoPilot Pipeline REST API."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from quantpilot_common.data import get_storage
from quantpilot.pipeline.orchestrator import PipelineJobState, PipelineOrchestrator, make_job

router = APIRouter(prefix="/pipeline", tags=["AutoPilot Pipeline"])

# in-memory job store
_JOBS: dict[str, PipelineJobState] = {}
_MAX_JOBS = 20


class PipelineRunRequest(BaseModel):
    """Request body for launching a pipeline run."""

    symbol: str = "BTC-USDT"
    timeframe: str = "1d"
    start_date: str = "2022-01-01"
    end_date: str = ""
    initial_cash: float = 10000.0


@router.post("/run")
async def run_pipeline(
    req: PipelineRunRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """启动 Pipeline，返回 job_id 供轮询."""
    storage = get_storage()
    state = make_job(req.model_dump())
    _JOBS[state.job_id] = state
    # keep only last _MAX_JOBS
    if len(_JOBS) > _MAX_JOBS:
        oldest = next(iter(_JOBS))
        del _JOBS[oldest]
    orch = PipelineOrchestrator(storage)
    background_tasks.add_task(orch.run, state)
    return {"job_id": state.job_id}


@router.get("/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    """查询 Pipeline 任务状态."""
    if job_id not in _JOBS:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return _JOBS[job_id].to_dict()


@router.get("/jobs")
def list_jobs() -> dict[str, Any]:
    """列出最近的 Pipeline 任务."""
    jobs = [
        {
            "job_id": j.job_id,
            "status": j.status.value,
            "current_step": j.current_step,
            "created_at": j.created_at,
            "finished_at": j.finished_at,
        }
        for j in reversed(list(_JOBS.values()))
    ]
    return {"jobs": jobs}
