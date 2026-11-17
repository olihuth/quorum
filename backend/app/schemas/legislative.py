from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PartyCompositionItem(BaseModel):
    party: str
    party_name: str
    seat_count: int
    percentage: float
    color_hex: str


class LegislativeSessionSchema(BaseModel):
    id: str
    date: str
    time: str
    title: str
    type: str
    highlighted_bills: list[str] = Field(default_factory=list)


class HouseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    short_name: str
    slug: str
    level: str
    state_or_city: str
    total_seats: int
    followers_count: int
    is_followed_by_default: bool
    official_portal_url: str
    description: str
    upcoming_sessions: list[LegislativeSessionSchema] = Field(default_factory=list)
    party_composition: list[PartyCompositionItem] = Field(default_factory=list)


class PartyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    acronym: str
    name: str
    color_hex: str
    registration_number: int | None = None
    foundation_year: int | None = None
    spectrum: str
    program_summary: str
    official_portal_url: str


class PoliticianVoteRecordOut(BaseModel):
    bill_id: int
    bill_number: str
    bill_title: str
    house_short_name: str
    date_label: str
    vote_choice: str
    citizen_majority_vote: Literal["A Favor", "Contra"]


class AuthoredBillBriefOut(BaseModel):
    id: int
    number: str
    title: str
    status: str
    house_short_name: str


class PoliticianSummaryOut(BaseModel):
    id: int
    external_id: str
    name: str
    state: str
    role: str
    party_acronym: str
    party_name: str
    party_color_hex: str
    house_slug: str
    house_short_name: str
    legislature: str
    attendance_rate: str
    biography_summary: str
    photo_url: str | None = None
    official_portal_url: str
    is_active: bool


class PoliticianDetailOut(PoliticianSummaryOut):
    authored_bills: list[AuthoredBillBriefOut] = Field(default_factory=list)
    voting_history: list[PoliticianVoteRecordOut] = Field(default_factory=list)


class BillOut(BaseModel):
    id: int
    external_id: str
    number: str
    year: int
    title: str
    theme: str
    house_slug: str
    house_short_name: str
    level: str
    author_id: int | None = None
    author_name: str | None = None
    author_party: str | None = None
    author_state: str | None = None
    official_summary: str
    desjuridiques_summary: list[str]
    status: str
    next_vote_at: str | None = None
    is_urgent_vote: bool
    likes_count: int
    votes_favor: int
    votes_against: int
    favor_percentage: float
    against_percentage: float
    official_approval_rate: int | None = None
    updated_at: datetime


class CitizenVoteRequest(BaseModel):
    citizen_identifier: str = Field(..., min_length=3, max_length=255)
    choice: Literal["favor", "against"]


class IoTVoteRequest(BaseModel):
    totem_id: str = Field(..., min_length=2, max_length=128)
    bill_id: int = Field(..., gt=0)
    choice: Literal["favor", "against"]
    session_token: str | None = Field(default=None, max_length=128)


class VoteResponse(BaseModel):
    bill_id: int
    choice: Literal["favor", "against"]
    source: str
    votes_favor: int
    votes_against: int
    total_votes: int
    favor_percentage: float
    against_percentage: float
    message: str


class LikeResponse(BaseModel):
    bill_id: int
    likes_count: int


class BillComparisonItem(BaseModel):
    bill_id: int
    number: str
    title: str
    house_short_name: str
    status: str
    total_citizen_votes: int
    citizen_favor_percentage: float
    official_approval_rate: int


class DashboardOverviewOut(BaseModel):
    house_slug: str
    total_monitored_bills: int
    total_citizen_votes: int
    web_votes: int
    iot_totem_votes: int
    official_approval_rate: float
    average_citizen_favor_rate: float
    party_seat_distribution: list[PartyCompositionItem]
    bill_comparisons: list[BillComparisonItem]


class SyncResultOut(BaseModel):
    task: str
    bronze_events_recorded: int
    records_upserted: int
    source_status: str


class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class UserUpdateRequest(BaseModel):
    email: str | None = Field(default=None, min_length=5, max_length=255)
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=6, max_length=128)
    urgent_vote_alerts: bool | None = None
    email_digest: bool | None = None
    status_change_notifications: bool | None = None
    followed_house_slugs: list[str] | None = None


class UserProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    urgent_vote_alerts: bool
    email_digest: bool
    status_change_notifications: bool
    followed_house_slugs: list[str]
    created_at: datetime


class AuthTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileOut
