from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.legislative import Bill, CitizenVote, LegislativeHouse
from app.schemas.legislative import (
    BillComparisonItem,
    DashboardOverviewOut,
    PartyCompositionItem,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Overview"])


@router.get("/overview", response_model=DashboardOverviewOut)
def get_dashboard_overview(
    house_slug: str = Query(default="all"),
    db: Session = Depends(get_db),
) -> DashboardOverviewOut:
    """Gold Layer analytical aggregation for the Panorama Legislativo view."""
    selected_house: LegislativeHouse | None = None
    bill_stmt = select(Bill).order_by(Bill.id)

    if house_slug != "all":
        selected_house = db.scalar(
            select(LegislativeHouse).where(LegislativeHouse.slug == house_slug)
        )
        if not selected_house:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Casa legislativa não encontrada.",
            )
        bill_stmt = bill_stmt.where(Bill.house_id == selected_house.id)
    else:
        selected_house = db.scalar(
            select(LegislativeHouse).where(LegislativeHouse.slug == "congresso-nacional")
        ) or db.scalar(select(LegislativeHouse).order_by(LegislativeHouse.id).limit(1))

    bills = db.scalars(bill_stmt).all()
    total_bills = len(bills)

    house_by_id = {
        h.id: h for h in db.scalars(select(LegislativeHouse)).all()
    }

    total_citizen_votes = 0
    approved_count = 0
    citizen_favor_rates: list[float] = []
    comparisons: list[BillComparisonItem] = []

    for bill in bills:
        bill_total = bill.votes_favor + bill.votes_against
        total_citizen_votes += bill_total
        if bill.status == "Aprovado":
            approved_count += 1
        favor_pct = round((bill.votes_favor / bill_total) * 100, 1) if bill_total > 0 else 50.0
        citizen_favor_rates.append(favor_pct)

        house_obj = house_by_id.get(bill.house_id)
        comparisons.append(
            BillComparisonItem(
                bill_id=bill.id,
                number=bill.number,
                title=bill.title,
                house_short_name=house_obj.short_name if house_obj else "Legislativo",
                status=bill.status,
                total_citizen_votes=bill_total,
                citizen_favor_percentage=favor_pct,
                official_approval_rate=bill.official_approval_rate or 70,
            )
        )

    bill_ids = [b.id for b in bills]
    web_votes = 0
    iot_votes = 0
    if bill_ids:
        web_votes = (
            db.scalar(
                select(func.count(CitizenVote.id)).where(
                    CitizenVote.bill_id.in_(bill_ids),
                    CitizenVote.source == "web",
                )
            )
            or 0
        )
        iot_votes = (
            db.scalar(
                select(func.count(CitizenVote.id)).where(
                    CitizenVote.bill_id.in_(bill_ids),
                    CitizenVote.source == "iot_totem",
                )
            )
            or 0
        )

    official_approval_rate = (
        round((approved_count / total_bills) * 100, 1) if total_bills > 0 else 0.0
    )
    avg_citizen_favor = (
        round(sum(citizen_favor_rates) / len(citizen_favor_rates), 1)
        if citizen_favor_rates
        else 0.0
    )

    seat_distribution: list[PartyCompositionItem] = []
    if selected_house:
        total_seats = max(selected_house.total_seats, 1)
        for entry in selected_house.party_composition_json or []:
            seats = int(entry.get("seat_count", 0))
            seat_distribution.append(
                PartyCompositionItem(
                    party=entry.get("party", "Outros"),
                    party_name=entry.get("party_name", entry.get("party", "Outros")),
                    seat_count=seats,
                    percentage=round((seats / total_seats) * 100, 1),
                    color_hex=entry.get("color_hex", "#64748B"),
                )
            )

    return DashboardOverviewOut(
        house_slug=house_slug,
        total_monitored_bills=total_bills,
        total_citizen_votes=total_citizen_votes,
        web_votes=web_votes,
        iot_totem_votes=iot_votes,
        official_approval_rate=official_approval_rate,
        average_citizen_favor_rate=avg_citizen_favor,
        party_seat_distribution=seat_distribution,
        bill_comparisons=comparisons,
    )
