"""
Project Manager Agent — orchestrates the 8-agent pipeline using asyncio.
Uses in-memory state for real-time SSE + fresh DB sessions per write.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from services import sse
from workers.idea_validator import IdeaValidatorWorker
from workers.strategy_planner import StrategyPlannerWorker
from workers.product_architect import ProductArchitectWorker
from workers.code_generator import CodeGeneratorWorker
from workers.security_reviewer import SecurityReviewerWorker
from workers.copywriter import CopywriterWorker
from workers.seo_optimizer import SEOOptimizerWorker

logger = logging.getLogger(__name__)

AGENT_ORDER = [
    "idea_validator", "strategy_planner", "product_architect",
    "code_generator", "security_reviewer", "copywriter", "seo_optimizer"
]

# In-memory pipeline state for active pipelines
PIPELINE_MEMORY: dict = {}


async def _db_write(pipeline_id: str, agents_state: dict,
                    status: str = "running", completed_at: Optional[str] = None) -> None:
    """Persist state to DB using a fresh session each time."""
    try:
        from database import AsyncSessionLocal
        from models.pipeline import Pipeline
        from sqlalchemy import select
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
            p = res.scalar_one_or_none()
            if p:
                p.agents_state = dict(agents_state)
                p.status = status
                if completed_at:
                    p.completed_at = datetime.fromisoformat(completed_at)
                db.add(p)
                await db.commit()
    except Exception as e:
        logger.error(f"DB write failed {pipeline_id}: {e}")


async def _update_agent(pipeline_id: str, agent_id: str, status: str,
                        result=None, error: Optional[str] = None) -> None:
    """Update in-memory state, push SSE, schedule DB write."""
    mem = PIPELINE_MEMORY.setdefault(pipeline_id, {})
    agents = mem.setdefault("agents", {})
    now = datetime.utcnow().isoformat()
    entry = dict(agents.get(agent_id, {"agentId": agent_id}))
    entry["status"] = status
    if status == "in_progress" and "startedAt" not in entry:
        entry["startedAt"] = now
    if status in ("complete", "failed"):
        entry["completedAt"] = now
    if result is not None:
        entry["result"] = result
    if error:
        entry["error"] = error
    agents[agent_id] = entry

    await sse.publish(pipeline_id, "agent_update", {
        "agentId": agent_id, "status": status,
        "startedAt": entry.get("startedAt"),
        "completedAt": entry.get("completedAt"),
        "result": result, "error": error,
    })
    asyncio.create_task(_db_write(pipeline_id, agents))


async def start_pipeline(idea_text: str, pipeline_id: str) -> None:
    """Main pipeline coroutine. Call via asyncio.create_task()."""
    logger.info(f"Pipeline {pipeline_id} starting")
    PIPELINE_MEMORY[pipeline_id] = {
        "pipelineId": pipeline_id, "ideaText": idea_text, "status": "running",
        "agents": {aid: {"agentId": aid, "status": "queued"} for aid in AGENT_ORDER},
    }
    await _db_write(pipeline_id, PIPELINE_MEMORY[pipeline_id]["agents"])
    ctx: dict = {}

    async def run(agent_id: str, worker_cls, prompt_ctx: dict) -> dict:
        await _update_agent(pipeline_id, agent_id, "in_progress")
        try:
            result = await worker_cls().run(idea_text, prompt_ctx)
            await _update_agent(pipeline_id, agent_id, "complete", result=result)
            logger.info(f"  ✓ {agent_id} done")
            return result
        except Exception as e:
            logger.error(f"  ✗ {agent_id} failed: {e}", exc_info=True)
            await _update_agent(pipeline_id, agent_id, "failed", error=str(e))
            return {"error": str(e)}

    try:
        ctx["idea_validator"] = await run("idea_validator", IdeaValidatorWorker, {})
        s, a = await asyncio.gather(
            asyncio.create_task(run("strategy_planner", StrategyPlannerWorker, dict(ctx))),
            asyncio.create_task(run("product_architect", ProductArchitectWorker, dict(ctx)))
        )
        ctx["strategy_planner"], ctx["product_architect"] = s, a
        ctx["code_generator"] = await run("code_generator", CodeGeneratorWorker, dict(ctx))
        ctx["security_reviewer"] = await run("security_reviewer", SecurityReviewerWorker, dict(ctx))
        cpy, seo = await asyncio.gather(
            asyncio.create_task(run("copywriter", CopywriterWorker, dict(ctx))),
            asyncio.create_task(run("seo_optimizer", SEOOptimizerWorker, dict(ctx)))
        )
        ctx["copywriter"], ctx["seo_optimizer"] = cpy, seo

        ts = datetime.utcnow().isoformat()
        PIPELINE_MEMORY[pipeline_id].update({"status": "complete", "completedAt": ts})
        await _db_write(pipeline_id, PIPELINE_MEMORY[pipeline_id]["agents"], "complete", ts)
        await sse.publish(pipeline_id, "pipeline_complete", PIPELINE_MEMORY[pipeline_id])
        logger.info(f"Pipeline {pipeline_id} complete ✅")

    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} error: {e}", exc_info=True)
        ts = datetime.utcnow().isoformat()
        PIPELINE_MEMORY[pipeline_id].update({"status": "failed", "completedAt": ts})
        await _db_write(pipeline_id, PIPELINE_MEMORY[pipeline_id].get("agents", {}), "failed", ts)
        await sse.publish(pipeline_id, "pipeline_failed", {"pipelineId": pipeline_id, "error": str(e)})
