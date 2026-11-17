from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.bills import record_bill_vote
from app.schemas.legislative import IoTVoteRequest, VoteResponse

router = APIRouter(prefix="/iot", tags=["IoT Civic Totem"])


@router.post("/vote", response_model=VoteResponse)
def ingest_totem_vote(
    payload: IoTVoteRequest,
    db: Session = Depends(get_db),
) -> VoteResponse:
    """Record a vote originating from an Arduino/Tinkercad civic totem."""
    token = payload.session_token or uuid4().hex
    raw_identifier = f"iot-totem:{payload.totem_id.strip()}:{token}"
    return record_bill_vote(
        db=db,
        bill_id=payload.bill_id,
        raw_identifier=raw_identifier,
        choice=payload.choice,
        source="iot_totem",
    )
