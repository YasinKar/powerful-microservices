import uuid
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship
from pydantic import PositiveInt, NonNegativeFloat

from .category import Category, Brand


class ProductImage(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="product.id")
    image_url: str
    alt_text: Optional[str] = None

    # Use string annotation for the relationship
    product: "Product" = Relationship(back_populates="images")


class Product(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    price: int
    stock: PositiveInt = Field(default=0)
    category_id: uuid.UUID = Field(foreign_key="category.id")
    brand_id: uuid.UUID = Field(foreign_key="brand.id")
    is_active: bool = Field(default=True)
    rating: Optional[NonNegativeFloat] = Field(default=None, ge=0.0, le=5.0)

    # Relationships (these are fine as they use direct imports)
    category: Category = Relationship(back_populates="products")
    brand: Brand = Relationship(back_populates="products")
    images: List[ProductImage] = Relationship(back_populates="product")


class ProductCreate(SQLModel):
    name: str
    price: int
    description: Optional[str] = None
    stock: PositiveInt = 0
    category_id: uuid.UUID
    brand_id: uuid.UUID
    is_active: bool = True
    rating: Optional[NonNegativeFloat] = None
    images: List[str] = []


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[PositiveInt] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    rating: Optional[NonNegativeFloat] = None
    images: Optional[List[str]] = None


class PaginatedProducts(SQLModel):
    items: List[Product]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int