import uuid
import logging
import math
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy.sql import func

from core.authentication import CurrentUserDep
from dependencies import SessionDep
from models.category import (
    Category, CategoryCreate,
    CategoryUpdate, Brand,
    BrandCreate, BrandUpdate,
    PaginatedCategories, PaginatedBrands,
    CategoryPublic, BrandPublic
)
from models.product import Product


logger = logging.getLogger(__name__)


class CategoryService:
    @staticmethod
    async def add_category(
        db: SessionDep,
        category_data: CategoryCreate,
        current_user: CurrentUserDep
    ) -> Category:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to add category by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        existing_category = db.exec(select(Category).where(Category.name == category_data.name)).first()
        if existing_category:
            logger.warning(f"Category already exists: {category_data.name}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")

        db_category = Category.model_validate(category_data)
        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        logger.info(f"Category created: {db_category.name}")
        return db_category

    @staticmethod
    async def get_category(
        db: SessionDep,
        category_id: uuid.UUID,
        current_user: CurrentUserDep
    ) -> CategoryPublic:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to add category by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
        
        category = db.get(Category, category_id)
        if not category:
            logger.warning(f"Category not found: {category_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    @staticmethod
    async def get_all_categories(
        db: SessionDep,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedCategories:
        query = select(Category)
        count_query = select(Category)

        if name:
            query = query.where(Category.name.ilike(f"%{name}%"))
            count_query = count_query.where(Category.name.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
            count_query = count_query.where(Category.is_active == is_active)

        total_items = db.exec(select(func.count()).select_from(count_query)).one()
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        current_page = max(1, min(page, total_pages))
        skip = (current_page - 1) * page_size

        categories = db.exec(query.offset(skip).limit(page_size)).all()
        logger.info(
            f"Retrieved {len(categories)} categories with filters: "
            f"name={name}, is_active={is_active}, page={current_page}, page_size={page_size}"
        )

        return PaginatedCategories(
            items=categories,
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            page_size=page_size
        )

    @staticmethod
    async def update_category(db: SessionDep, category_id: uuid.UUID, category_data: CategoryUpdate, current_user: CurrentUserDep) -> Category:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to update category by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_category = db.get(Category, category_id)
        if not db_category:
            logger.warning(f"Category not found: {category_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        if category_data.name and category_data.name != db_category.name:
            existing_category = db.exec(select(Category).where(Category.name == category_data.name)).first()
            if existing_category:
                logger.warning(f"Category name already exists: {category_data.name}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category name already exists")

        update_data = category_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_category, key, value)

        db.add(db_category)
        db.commit()
        db.refresh(db_category)
        logger.info(f"Category updated: {db_category.name}")
        return db_category

    @staticmethod
    async def delete_category(db: SessionDep, category_id: uuid.UUID, current_user: CurrentUserDep) -> None:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to delete category by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_category = db.get(Category, category_id)
        if not db_category:
            logger.warning(f"Category not found: {category_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        products = db.exec(select(Product).where(Product.category_id == category_id)).all()
        if products:
            logger.warning(f"Category {category_id} has associated products")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category has associated products")

        db.delete(db_category)
        db.commit()
        logger.info(f"Category deleted: {category_id}")

    @staticmethod
    async def add_brand(db: SessionDep, brand_data: BrandCreate, current_user: CurrentUserDep) -> Brand:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to add brand by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        existing_brand = db.exec(select(Brand).where(Brand.name == brand_data.name)).first()
        if existing_brand:
            logger.warning(f"Brand already exists: {brand_data.name}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand name already exists")

        db_brand = Brand.model_validate(brand_data)
        db.add(db_brand)
        db.commit()
        db.refresh(db_brand)
        logger.info(f"Brand created: {db_brand.name}")
        return db_brand

    @staticmethod
    async def get_brand(db: SessionDep, brand_id: uuid.UUID) -> BrandPublic:
        brand = db.get(Brand, brand_id)
        if not brand:
            logger.warning(f"Brand not found: {brand_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return brand

    @staticmethod
    async def get_all_brands(
        db: SessionDep,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> PaginatedBrands:
        query = select(Brand)
        count_query = select(Brand)

        if name:
            query = query.where(Brand.name.ilike(f"%{name}%"))
            count_query = count_query.where(Brand.name.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.where(Brand.is_active == is_active)
            count_query = count_query.where(Brand.is_active == is_active)

        total_items = db.exec(select(func.count()).select_from(count_query)).one()
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        current_page = max(1, min(page, total_pages))
        skip = (current_page - 1) * page_size

        brands = db.exec(query.offset(skip).limit(page_size)).all()
        logger.info(
            f"Retrieved {len(brands)} brands with filters: "
            f"name={name}, is_active={is_active}, page={current_page}, page_size={page_size}"
        )

        return PaginatedBrands(
            items=brands,
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            page_size=page_size
        )

    @staticmethod
    async def update_brand(db: SessionDep, brand_id: uuid.UUID, brand_data: BrandUpdate, current_user: CurrentUserDep) -> Brand:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to update brand by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_brand = db.get(Brand, brand_id)
        if not db_brand:
            logger.warning(f"Brand not found: {brand_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        if brand_data.name and brand_data.name != db_brand.name:
            existing_brand = db.exec(select(Brand).where(Brand.name == brand_data.name)).first()
            if existing_brand:
                logger.warning(f"Brand name already exists: {brand_data.name}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand name already exists")

        update_data = brand_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_brand, key, value)

        db.add(db_brand)
        db.commit()
        db.refresh(db_brand)
        logger.info(f"Brand updated: {db_brand.name}")
        return db_brand

    @staticmethod
    async def delete_brand(db: SessionDep, brand_id: uuid.UUID, current_user: CurrentUserDep) -> None:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to delete brand by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_brand = db.get(Brand, brand_id)
        if not db_brand:
            logger.warning(f"Brand not found: {brand_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        products = db.exec(select(Product).where(Product.brand_id == brand_id)).all()
        if products:
            logger.warning(f"Brand {brand_id} has associated products")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Brand has associated products")

        db.delete(db_brand)
        db.commit()
        logger.info(f"Brand deleted: {brand_id}")