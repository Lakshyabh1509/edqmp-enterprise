from app.api.quality import router as quality_router
from app.api.pipelines import router as pipelines_router
from app.api.alerts import router as alerts_router
from app.api.auth import router as auth_router

__all__ = ["quality_router", "pipelines_router", "alerts_router", "auth_router"]
