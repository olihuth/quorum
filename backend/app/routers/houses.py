from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.legislative import LegislativeHouse
from app.schemas.legislative import HouseOut, PartyCompositionItem

router = APIRouter(prefix="/houses", tags=["Legislative Houses"])


def _build_house_out(house: LegislativeHouse) -> HouseOut:
    """Transform Silver house row into Gold-layer house output with seat percentages."""
    total_seats = max(house.total_seats, 1)
    composition: list[PartyCompositionItem] = []
    for entry in house.party_composition_json or []:
        seat_count = int(entry.get("seat_count", 0))
        composition.append(
            PartyCompositionItem(
                party=entry.get("party", "Outros"),
                party_name=entry.get("party_name", entry.get("party", "Outros")),
                seat_count=seat_count,
                percentage=round((seat_count / total_seats) * 100, 1),
                color_hex=entry.get("color_hex", "#64748B"),
            )
        )

    return HouseOut(
        id=house.id,
        name=house.name,
        short_name=house.short_name,
        slug=house.slug,
        level=house.level,
        state_or_city=house.state_or_city,
        total_seats=house.total_seats,
        followers_count=house.followers_count,
        is_followed_by_default=house.is_followed_by_default,
        official_portal_url=house.official_portal_url,
        description=house.description,
        upcoming_sessions=house.upcoming_sessions or [],
        party_composition=composition,
    )


@router.get("", response_model=list[HouseOut])
def list_houses(db: Session = Depends(get_db)) -> list[HouseOut]:
    """List all monitored legislative houses with Gold-layer party seat composition."""
    houses = db.scalars(select(LegislativeHouse).order_by(LegislativeHouse.id)).all()
    return [_build_house_out(h) for h in houses]


@router.get("/{slug}", response_model=HouseOut)
def get_house_by_slug(slug: str, db: Session = Depends(get_db)) -> HouseOut:
    """Return details, upcoming sessions, and party seat composition for one house."""
    house = db.scalar(select(LegislativeHouse).where(LegislativeHouse.slug == slug))
    if not house:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Casa legislativa não encontrada.",
        )
    return _build_house_out(house)
