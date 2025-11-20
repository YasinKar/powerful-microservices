import uuid 
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field


class Outbox(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    topic: str = Field(index=True)
    value: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending/sent/failed/dead
    retry_count: int = Field(default=0)
    last_attempt_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None