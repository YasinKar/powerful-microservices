import uuid
from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field


class UserAddress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    phone: Optional[str] = None
    is_default: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_mongo(cls, data):
        if not data:
            return None
        data["id"] = data.get("id") or str(data.get("_id"))
        data.pop("_id", None)
        return cls(**data)