from typing import Optional
import uuid

from fastapi import APIRouter, status

from dependencies import SessionDep
from core.authentication import StaffUserDep
from models.category import (
    PaginatedCategories, Category,
    CategoryCreate, CategoryUpdate
)
from services.category_service import CategoryService


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=PaginatedCategories)
async def get_all_categories(
    db: SessionDep,
    current_user: StaffUserDep,
    name: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 10,
):
    return await CategoryService.get_all_categories(db, name, is_active, page, page_size)


@router.post("/", response_model=Category, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: CategoryCreate,
    db: SessionDep,
    current_user: StaffUserDep
):
    return await CategoryService.add_category(db, category, current_user)


@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: uuid.UUID, 
    db: SessionDep
):
    return await CategoryService.get_category(db, category_id)


@router.patch("/{category_id}", response_model=Category)
async def update_category(
    category_id: uuid.UUID,
    category_update: CategoryUpdate, 
    db: SessionDep, 
    current_user: StaffUserDep
):
    return await CategoryService.update_category(db, category_id, category_update, current_user)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID, 
    db: SessionDep, 
    current_user: StaffUserDep
):
    await CategoryService.delete_category(db, category_id, current_user)
    return None