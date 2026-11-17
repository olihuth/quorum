import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.legislative import SyncResultOut
from app.workers.ingestion import poll_recent_bills, sync_politicians

router = APIRouter(prefix="/admin", tags=["Admin Ingestion"])


def _verify_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    expected = get_settings().admin_api_key
    if not x_admin_key or not hmac.compare_digest(x_admin_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave administrativa inválida ou ausente.",
        )


@router.post("/sync/politicians", response_model=SyncResultOut, dependencies=[Depends(_verify_admin_key)])
def trigger_sync_politicians(db: Session = Depends(get_db)) -> SyncResultOut:
    """Manually trigger Track A batch synchronization of politicians."""
    result = sync_politicians(db)
    return SyncResultOut(**result)


@router.post("/sync/bills", response_model=SyncResultOut, dependencies=[Depends(_verify_admin_key)])
def trigger_sync_bills(db: Session = Depends(get_db)) -> SyncResultOut:
    """Manually trigger Track B polling of recent bills."""
    result = poll_recent_bills(db)
    return SyncResultOut(**result)
