from contextlib import asynccontextmanager
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete, func, select

from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.models.legislative import Bill, CitizenVote, OfficialVote, Politician
from app.routers import admin, auth, bills, dashboard, houses, iot, politicians
from app.workers.ingestion import sync_politicians
from app.workers.seed import seed_database

logger = logging.getLogger(__name__)
settings = get_settings()


def _scheduled_sync_politicians() -> None:
    db = SessionLocal()
    try:
        sync_politicians(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize schema, bootstrap curated bills, and sync real politicians & compositions."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)

        if settings.enable_scheduler:
            # Keep only the curated example bills in the default feed.
            uncurated_ids = db.scalars(
                select(Bill.id).where(Bill.external_id.like("camara-pl-%"))
            ).all()
            if uncurated_ids:
                db.execute(delete(CitizenVote).where(CitizenVote.bill_id.in_(uncurated_ids)))
                db.execute(delete(OfficialVote).where(OfficialVote.bill_id.in_(uncurated_ids)))
                db.execute(delete(Bill).where(Bill.id.in_(uncurated_ids)))
                db.commit()

            # Sync real federal deputies, senators, and house party compositions if not yet populated.
            politician_count = db.scalar(select(func.count(Politician.id))) or 0
            if politician_count < 100:
                sync_politicians(db)
    finally:
        db.close()

    scheduler: BackgroundScheduler | None = None
    if settings.enable_scheduler:
        scheduler = BackgroundScheduler()
        scheduler.add_job(_scheduled_sync_politicians, "interval", hours=24, id="sync_politicians")
        scheduler.start()
        logger.info("APScheduler started for Quorum real politician & composition sync (24h).")

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
