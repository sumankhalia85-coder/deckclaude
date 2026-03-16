"""
DeckClaude FastAPI Application

Endpoints:
  POST /generate        — Start a generation job from JSON prompt/form data
  POST /generate/upload — Start a generation job with file upload
  GET  /status/{job_id} — Poll job status; returns download URL when ready
  GET  /download/{filename} — Download generated .pptx file
  GET  /health          — Health check
"""

import asyncio
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

load_dotenv()

# ---- Logging Setup ----
try:
    from rich.logging import RichHandler
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

logger = logging.getLogger("deckclaude.api")

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

UPLOAD_DIR = OUTPUT_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ---- In-Memory Job Store ----
# For production, replace with Redis or a database
jobs: Dict[str, Dict[str, Any]] = {}

# ---- FastAPI App ----
app = FastAPI(
    title="DeckClaude API",
    description="Multi-agent AI-powered PowerPoint generation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Pydantic Models ----

class GenerateRequest(BaseModel):
    prompt: str
    theme: Optional[str] = "default"
    slides: Optional[int] = None
    deck_type: Optional[str] = "strategy_deck"
    form_data: Optional[Dict[str, Any]] = None
    audience: Optional[str] = None
    tone: Optional[str] = None
    intent: Optional[str] = None
    include_charts: bool = True
    include_diagrams: bool = True
    include_images: bool = True


class JobStatus(BaseModel):
    job_id: str
    status: str  # queued | running | completed | failed
    progress_pct: Optional[float] = None
    message: Optional[str] = None
    output_filename: Optional[str] = None
    download_url: Optional[str] = None
    quality_score: Optional[float] = None
    error: Optional[str] = None
    created_at: float
    completed_at: Optional[float] = None
    total_time: Optional[float] = None


# ---- Background Task: Run Workflow ----

async def run_generation_job(job_id: str, user_input: dict):
    """Background task that runs the full deck generation workflow."""
    jobs[job_id]["status"] = "running"
    jobs[job_id]["message"] = "Running multi-agent pipeline..."

    def _run():
        from workflows.deck_workflow import run_workflow
        return run_workflow(user_input, show_progress=False)

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _run)

        if result.get("success") and result.get("output_path"):
            output_path = Path(result["output_path"])
            filename = output_path.name
            jobs[job_id].update({
                "status": "completed",
                "message": "Presentation generated successfully.",
                "output_filename": filename,
                "output_path": str(output_path),
                "download_url": f"/download/{filename}",
                "quality_score": result.get("quality_report", {}).get("overall_deck_score"),
                "completed_at": time.time(),
                "total_time": result.get("total_time"),
                "errors": result.get("errors", []),
            })
            logger.info(f"Job {job_id} completed: {filename}")
        else:
            errors = result.get("errors", ["Unknown error"])
            jobs[job_id].update({
                "status": "failed",
                "message": "Generation failed.",
                "error": "; ".join(errors),
                "completed_at": time.time(),
                "total_time": result.get("total_time"),
            })
            logger.error(f"Job {job_id} failed: {errors}")

    except Exception as e:
        logger.error(f"Job {job_id} raised exception: {e}", exc_info=True)
        jobs[job_id].update({
            "status": "failed",
            "message": "Internal error during generation.",
            "error": str(e),
            "completed_at": time.time(),
        })


def _create_job() -> str:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "message": "Job queued. Generation will begin shortly.",
        "output_filename": None,
        "download_url": None,
        "quality_score": None,
        "error": None,
        "created_at": time.time(),
        "completed_at": None,
        "total_time": None,
        "errors": [],
    }
    return job_id


# ---- Endpoints ----

@app.get("/health")
async def health_check():
    """Health check — verifies API is running and env is configured."""
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    provider = os.getenv("LLM_PROVIDER", "anthropic")

    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_provider": provider,
        "llm_configured": has_anthropic if provider == "anthropic" else has_openai,
        "output_dir": str(OUTPUT_DIR),
        "active_jobs": len(jobs),
    }


@app.post("/generate")
async def generate(request: GenerateRequest, background_tasks: BackgroundTasks):
    """
    Start a presentation generation job from a JSON prompt/form.

    Returns job_id immediately. Poll /status/{job_id} for progress.
    """
    if not request.prompt and not request.form_data:
        raise HTTPException(status_code=400, detail="Provide at least 'prompt' or 'form_data'.")

    # Build form_data with any explicit fields provided
    form_data = request.form_data or {}
    if request.audience:
        form_data["audience"] = request.audience
    if request.tone:
        form_data["tone"] = request.tone
    if request.intent:
        form_data["intent"] = request.intent

    user_input = {
        "prompt": request.prompt,
        "form_data": form_data if form_data else None,
        "requested_slides": request.slides,
        "requested_theme": request.theme,
        "deck_type": request.deck_type,
        "include_charts": request.include_charts,
        "include_diagrams": request.include_diagrams,
        "include_images": request.include_images,
    }

    job_id = _create_job()
    background_tasks.add_task(run_generation_job, job_id, user_input)

    logger.info(f"Job {job_id} queued: '{request.prompt[:80]}'")
    return {"job_id": job_id, "status": "queued", "message": "Generation started. Poll /status/{job_id}"}


@app.post("/generate/upload")
async def generate_with_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    prompt: str = Form(...),
    theme: str = Form("default"),
    slides: Optional[int] = Form(None),
):
    """
    Start a generation job with an uploaded file (PDF/CSV/Excel/JSON).

    Accepts multipart/form-data. Returns job_id immediately.
    """
    # Validate file type
    allowed_extensions = {".pdf", ".csv", ".xlsx", ".xls", ".json", ".txt"}
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed: {allowed_extensions}",
        )

    # Save uploaded file
    job_id = _create_job()
    save_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
    try:
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
        logger.info(f"Uploaded file saved: {save_path} ({len(content):,} bytes)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    user_input = {
        "prompt": prompt,
        "file_path": str(save_path),
        "file_name": file.filename,
        "requested_slides": slides,
        "requested_theme": theme,
    }

    background_tasks.add_task(run_generation_job, job_id, user_input)
    logger.info(f"Job {job_id} queued with file: {file.filename}")

    return {
        "job_id": job_id,
        "status": "queued",
        "file_received": file.filename,
        "file_size_bytes": len(content),
        "message": f"File received. Generation started. Poll /status/{job_id}",
    }


@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """
    Get the status of a generation job.
    When status is 'completed', download_url will be populated.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    # Calculate progress estimate based on status
    progress_map = {"queued": 0.0, "running": 50.0, "completed": 100.0, "failed": 0.0}
    progress = progress_map.get(job["status"], 0.0)

    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress_pct=progress,
        message=job.get("message"),
        output_filename=job.get("output_filename"),
        download_url=job.get("download_url"),
        quality_score=job.get("quality_score"),
        error=job.get("error"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
        total_time=job.get("total_time"),
    )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a generated PowerPoint file by filename.
    Files are served from the OUTPUT_DIR.
    """
    # Security: prevent path traversal
    safe_filename = Path(filename).name
    if safe_filename != filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = OUTPUT_DIR / safe_filename
    if not file_path.exists():
        # Check subdirectories
        found = list(OUTPUT_DIR.rglob(safe_filename))
        if found:
            file_path = found[0]
        else:
            raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    return FileResponse(
        path=str(file_path),
        filename=safe_filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'},
    )


@app.get("/jobs")
async def list_jobs():
    """List all jobs and their statuses (for debugging/monitoring)."""
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": jid,
                "status": j["status"],
                "created_at": j["created_at"],
                "total_time": j.get("total_time"),
            }
            for jid, j in sorted(jobs.items(), key=lambda x: x[1]["created_at"], reverse=True)[:50]
        ],
    }


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a job record and optionally its output file."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    # Remove output file if it exists
    if job.get("output_path"):
        try:
            Path(job["output_path"]).unlink(missing_ok=True)
        except Exception:
            pass

    del jobs[job_id]
    return {"deleted": job_id}


# ---- Main ----
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True,
        log_level="info",
    )
