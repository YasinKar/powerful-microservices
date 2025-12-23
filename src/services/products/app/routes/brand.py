from typing import Optional
import uuid

from fastapi import APIRouter, status

from dependencies import SessionDep
from models.category import (
    Brand, PaginatedBrands,
    BrandUpdate, BrandCreate
)
from services.category_service import CategoryService


router = APIRouter(prefix="/brands", tags=["Brands"])


@router.get("/", response_model=PaginatedBrands)
async def get_all_brands(
    db: SessionDep,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 10
):
    return await CategoryService.get_all_brands(db, name, is_active, page, page_size)


@router.post("/", response_model=Brand, status_code=status.HTTP_201_CREATED)
async def create_brand(brand: BrandCreate, db: SessionDep):
    return await CategoryService.add_brand(db, brand)


@router.get("/{brand_id}", response_model=Brand)
async def get_brand(brand_id: uuid.UUID, db: SessionDep):
    return await CategoryService.get_brand(db, brand_id)


@router.patch("/{brand_id}", response_model=Brand)
async def update_brand(brand_id: uuid.UUID, brand_update: BrandUpdate, db: SessionDep ):
    return await CategoryService.update_brand(db, brand_id, brand_update)


@router.delete("/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(brand_id: uuid.UUID, db: SessionDep):
    await CategoryService.delete_brand(db, brand_id)
    return None