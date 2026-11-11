from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="AI Studio API",
    description="Self-hosted AI image and video platform",
    version="0.2.0",
)

# Development-only CORS. Restrict origins before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

# Demo-only in-memory job store. Replace with PostgreSQL in a later milestone.
jobs: dict[str, dict] = {}


class GenerationRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=2000)
    generation_type: str = Field(pattern="^(image|video)$")


@app.get("/")
async def root():
    return {"name": "AI Studio", "status": "online", "version": "0.2.0"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/system")
async def system():
    return {
        "backend": "operational",
        "image_engine": "not_connected",
        "video_engine": "not_connected",
        "database": "not_connected",
        "queue": "not_connected",
    }


@app.post("/api/generations", status_code=202)
async def create_generation(request: GenerationRequest):
    job_id = str(uuid4())
    job = {
        "id": job_id,
        "prompt": request.prompt,
        "type": request.generation_type,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    jobs[job_id] = job
    return {"success": True, "message": "Demo job created", "job": job}


@app.get("/api/generations/{job_id}")
async def get_generation(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Generation job not found")
    return {"success": True, "job": job}
