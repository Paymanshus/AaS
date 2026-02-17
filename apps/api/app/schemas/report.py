from datetime import datetime

from pydantic import BaseModel, Field


class WrappedReport(BaseModel):
    who_cooked: str
    best_receipts: list[str] = Field(default_factory=list)
    most_stubborn_point: str
    unexpected_common_ground: str
    momentum_shift_turn: int | None = None
    highlights: list[str] = Field(default_factory=list)


class ArgumentReportView(BaseModel):
    argument_id: str
    summary: str
    report: WrappedReport
    created_at: datetime
