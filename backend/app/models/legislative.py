from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Use native JSONB on PostgreSQL 16 and standard JSON on SQLite for local testing.
JSONB_VARIANT = JSON().with_variant(JSONB, "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RawLegislativeEvent(Base):
    """Bronze Layer: immutable raw ingestion payload from official government APIs."""

    __tablename__ = "raw_legislative_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_payload: Mapped[dict] = mapped_column(JSONB_VARIANT, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)


class LegislativeHouse(Base):
    """Silver Layer: normalized legislative house directory and metadata."""

    __tablename__ = "legislative_houses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False)
    state_or_city: Mapped[str] = mapped_column(String(100), nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)
    followers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_followed_by_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    official_portal_url: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    upcoming_sessions: Mapped[list] = mapped_column(JSONB_VARIANT, default=list, nullable=False)
    party_composition_json: Mapped[list] = mapped_column(JSONB_VARIANT, default=list, nullable=False)

    politicians: Mapped[list["Politician"]] = relationship(back_populates="house")
    bills: Mapped[list["Bill"]] = relationship(back_populates="house")


class Party(Base):
    """Silver Layer: registered political party metadata."""

    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    acronym: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(16), default="#1D4ED8", nullable=False)
    registration_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    foundation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    spectrum: Mapped[str] = mapped_column(String(64), default="Diversos", nullable=False)
    program_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    official_portal_url: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    politicians: Mapped[list["Politician"]] = relationship(back_populates="party")


class Politician(Base):
    """Silver Layer: strictly read-only public representative profile."""

    __tablename__ = "politicians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    house_id: Mapped[int] = mapped_column(ForeignKey("legislative_houses.id"), nullable=False, index=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    legislature: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    attendance_rate: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    biography_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    official_portal_url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    house: Mapped["LegislativeHouse"] = relationship(back_populates="politicians")
    party: Mapped["Party"] = relationship(back_populates="politicians")
    authored_bills: Mapped[list["Bill"]] = relationship(back_populates="author")
    official_votes: Mapped[list["OfficialVote"]] = relationship(back_populates="politician")


class Bill(Base):
    """Silver Layer: legislative bill with plain-language AI summary and citizen tallies."""

    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    house_id: Mapped[int] = mapped_column(ForeignKey("legislative_houses.id"), nullable=False, index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("politicians.id"), nullable=True, index=True)
    number: Mapped[str] = mapped_column(String(64), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    theme: Mapped[str] = mapped_column(String(120), default="Legislação Geral", nullable=False)
    official_summary: Mapped[str] = mapped_column(Text, nullable=False)
    desjuridiques_summary: Mapped[list] = mapped_column(JSONB_VARIANT, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="Em Tramitação", nullable=False, index=True)
    next_vote_at: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_urgent_vote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    likes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    votes_favor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    votes_against: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    official_approval_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    house: Mapped["LegislativeHouse"] = relationship(back_populates="bills")
    author: Mapped["Politician | None"] = relationship(back_populates="authored_bills")
    official_votes: Mapped[list["OfficialVote"]] = relationship(back_populates="bill")
    citizen_votes: Mapped[list["CitizenVote"]] = relationship(back_populates="bill")


class OfficialVote(Base):
    """Silver Layer: nominal official vote cast by a representative."""

    __tablename__ = "official_votes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id"), nullable=False, index=True)
    politician_id: Mapped[int] = mapped_column(ForeignKey("politicians.id"), nullable=False, index=True)
    vote_choice: Mapped[str] = mapped_column(String(32), nullable=False)
    date_label: Mapped[str] = mapped_column(String(80), default="", nullable=False)

    bill: Mapped["Bill"] = relationship(back_populates="official_votes")
    politician: Mapped["Politician"] = relationship(back_populates="official_votes")


class CitizenVote(Base):
    """Silver Layer: anonymized citizen poll vote (1 vote per citizen per bill)."""

    __tablename__ = "citizen_votes"
    __table_args__ = (UniqueConstraint("bill_id", "citizen_hash", name="uq_bill_citizen_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bill_id: Mapped[int] = mapped_column(ForeignKey("bills.id"), nullable=False, index=True)
    citizen_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    choice: Mapped[str] = mapped_column(String(16), nullable=False)
    source: Mapped[str] = mapped_column(String(32), default="web", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    bill: Mapped["Bill"] = relationship(back_populates="citizen_votes")


class User(Base):
    """Private citizen account for notification settings and followed houses (no public profile)."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    urgent_vote_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_digest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status_change_notifications: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    followed_house_slugs: Mapped[list] = mapped_column(
        JSONB_VARIANT,
        default=lambda: ["congresso-nacional", "senado-federal"],
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
