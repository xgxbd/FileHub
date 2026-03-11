from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.router import api_router
from app.core.config import settings
from app.db import SessionLocal, init_db
from app.services.admin_bootstrap_service import ensure_admin_user

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        ensure_admin_user(db)
    yield


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_frontend_dist_dir() -> Path:
    if settings.frontend_dist_dir:
        return Path(settings.frontend_dist_dir).expanduser().resolve()
    # backend/app/main.py -> repo -> frontend/dist
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


if settings.app_serve_frontend:
    app.include_router(api_router, prefix="/api")
    frontend_dist_dir = _resolve_frontend_dist_dir()
    frontend_index = frontend_dist_dir / "index.html"

    if frontend_index.exists():
        @app.get("/", include_in_schema=False)
        def serve_index():
            return FileResponse(frontend_index)

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_spa(full_path: str):
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="接口不存在")
            candidate = (frontend_dist_dir / full_path).resolve()
            if candidate.is_file() and frontend_dist_dir in candidate.parents:
                return FileResponse(candidate)
            return FileResponse(frontend_index)
    else:
        logger.warning(
            "APP_SERVE_FRONTEND=true 但未找到前端构建产物：%s；当前仅提供 /api 接口",
            frontend_index,
        )
else:
    app.include_router(api_router)
