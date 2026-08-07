from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class OpeningHoursInput(BaseModel):
    schedule: dict[str, list[dict[str, str]]] = Field(default_factory=dict)


class CreateSuccursaleInput(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    address_line: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=80)
    country: str = Field(min_length=2, max_length=2)
    default_currency: str = Field(min_length=3, max_length=3)
    default_locale: str = Field(min_length=2, max_length=10)
    phone_number: str | None = None
    opening_hours: dict[str, list[dict[str, str]]] = Field(default_factory=dict)


class UpdateSuccursaleInput(BaseModel):
    name: str | None = None
    address_line: str | None = None
    city: str | None = None
    phone_number: str | None = None
    opening_hours: dict[str, list[dict[str, str]]] | None = None


class SuccursaleSummary(BaseModel):
    id: UUID
    name: str
    address_line: str
    city: str
    country: str
    default_currency: str
    default_locale: str
    status: str
    phone_number: str | None
    opening_hours: dict[str, list[dict[str, str]]]
    created_at: datetime | None


class AssignStaffInput(BaseModel):
    user_id: UUID
    role_code: str


class RemoveStaffInput(BaseModel):
    user_id: UUID
    role_code: str


class StaffMember(BaseModel):
    user_id: UUID
    email: str | None
    phone_number: str | None
    role_codes: list[str]
