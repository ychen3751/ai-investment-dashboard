import asyncio
import logging
import sys
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

logging.basicConfig(level=logging.INFO if settings.is_production else logging.DEBUG)
logger = logging.getLogger(__name__)

RETRY_ATTEMPTS = 5
RETRY_DELAY = 3  # seconds


async def wait_for_database(engine) -> bool:
    """Retry database connection up to RETRY_ATTEMPTS times on startup."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as exc:
            logger.warning("DB connection attempt %d/%d failed: %s", attempt, RETRY_ATTEMPTS, exc)
            if attempt < RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_DELAY)
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (debug=%s)", settings.APP_NAME, settings.DEBUG)

    # ── Database ──────────────────────────────────────────────────────
    from app.db.session import engine
    from app.db.base import Base

    db_ok = await wait_for_database(engine)
    if not db_ok:
        logger.error("Could not connect to database after %d attempts. Exiting.", RETRY_ATTEMPTS)
        sys.exit(1)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified/created.")
    except Exception as e:
        logger.warning("Table creation failed (non-fatal): %s", e)

    # ── Background jobs ───────────────────────────────────────────────
    try:
        scheduler.start()
        logger.info("Background scheduler started.")
    except Exception as e:
        logger.warning("Scheduler failed to start (non-fatal): %s", e)

    yield

    scheduler.shutdown(wait=False)
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
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
    return {"status": "ok", "app": settings.APP_NAME, "debug": settings.DEBUG}
