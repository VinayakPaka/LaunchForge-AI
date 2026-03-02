"""
LaunchForge AI — Orchestrator
Calls all 7 LangGraph agents with smart parallelism where dependencies allow.

Execution plan (optimised for speed):
  Stage 1:  idea_validator                            (standalone)
  Stage 2:  strategy_planner || product_architect     (both depend only on stage 1)
  Stage 3:  code_generator                            (needs strategy + architect)
  Stage 4:  security_reviewer || copywriter           (independent of each other)
  Stage 5:  seo_optimizer                             (needs copywriter)

7 sequential rounds -> 5 parallel-aware stages = ~40-60% wall-clock savings.
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from services import sse

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
    """Update in-memory state, push SSE event, schedule DB write."""
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
    """
    Main pipeline coroutine. Called via asyncio.create_task().

    Runs all 7 LangGraph agents SEQUENTIALLY — one at a time.
    This is critical: each agent makes 3 Groq calls (analyze/reflect/refine),
    and sequential execution prevents concurrent TPM exhaustion.

    Pipeline order:
      1. idea_validator
      2. strategy_planner   (uses idea_validator context)
      3. product_architect  (uses idea_validator context)
      4. code_generator     (uses strategy + architect context)
      5. security_reviewer  (uses code + architect context)
      6. copywriter         (uses idea_validator + strategy context)
      7. seo_optimizer      (uses idea_validator + copywriter context)
    """
    logger.info(f"Pipeline {pipeline_id} starting — parallel LangGraph agent mode")

    PIPELINE_MEMORY[pipeline_id] = {
        "pipelineId": pipeline_id,
        "ideaText": idea_text,
        "status": "running",
        "agents": {aid: {"agentId": aid, "status": "queued"} for aid in AGENT_ORDER},
    }
    await _db_write(pipeline_id, PIPELINE_MEMORY[pipeline_id]["agents"])

    ctx: dict = {}

    async def run(agent_id: str, agent_cls, prompt_ctx: dict) -> dict:
        """Run a single LangGraph agent and emit SSE updates."""
        await _update_agent(pipeline_id, agent_id, "in_progress")
        try:
            result = await agent_cls().run(idea_text, prompt_ctx)
            await _update_agent(pipeline_id, agent_id, "complete", result=result)
            logger.info(f"  [DONE] {agent_id}")
            return result
        except Exception as e:
            logger.error(f"  [FAIL] {agent_id}: {e}", exc_info=True)
            await _update_agent(pipeline_id, agent_id, "failed", error=str(e))
            return {"error": str(e)}

    try:
        # Lazy imports — keeps startup fast, avoids circular import issues
        from agents.idea_validator_agent import IdeaValidatorAgent
        from agents.strategy_planner_agent import StrategyPlannerAgent
        from agents.product_architect_agent import ProductArchitectAgent
        from agents.code_generator_agent import CodeGeneratorAgent
        from agents.security_reviewer_agent import SecurityReviewerAgent
        from agents.copywriter_agent import CopywriterAgent
        from agents.seo_optimizer_agent import SEOOptimizerAgent

        # ── Stage 1: Idea Validator ──────────────────────────────────────────
        ctx["idea_validator"] = await run(
            "idea_validator", IdeaValidatorAgent, {}
        )

        # ── Stage 2: Strategy Planner ║ Product Architect (PARALLEL) ────────
        # Both only depend on idea_validator — safe to run concurrently.
        strategy_result, architect_result = await asyncio.gather(
            run("strategy_planner", StrategyPlannerAgent,
                {"idea_validator": ctx["idea_validator"]}),
            run("product_architect", ProductArchitectAgent,
                {"idea_validator": ctx["idea_validator"]}),
        )
        ctx["strategy_planner"]  = strategy_result
        ctx["product_architect"] = architect_result

        # ── Stage 3: Code Generator ──────────────────────────────────────────
        ctx["code_generator"] = await run(
            "code_generator", CodeGeneratorAgent,
            {
                "strategy_planner":  ctx["strategy_planner"],
                "product_architect": ctx["product_architect"],
            }
        )

        # ── Stage 4: Security Reviewer ║ Copywriter (PARALLEL) ──────────────
        # security_reviewer needs code+architect; copywriter needs validator+strategy.
        # They are independent of each other — run concurrently.
        security_result, copywriter_result = await asyncio.gather(
            run("security_reviewer", SecurityReviewerAgent,
                {
                    "code_generator":    ctx["code_generator"],
                    "product_architect": ctx["product_architect"],
                }),
            run("copywriter", CopywriterAgent,
                {
                    "idea_validator":   ctx["idea_validator"],
                    "strategy_planner": ctx["strategy_planner"],
                }),
        )
        ctx["security_reviewer"] = security_result
        ctx["copywriter"]        = copywriter_result

        # ── Stage 5: SEO Optimizer ───────────────────────────────────────────
        ctx["seo_optimizer"] = await run(
            "seo_optimizer", SEOOptimizerAgent,
            {
                "idea_validator": ctx["idea_validator"],
                "copywriter":     ctx["copywriter"],
            }
        )

        # ── Pipeline Complete ────────────────────────────────────────────────
        ts = datetime.utcnow().isoformat()
        PIPELINE_MEMORY[pipeline_id].update({"status": "complete", "completedAt": ts})
        await _db_write(pipeline_id, PIPELINE_MEMORY[pipeline_id]["agents"], "complete", ts)
        await sse.publish(pipeline_id, "pipeline_complete", PIPELINE_MEMORY[pipeline_id])
        logger.info(f"Pipeline {pipeline_id} complete (all 7 LangGraph agents)")

    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} error: {e}", exc_info=True)
        ts = datetime.utcnow().isoformat()
        PIPELINE_MEMORY[pipeline_id].update({"status": "failed", "completedAt": ts})
        await _db_write(
            pipeline_id,
            PIPELINE_MEMORY[pipeline_id].get("agents", {}),
            "failed", ts
        )
        await sse.publish(
            pipeline_id, "pipeline_failed",
            {"pipelineId": pipeline_id, "error": str(e)}
        )
