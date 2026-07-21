import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.rate_limit import limiter
from app.routers import admin, health, submissions

settings = get_settings()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Día del Niño - Tienda Inglesa")

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_origin_regex=settings.CORS_ALLOW_ORIGIN_REGEX,
    allow_credentials=False,  # bearer tokens in headers, not cookies - no credentials mode needed
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Wrapped in "detail" to match FastAPI's default HTTPException envelope shape, so
    # the frontend can always read error.response.data.detail regardless of which
    # handler produced the response.
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": {"error": "rate_limited", "message": "Demasiadas solicitudes, intente nuevamente más tarde."}},
        headers={"Retry-After": str(getattr(exc, "retry_after", 60))},
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": {"error": "internal_error", "message": "Ocurrió un error inesperado."}},
    )


app.include_router(health.router)
app.include_router(submissions.router)
app.include_router(admin.login_router)
app.include_router(admin.router)
