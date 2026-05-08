import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.router import api_router
from app.tasks.scheduler import scheduler
from app.websocket.handlers import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.DEBUG:
        print(f"Starting {settings.APP_NAME} in debug mode...")

    # Create all database tables on startup
    from app.db.session import engine
    from app.db.base import Base
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if settings.DEBUG:
            print("Database tables verified/created successfully.")
    except Exception as e:
        print(f"Warning: Could not create tables: {e}")

    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return a JSON response."""
    detail = str(exc)
    if settings.DEBUG:
        traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": detail, "type": exc.__class__.__name__},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(ws_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
