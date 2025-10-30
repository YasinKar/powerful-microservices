from pydantic import BaseModel
from typing import Optional


class UserAddress(BaseModel):
    street: str
    city: str
    state: str
    country: str
    postal_code: str
    phone: Optional[str] = None