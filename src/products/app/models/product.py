import uuid
from typing import Optional, List

from fastapi import Form, File, UploadFile

from sqlmodel import SQLModel, Field, Relationship
from pydantic import (
    PositiveInt, NonNegativeFloat,
    field_validator, ValidationInfo
)

from .category import Category, Brand


### ProductImage ###


class ProductImage(SQLModel, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)
    product_id: uuid.UUID = Field(foreign_key="product.id")
    image_url: str
    alt_text: Optional[str] = None

    # Use string annotation for the relationship
    product: "Product" = Relationship(back_populates="images")


class ProductImageCreate(SQLModel):
    image_url: str
    alt_text: Optional[str] = None


class ProductImageUpdate(SQLModel):
    image_url: Optional[str] = None
    alt_text: Optional[str] = None


class PaginatedProductImages(SQLModel):
    items: List[ProductImage]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


### Product ###


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


# class ProductCreateInput(SQLModel):
#     name: str = Form()
#     price: int = Form()
#     description: Optional[str] = Form(None)
#     stock: PositiveInt = Form(0)
#     category_id: uuid.UUID = Form()
#     brand_id: uuid.UUID = Form()
#     is_active: bool = Form(True)
#     rating: Optional[NonNegativeFloat] = Form(None)

#     images: List[UploadFile] = File(None) 
#     alt_texts: List[Optional[str]] = Form(None)

#     @field_validator("alt_texts")
#     @classmethod
#     def validate_alt_texts(cls, alt_texts, info: ValidationInfo):
#         images = info.data.get("images")
#         if alt_texts and images and len(alt_texts) != len(images):
#             raise ValueError("Number of alt_texts must match number of images")
#         return alt_texts
    

class ProductCreate(SQLModel):
    name: str
    price: int
    description: Optional[str] = None
    stock: PositiveInt = 0
    category_id: uuid.UUID
    brand_id: uuid.UUID
    is_active: bool = True
    rating: Optional[NonNegativeFloat] = None
    images: List[ProductImageCreate] = []


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    stock: Optional[PositiveInt] = None
    category_id: Optional[uuid.UUID] = None
    brand_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None
    rating: Optional[NonNegativeFloat] = None
    images: List[ProductImageUpdate] = []


class PaginatedProducts(SQLModel):
    items: List[Product]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int