"""
EDQMP - Enterprise Data Quality & Monitoring Platform
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_database
from app.api import quality_router, pipelines_router, alerts_router, auth_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info(f"Starting EDQMP v{settings.app_version}")
    init_database()
    yield
    logger.info("Shutting down EDQMP")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Enterprise Data Quality & Monitoring Platform API",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}


# Include routers
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(quality_router, prefix=settings.api_prefix)
app.include_router(pipelines_router, prefix=settings.api_prefix)
app.include_router(alerts_router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs"
    }
