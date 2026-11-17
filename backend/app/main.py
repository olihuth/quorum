from contextlib import asynccontextmanager
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.routers import admin, auth, bills, dashboard, houses, iot, politicians
from app.workers.ingestion import poll_recent_bills, sync_politicians
from app.workers.seed import seed_database

logger = logging.getLogger(__name__)
settings = get_settings()


def _scheduled_sync_politicians() -> None:
    db = SessionLocal()
    try:
        sync_politicians(db)
    finally:
        db.close()


def _scheduled_poll_bills() -> None:
    db = SessionLocal()
    try:
        poll_recent_bills(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize schema, bootstrap Portuguese mock/seed data, and start ingestion scheduler."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()

    scheduler: BackgroundScheduler | None = None
    if settings.enable_scheduler:
        scheduler = BackgroundScheduler()
        scheduler.add_job(_scheduled_sync_politicians, "interval", hours=24, id="sync_politicians")
        scheduler.add_job(_scheduled_poll_bills, "interval", minutes=10, id="poll_recent_bills")
        scheduler.start()
        logger.info("APScheduler started for Quorum ingestion tracks A & B.")

    try:
        yield
    finally:
        if scheduler and scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API de transparência legislativa, arquitetura Medalhão e participação cidadã do Quorum.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(houses.router, prefix=settings.api_v1_prefix)
app.include_router(politicians.router, prefix=settings.api_v1_prefix)
app.include_router(bills.router, prefix=settings.api_v1_prefix)
app.include_router(iot.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Liveness check endpoint."""
    return {"status": "ok", "service": "quorum-backend"}
