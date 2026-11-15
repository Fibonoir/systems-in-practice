"""Explicit output shapes for clients and contract tests."""
from pydantic import BaseModel, ConfigDict


class TicketSummary(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: int
    equipment_id: str
    summary: str
    status: str
    version: int


class Ticket(TicketSummary):
    label: str
    bay: str


class SearchPage(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: list[TicketSummary]
    next_after: int | None
    source: str
    query: str
