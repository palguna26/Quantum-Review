"""FastAPI application entry point."""
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.config import get_settings
from app.logging_config import setup_logging, get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    setup_logging(use_json=settings.RENDER, level="DEBUG" if settings.DEBUG else "INFO")
    logger.info("Starting QuantumReview backend", extra={"version": settings.APP_VERSION})
    
    # Initialize database connection pool
    from app.adapters.db import init_db, close_db
    from app.services.github_auth import init_redis, close_redis
    # Optional Mongo adapter
    from app.adapters.mongo import init_mongo, close_mongo
    await init_db()
    await init_redis()
    await init_mongo()
    
    yield
    
    # Shutdown
    logger.info("Shutting down QuantumReview backend")
    await close_db()
    await close_redis()
    await close_mongo()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request ID to logger context
    logger = get_logger(__name__)
    old_factory = logging.getLogRecordFactory()
    
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        # Only set request_id if it hasn't been set already to avoid
        # KeyError: "Attempt to overwrite 'request_id' in LogRecord" when
        # callers pass the same key via `extra=` in logging calls.
        if not hasattr(record, "request_id"):
            record.request_id = request_id
        return record
    
    logging.setLogRecordFactory(record_factory)
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger = get_logger(__name__)
    request_id = getattr(request.state, "request_id", "unknown")
    # Avoid passing `extra` to logger.error here because logging.makeRecord
    # can raise KeyError if the same key already exists on the LogRecord.
    # Include the request_id in the message instead.
    logger.error(f"Unhandled exception [{request_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for readiness probes."""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Include routers
from app.api import auth, routes, events, github as github_api
from app.webhooks import github

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(routes.router, prefix="/api", tags=["api"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(github.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(github_api.router, prefix="/api", tags=["github"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }

