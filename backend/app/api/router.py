from fastapi import APIRouter

from app.api.admin_files import router as admin_files_router
from app.api.admin_logs import router as admin_logs_router
from app.api.auth import router as auth_router
from app.api.files import router as files_router
from app.api.folders import router as folders_router
from app.api.health import router as health_router
from app.api.recycle import router as recycle_router
from app.api.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(files_router)
api_router.include_router(folders_router)
api_router.include_router(admin_files_router)
api_router.include_router(admin_logs_router)
api_router.include_router(recycle_router)
api_router.include_router(upload_router)
