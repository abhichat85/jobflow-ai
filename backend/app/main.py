from contextlib import asynccontextmanager
import traceback
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import Base, engine
from app.routes.profile import router as profile_router
from app.routes.jobs import router as jobs_router
from app.routes.assets import router as assets_router
from app.routes.outreach import router as outreach_router
from app.routes.crm import router as crm_router
from app.routes.interviews import router as interviews_router
from app.routes.discovery import router as discovery_router
from app.routes.settings import router as settings_router
from app.routes.system import router as system_router
from app.routes.apply import router as apply_router

ALLOWED_ORIGINS = ["http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    for subdir in ["db", "profiles", "assets", "templates"]:
        (settings.data_dir / subdir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="JobFlow AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Ensure CORS headers are present even on unhandled 500 errors."""
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    tb = traceback.format_exc()
    print(f"[ERROR] Unhandled exception on {request.method} {request.url}:\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__},
        headers=headers,
    )

app.include_router(profile_router)
app.include_router(jobs_router)
app.include_router(assets_router)
app.include_router(outreach_router)
app.include_router(crm_router)
app.include_router(interviews_router)
app.include_router(discovery_router)
app.include_router(settings_router)
app.include_router(system_router)
app.include_router(apply_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
