from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.api.routes import users, sessions, profiles, statistics, expertise
from app.core.config import settings

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="User Profiling Service for HotLabel platform",
    version="0.1.0",
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable default redoc
    openapi_url=None,  # Disable default openapi
)

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
    return {"status": "healthy", "service": "user-profiling"}

# Root redirect to docs
@app.get("/", include_in_schema=False)
async def root_redirect():
    return {"message": "HotLabel User Profiling Service API", "docs": f"{settings.API_V1_STR}/docs"}
