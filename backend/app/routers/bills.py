from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import hash_citizen_identifier
from app.models.legislative import Bill, CitizenVote, LegislativeHouse, Politician
from app.schemas.legislative import (
    BillOut,
    BillTranslatePreviewRequest,
    BillTranslatePreviewResponse,
    CitizenVoteRequest,
    LikeResponse,
    VoteResponse,
)
from app.services.llm_service import translate_bill_preview

router = APIRouter(prefix="/bills", tags=["Bills"])


def _compute_percentages(votes_favor: int, votes_against: int) -> tuple[float, float]:
    total = votes_favor + votes_against
    if total <= 0:
        return 50.0, 50.0
    favor_pct = round((votes_favor / total) * 100, 1)
    against_pct = round(100.0 - favor_pct, 1)
    return favor_pct, against_pct


def _to_bill_out(bill: Bill) -> BillOut:
    favor_pct, against_pct = _compute_percentages(bill.votes_favor, bill.votes_against)
    author = bill.author
    return BillOut(
        id=bill.id,
        external_id=bill.external_id,
        number=bill.number,
        year=bill.year,
        title=bill.title,
        theme=bill.theme,
        house_slug=bill.house.slug,
        house_short_name=bill.house.short_name,
        level=bill.house.level,
        author_id=author.id if author else None,
        author_name=author.name if author else None,
        author_party=author.party.acronym if author and author.party else None,
        author_state=author.state if author else None,
        official_summary=bill.official_summary,
        desjuridiques_summary=bill.desjuridiques_summary or [],
        status=bill.status,
        next_vote_at=bill.next_vote_at,
        is_urgent_vote=bill.is_urgent_vote,
        likes_count=bill.likes_count,
        votes_favor=bill.votes_favor,
        votes_against=bill.votes_against,
        favor_percentage=favor_pct,
        against_percentage=against_pct,
        official_approval_rate=bill.official_approval_rate,
        updated_at=bill.updated_at,
    )


def record_bill_vote(
    db: Session,
    bill_id: int,
    raw_identifier: str,
    choice: str,
    source: str,
) -> VoteResponse:
    """Persist an anonymized SHA-256 vote and atomically update bill counters."""
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto de lei não encontrado.",
        )

    citizen_hash = hash_citizen_identifier(raw_identifier)
    existing = db.scalar(
        select(CitizenVote).where(
            CitizenVote.bill_id == bill_id,
            CitizenVote.citizen_hash == citizen_hash,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voto já registrado para este cidadão neste projeto de lei.",
        )

    vote_row = CitizenVote(
        bill_id=bill_id,
        citizen_hash=citizen_hash,
        choice=choice,
        source=source,
    )
    db.add(vote_row)

    if choice == "favor":
        bill.votes_favor += 1
    else:
        bill.votes_against += 1

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Voto já registrado para este cidadão neste projeto de lei.",
        ) from exc

    db.refresh(bill)
    favor_pct, against_pct = _compute_percentages(bill.votes_favor, bill.votes_against)
    total = bill.votes_favor + bill.votes_against

    return VoteResponse(
        bill_id=bill.id,
        choice=choice,
        source=source,
        votes_favor=bill.votes_favor,
        votes_against=bill.votes_against,
        total_votes=total,
        favor_percentage=favor_pct,
        against_percentage=against_pct,
        message="Voto registrado com sucesso na enquete cidadã.",
    )


@router.post("/translate-preview", response_model=BillTranslatePreviewResponse)
def translate_bill_preview_endpoint(
    payload: BillTranslatePreviewRequest,
) -> BillTranslatePreviewResponse:
    """Live Desjuridiquês translation preview with before/after Portuguese readability metrics."""
    result = translate_bill_preview(payload.title, payload.official_summary)
    return BillTranslatePreviewResponse(**result)


@router.get("", response_model=list[BillOut])
def list_bills(
    house_slug: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[BillOut]:
    """List bills with Desjuridiquês summaries and live citizen poll tallies."""
    stmt = (
        select(Bill)
        .options(
            joinedload(Bill.house),
            joinedload(Bill.author).joinedload(Politician.party),
        )
        .order_by(Bill.is_urgent_vote.desc(), Bill.id)
    )
    if house_slug:
        stmt = stmt.join(Bill.house).where(LegislativeHouse.slug == house_slug)
    if status_filter:
        stmt = stmt.where(Bill.status == status_filter)

    bills = db.scalars(stmt).unique().all()
    return [_to_bill_out(bill) for bill in bills]


@router.get("/{bill_id}", response_model=BillOut)
def get_bill(bill_id: int, db: Session = Depends(get_db)) -> BillOut:
    """Return a single bill with its Desjuridiquês summary and tallies."""
    stmt = (
        select(Bill)
        .options(
            joinedload(Bill.house),
            joinedload(Bill.author).joinedload(Politician.party),
        )
        .where(Bill.id == bill_id)
    )
    bill = db.scalars(stmt).unique().first()
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto de lei não encontrado.",
        )
    return _to_bill_out(bill)


@router.post("/{bill_id}/vote", response_model=VoteResponse)
def vote_on_bill(
    bill_id: int,
    payload: CitizenVoteRequest,
    db: Session = Depends(get_db),
) -> VoteResponse:
    """Cast 1 anonymized citizen vote per bill (HTTP 409 on duplicate)."""
    return record_bill_vote(
        db=db,
        bill_id=bill_id,
        raw_identifier=payload.citizen_identifier,
        choice=payload.choice,
        source="web",
    )


@router.post("/{bill_id}/like", response_model=LikeResponse)
def like_bill(bill_id: int, db: Session = Depends(get_db)) -> LikeResponse:
    """Increment the support/like counter for a bill."""
    bill = db.get(Bill, bill_id)
    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projeto de lei não encontrado.",
        )
    bill.likes_count += 1
    db.commit()
    db.refresh(bill)
    return LikeResponse(bill_id=bill.id, likes_count=bill.likes_count)
