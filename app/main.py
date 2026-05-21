from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import video_router, r2_router
from app.config import app_config
from app.logging_config import setup_logging, get_logger
from app.exceptions import AppException

# Setup logging
setup_logging(app_config.log_level)
logger = get_logger(__name__)

app = FastAPI(
    title="Video Transcript Search API",
    description="API for uploading videos, generating transcripts, and searching through them",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.error(
        f"App exception: {exc.message}",
        extra={
            "extra_fields": {
                "error_code": exc.code,
                "status_code": exc.status_code,
                "path": str(request.url),
                "method": request.method,
            },
        },
    )
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

app.include_router(video_router, prefix="/api")
app.include_router(r2_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to the Video Transcript Search API!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
