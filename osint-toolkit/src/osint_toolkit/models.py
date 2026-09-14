from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, field_validator

EntityType = Literal["dns", "http_header", "tls_cert", "robots", "ip", "asn", "identity", "evidence"]
Status = Literal["ok", "error", "skipped"]


class Observation(BaseModel):
    source: str = Field(min_length=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target: str = Field(min_length=1)
    entity_type: EntityType
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_url: str | None = None
    hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    status: Status = "ok"

    model_config = {"extra": "forbid"}

    @field_validator("timestamp")
    @classmethod
    def timestamp_is_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must include timezone")
        return value
