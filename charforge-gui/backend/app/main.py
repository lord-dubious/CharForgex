from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from pathlib import Path

from app.core.config import settings
from app.core.database import engine, Base
from app.core.security import rate_limit_middleware, security_headers_middleware
from app.api import auth, training, inference, media, datasets, models, settings as settings_api

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CharForge GUI API",
    description="API for CharForge AI Character LoRA Creation",
    version="1.0.0"
)

# CORS configuration - Enhanced for remote access
# Only allow all origins in development mode
cors_origins = settings.ALLOWED_ORIGINS
if os.getenv("ENVIRONMENT", "development") == "development":
    cors_origins = ["*"]  # Allow all origins only in development

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error reporting."""
    import logging
    import traceback

    # Log the error
    logging.error(f"Global exception on {request.url}: {str(exc)}")
    logging.error(traceback.format_exc())

    # Return appropriate error response
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # For unexpected errors, return generic message
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Add security middleware
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(security_headers_middleware)

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
os.makedirs(settings.RESULTS_DIR, exist_ok=True)

# Mount static files
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")
app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")

# Include routers
# Conditionally include auth router only if authentication is enabled
if settings.ENABLE_AUTH:
    app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(inference.router, prefix="/api/inference", tags=["inference"])
app.include_router(media.router, prefix="/api/media", tags=["media"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(settings_api.router, prefix="/api/settings", tags=["settings"])

@app.get("/")
async def root():
    return {"message": "CharForge GUI API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        access_log=True,
        log_level="info"
    )
