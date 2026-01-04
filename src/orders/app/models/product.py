import uuid
from typing import Optional, List
from pydantic import BaseModel, PositiveInt, NonNegativeFloat, Field


class ProductBase(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: Optional[str] = None
    stock: PositiveInt = 0
    category_id: uuid.UUID
    brand_id: uuid.UUID
    is_active: bool = True
    rating: Optional[NonNegativeFloat] = None
    images: List[str] = []


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    stock: Optional[PositiveInt]
    category_id: Optional[uuid.UUID]
    brand_id: Optional[uuid.UUID]
    is_active: Optional[bool]
    rating: Optional[NonNegativeFloat]
    images: Optional[List[str]]
