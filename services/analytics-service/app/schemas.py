from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


EventType = Literal[
    "page_view",
    "property_view",
    "schedule_visit_click",
]


class AnalyticsEvent(BaseModel):
    event_type: EventType
    page: str = Field(min_length=1, max_length=500)
    property_id: int | None = Field(default=None, gt=0)
    session_id: str = Field(min_length=1, max_length=100)
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_event(self):
        if self.occurred_at.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")

        if self.event_type == "property_view" and self.property_id is None:
            raise ValueError("property_id is required for property_view")

        return self


class AnalyticsEventResponse(BaseModel):
    event_id: UUID
    status: str
