import uuid
from typing import Optional, List

from sqlmodel import SQLModel, Field, Relationship


class CategoryBase(SQLModel):
    name: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)


class Category(CategoryBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

    # Use string annotation for the relationship to avoid importing Product
    products: List["Product"] = Relationship(back_populates="category")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryPublic(CategoryBase):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


class BrandBase(SQLModel):
    name: str = Field(index=True, unique=True)
    is_active: bool = Field(default=True)


class Brand(BrandBase, table=True):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)

    # Use string annotation for the relationship to avoid importing Product
    products: List["Product"] = Relationship(back_populates="brand")


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BrandBase):
    pass


class BrandPublic(BrandBase):
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True)


class PaginatedCategories(SQLModel):
    items: List[CategoryPublic]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int


class PaginatedBrands(SQLModel):
    items: List[BrandPublic]
    total_items: int
    total_pages: int
    current_page: int
    page_size: int