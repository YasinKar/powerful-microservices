from typing import Optional
import uuid

from fastapi import APIRouter, status

from dependencies import SessionDep
from core.authentication import CurrentUserDep
from models.product import (
    PaginatedProducts, Product,
    ProductUpdate, ProductCreate
)
from services.product_service import ProductService


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=PaginatedProducts)
async def read_products(
    db: SessionDep,
    category_id: Optional[uuid.UUID] = None,
    brand_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    name: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    min_stock: Optional[int] = None,
    page: int = 1,
    page_size: int = 10
):
    return await ProductService.filter_products(
        db, category_id, brand_id, is_active, name, min_rating, max_rating, min_stock, page, page_size
    )


@router.get("/{product_id}", response_model=Product)
async def read_product(product_id: uuid.UUID, db: SessionDep):
    return await ProductService.get_product(db, product_id)


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: SessionDep, current_user: CurrentUserDep):
    return await ProductService.add_product(db, product, current_user)


@router.patch("/{product_id}", response_model=Product)
async def update_product(product_id: uuid.UUID, product_update: ProductUpdate, db: SessionDep, current_user: CurrentUserDep):
    return await ProductService.update_product(db, product_id, product_update, current_user)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: uuid.UUID, db: SessionDep, current_user: CurrentUserDep):
    await ProductService.delete_product(db, product_id, current_user)
    return None