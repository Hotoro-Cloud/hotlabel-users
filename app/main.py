import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.api.routes import users, sessions, profiles, statistics, expertise
from app.core.config import settings
from app.core.exceptions import ServiceException

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User Profiling Service for HotLabel platform",
    version="0.1.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url=None,  # Disable default openapi
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(profiles.router, prefix=settings.API_V1_STR)
app.include_router(statistics.router, prefix=settings.API_V1_STR)
app.include_router(expertise.router, prefix=settings.API_V1_STR)

# Exception handlers
@app.exception_handler(ServiceException)
async def service_exception_handler(request: Request, exc: ServiceException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": str(request.state.request_id) if hasattr(request.state, "request_id") else None,
            }
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "invalid_request",
                "message": "Request validation error",
                "details": {
                    "errors": exc.errors(),
                    "body": exc.body,
                },
                "request_id": str(request.state.request_id) if hasattr(request.state, "request_id") else None,
            }
        },
    )

# Custom docs URL with API prefix
@app.get(f"{settings.API_V1_STR}/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
    )

@app.get(f"{settings.API_V1_STR}/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=app.title + " - ReDoc",
    )

@app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
async def get_open_api_endpoint():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

# Ready check endpoint
@app.get("/ready", tags=["health"])
async def ready_check():
    # Check database connection
    from app.db.session import get_db
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        db_status = "error"
    
    # Check Redis connection
    from app.core.redis import get_redis_pool
    try:
        redis = await get_redis_pool()
        await redis.ping()
        redis_status = "ok"
    except Exception as e:
        logger.error(f"Redis connection failed: {str(e)}")
        redis_status = "error"
    
    status = "ok" if db_status == "ok" and redis_status == "ok" else "error"
    
    return {
        "status": status,
        "service": settings.SERVICE_NAME,
        "dependencies": {
            "database": db_status,
            "redis": redis_status
        }
    }

# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root_redirect():
    return {"message": "HotLabel User Profiling Service API", "docs": f"{settings.API_V1_STR}/docs"}
