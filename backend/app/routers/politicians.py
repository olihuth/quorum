from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.legislative import LegislativeHouse, OfficialVote, Party, Politician
from app.schemas.legislative import (
    AuthoredBillBriefOut,
    PoliticianDetailOut,
    PoliticianSummaryOut,
    PoliticianVoteRecordOut,
)

router = APIRouter(prefix="/politicians", tags=["Politicians"])


def _to_summary(pol: Politician) -> PoliticianSummaryOut:
    return PoliticianSummaryOut(
        id=pol.id,
        external_id=pol.external_id,
        name=pol.name,
        state=pol.state,
        role=pol.role,
        party_acronym=pol.party.acronym,
        party_name=pol.party.name,
        party_color_hex=pol.party.color_hex,
        house_slug=pol.house.slug,
        house_short_name=pol.house.short_name,
        legislature=pol.legislature,
        attendance_rate=pol.attendance_rate,
        biography_summary=pol.biography_summary,
        photo_url=pol.photo_url,
        official_portal_url=pol.official_portal_url,
        is_active=pol.is_active,
    )


@router.get("", response_model=list[PoliticianSummaryOut])
def list_politicians(
    house_slug: str | None = Query(default=None),
    party_acronym: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PoliticianSummaryOut]:
    """List strictly read-only politician profiles filtered by house, party, or name."""
    stmt = (
        select(Politician)
        .options(joinedload(Politician.house), joinedload(Politician.party))
        .order_by(Politician.id)
    )
    if house_slug:
        stmt = stmt.join(Politician.house).where(LegislativeHouse.slug == house_slug)
    if party_acronym:
        stmt = stmt.join(Politician.party).where(Party.acronym == party_acronym.upper())
    if search:
        stmt = stmt.where(Politician.name.ilike(f"%{search.strip()}%"))

    politicians = db.scalars(stmt).unique().all()
    return [_to_summary(pol) for pol in politicians]


@router.get("/{politician_id}", response_model=PoliticianDetailOut)
def get_politician(politician_id: int, db: Session = Depends(get_db)) -> PoliticianDetailOut:
    """Return a strictly read-only institutional profile with authored bills and voting history."""
    stmt = (
        select(Politician)
        .options(
            joinedload(Politician.house),
            joinedload(Politician.party),
            joinedload(Politician.authored_bills),
            joinedload(Politician.official_votes).joinedload(OfficialVote.bill),
        )
        .where(Politician.id == politician_id)
    )
    pol = db.scalars(stmt).unique().first()
    if not pol:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parlamentar não encontrado.",
        )

    authored = [
        AuthoredBillBriefOut(
            id=bill.id,
            number=bill.number,
            title=bill.title,
            status=bill.status,
            house_short_name=pol.house.short_name,
        )
        for bill in pol.authored_bills
    ]

    history: list[PoliticianVoteRecordOut] = []
    for ov in pol.official_votes:
        bill = ov.bill
        if not bill:
            continue
        citizen_majority = "A Favor" if bill.votes_favor >= bill.votes_against else "Contra"
        house_obj = db.get(LegislativeHouse, bill.house_id)
        history.append(
            PoliticianVoteRecordOut(
                bill_id=bill.id,
                bill_number=bill.number,
                bill_title=bill.title,
                house_short_name=house_obj.short_name if house_obj else pol.house.short_name,
                date_label=ov.date_label,
                vote_choice=ov.vote_choice,
                citizen_majority_vote=citizen_majority,
            )
        )

    summary = _to_summary(pol)
    return PoliticianDetailOut(
        **summary.model_dump(),
        authored_bills=authored,
        voting_history=history,
    )
