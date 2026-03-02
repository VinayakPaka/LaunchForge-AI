"""Pipeline router — start, status, SSE stream, ZIP download."""
import asyncio
import io
import json
import uuid
import zipfile
from typing import Optional
from services import pdf_gen

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.pipeline import Pipeline, PipelineStatus
from services import sse as sse_service
from services.orchestrator import start_pipeline, PIPELINE_MEMORY
from database import get_db

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class StartPipelineRequest(BaseModel):
    ideaText: str = Field(..., min_length=20, max_length=2000)
    userId: Optional[str] = "anonymous"
    tier: Optional[str] = "free"


class StartPipelineResponse(BaseModel):
    pipelineId: str
    status: str
    message: str


@router.post("/start", response_model=StartPipelineResponse)
async def start(body: StartPipelineRequest, db: AsyncSession = Depends(get_db)):
    """Create a pipeline record and launch background agent execution."""
    pipeline_id = str(uuid.uuid4())
    pipeline = Pipeline(
        id=pipeline_id,
        user_id=body.userId or "anonymous",
        idea_text=body.ideaText,
        status=PipelineStatus.RUNNING,
        agents_state={},
    )
    db.add(pipeline)
    await db.commit()

    # Launch pipeline as asyncio task (avoids BackgroundTasks session conflicts)
    asyncio.create_task(start_pipeline(body.ideaText, pipeline_id))

    return StartPipelineResponse(
        pipelineId=pipeline_id,
        status="running",
        message="Pipeline started. Connect to SSE stream for real-time updates.",
    )


@router.get("/{pipeline_id}/status")
async def get_status(pipeline_id: str, db: AsyncSession = Depends(get_db)):
    """Return current pipeline state — checks in-memory first, then DB."""
    # Fast path: in-memory state for active pipelines
    if pipeline_id in PIPELINE_MEMORY:
        return PIPELINE_MEMORY[pipeline_id]
    # Fall back to DB
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline.to_dict()


@router.get("/{pipeline_id}/stream")
async def stream(pipeline_id: str, db: AsyncSession = Depends(get_db)):
    """SSE endpoint — streams real-time agent status events."""
    # Accept if in-memory or in DB
    in_memory = pipeline_id in PIPELINE_MEMORY
    if not in_memory:
        result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Pipeline not found")

    return StreamingResponse(
        sse_service.event_stream(pipeline_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/{pipeline_id}/download")
async def download_zip(pipeline_id: str, db: AsyncSession = Depends(get_db)):
    """
    Generate and stream a ZIP containing:
    - 7 styled PDFs (one per agent section)
    - Raw MVP source code files under mvp_code/
    - README.md
    """
    # Fetch state
    state = PIPELINE_MEMORY.get(pipeline_id)
    if not state:
        result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
        p = result.scalar_one_or_none()
        if not p:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        state = p.to_dict()

    agents = state.get("agents", {})
    idea   = state.get("ideaText", "Your Startup Idea")
    buf    = io.BytesIO()

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # ── README ──────────────────────────────────────────────────────────
        zf.writestr(
            "README.md",
            f"# LaunchForge AI — Startup Launch Package\n\n"
            f"**Idea:** {idea}\n\n"
            f"## PDF Reports\n"
            f"| File | Contents |\n"
            f"|------|----------|\n"
            f"| `reports/01_business_validation.pdf` | Market validation, opportunity score, competitors |\n"
            f"| `reports/02_gtm_strategy.pdf`        | GTM plan, pricing tiers, launch timeline |\n"
            f"| `reports/03_technical_architecture.pdf` | Tech stack, API endpoints, data models |\n"
            f"| `reports/04_security_audit.pdf`      | OWASP Top 10 audit, vulnerability details |\n"
            f"| `reports/05_marketing_kit.pdf`       | Landing copy, pitch deck (10 slides) |\n"
            f"| `reports/06_seo_strategy.pdf`        | Keywords, meta tags, content plan |\n"
            f"| `reports/07_mvp_code_overview.pdf`   | MVP file listing + code snippets |\n\n"
            f"## MVP Source Code\n"
            f"Raw generated source files are under `mvp_code/`.\n\n"
            f"Generated by [LaunchForge AI](https://tb314nms.run.complete.dev)\n"
        )

        # ── Styled PDFs ──────────────────────────────────────────────────────
        pdf_files = pdf_gen.build_all_pdfs(agents, idea)
        for filename, pdf_bytes in pdf_files:
            zf.writestr(f"reports/{filename}", pdf_bytes)

        # ── MVP source code files ────────────────────────────────────────────
        code     = agents.get("code_generator", {}).get("result", {})
        src_files = code.get("files", [])
        if isinstance(src_files, list):
            for f in src_files:
                if isinstance(f, dict) and f.get("path") and f.get("content"):
                    zf.writestr(f"mvp_code/{f['path']}", str(f["content"]))
        # .env.example
        env_vars = code.get("envVariables", [])
        if env_vars:
            zf.writestr(
                "mvp_code/.env.example",
                "\n".join(str(v) for v in env_vars) + "\n"
            )

    buf.seek(0)
    slug     = idea[:30].replace(" ", "-").lower()
    zip_name = f"launchforge-{slug}.zip"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_name}"'},
    )


@router.get("/list/{user_id}")
async def list_pipelines(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Pipeline).where(Pipeline.user_id == user_id).order_by(Pipeline.created_at.desc())
    )
    return [p.to_dict() for p in result.scalars().all()]
