"""Pydantic domain models for caregiver-os."""

from __future__ import annotations

from datetime import datetime, time
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now()


class CareRecipient(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    age: int | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=_now)


class Medication(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    care_recipient_id: UUID
    name: str
    dose: str
    times: list[time] = Field(default_factory=list)
    instructions: str | None = None
    refill_at_days_left: int = 7
    active: bool = True
    created_at: datetime = Field(default_factory=_now)


class Appointment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    care_recipient_id: UUID
    provider: str
    at: datetime
    location: str | None = None
    purpose: str | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=_now)


IncidentKind = Literal["fall", "confusion", "missed_meal", "medication_refusal", "other"]
IncidentSeverity = Literal["info", "warning", "alert"]


class Incident(BaseModel):
    kind: IncidentKind
    at: datetime = Field(default_factory=_now)
    description: str
    severity: IncidentSeverity = "info"


class HandoffLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    care_recipient_id: UUID
    shift_start: datetime = Field(default_factory=_now)
    shift_end: datetime | None = None
    caregiver: str
    vitals: str | None = None
    mood: str | None = None
    meals: str | None = None
    medications_given: list[UUID] = Field(default_factory=list)
    incidents: list[Incident] = Field(default_factory=list)
    notes: str | None = None


class CarePlan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    care_recipient_id: UUID
    version: int = 1
    markdown: str
    updated_at: datetime = Field(default_factory=_now)
    updated_by: str


class TodaySummary(BaseModel):
    recipient: CareRecipient
    upcoming_appointments: list[Appointment]
    medications_due: list[Medication]
    open_handoff: HandoffLog | None
    recent_incidents: list[Incident]
