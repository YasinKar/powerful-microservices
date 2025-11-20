from typing import Optional
import uuid
import logging
import math
import json

from fastapi import HTTPException, status
from sqlmodel import select, func, delete
from sqlalchemy.orm import selectinload

from core.authentication import CurrentUserDep
from core.redis_cache import get_cache, set_cache
from dependencies import SessionDep
from models.product import (
    Product, ProductCreate,
    ProductUpdate, Category,
    Brand, ProductImage,
    PaginatedProducts
)
from models.outbox import Outbox
from events.kafka_producer import publish_event


logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class ProductService:
    @staticmethod
    async def add_product(db: SessionDep, product_data: ProductCreate, current_user: CurrentUserDep) -> Product:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to add product by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        category = db.get(Category, product_data.category_id)
        if not category:
            logger.warning(f"Category not found: {product_data.category_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        brand = db.get(Brand, product_data.brand_id)
        if not brand:
            logger.warning(f"Brand not found: {product_data.brand_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        db_product = Product.model_validate(product_data)

        # Prepare event (use db_product before commit, as ID will be generated on add)
        event = {
            "event_type": "ProductCreated",
            "product": db_product.model_dump(),
        }
        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event, default=str),
            retry_count=0
        )

        # Atomic: Add product, images, and outbox
        try:
            db.add(db_product)
            db.add(outbox_entry)
            db.commit()
            db.refresh(db_product)

            # Add images after product ID is available
            for image_url in product_data.images:
                db_image = ProductImage(product_id=db_product.id, image_url=image_url)
                db.add(db_image)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to add product")

        logger.info(f"Product created: {db_product.name}")
        return db_product

    @staticmethod
    async def add_product_image(db: SessionDep, product_id: uuid.UUID, image_url: str, current_user: CurrentUserDep) -> ProductImage:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to add product image by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        product = db.get(Product, product_id)
        if not product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        db_image = ProductImage(product_id=product_id, image_url=image_url)
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        logger.info(f"Image added to product {product_id}")
        return db_image

    @staticmethod
    async def update_product(db: SessionDep, product_id: uuid.UUID, product_data: ProductUpdate, current_user: CurrentUserDep) -> Product:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to update product by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_product = db.get(Product, product_id)
        if not db_product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        if product_data.category_id:
            category = db.get(Category, product_data.category_id)
            if not category:
                logger.warning(f"Category not found: {product_data.category_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        if product_data.brand_id:
            brand = db.get(Brand, product_data.brand_id)
            if not brand:
                logger.warning(f"Brand not found: {product_data.brand_id}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")

        update_data = product_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            if key != "images":
                setattr(db_product, key, value)

        event = {
            "event_type": "ProductUpdated",
            "product": db_product.model_dump(),
        }
        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event, default=str),
            retry_count=0
        )

        # Atomic: Update product, handle images, add outbox
        try:
            if product_data.images is not None:
                # Delete old images
                db.exec(delete(ProductImage).where(ProductImage.product_id == product_id))
                # Add new images
                for image_url in product_data.images:
                    db_image = ProductImage(product_id=product_id, image_url=image_url)
                    db.add(db_image)

            db.add(db_product)
            db.add(outbox_entry)
            db.commit()
            db.refresh(db_product)
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to update product")

        logger.info(f"Product updated: {db_product.name}")
        return db_product

    @staticmethod
    async def delete_product(db: SessionDep, product_id: uuid.UUID, current_user: CurrentUserDep) -> None:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to delete product by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_product = db.get(Product, product_id)
        if not db_product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        event = {
            "event_type": "ProductDeleted",
            "product": db_product.model_dump(),
        }
        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event, default=str),
            retry_count=0
        )

        # Atomic
        try:
            db.add(outbox_entry)
            db.delete(db_product)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete product")

        logger.info(f"Product deleted: {product_id}")

    @staticmethod
    async def delete_product_image(db: SessionDep, image_id: uuid.UUID, current_user: CurrentUserDep) -> None:
        if "staff" not in current_user.permissions:
            logger.warning(f"Unauthorized attempt to delete product image by user: {current_user.username}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

        db_image = db.get(ProductImage, image_id)
        if not db_image:
            logger.warning(f"Product image not found: {image_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product image not found")

        db.delete(db_image)
        db.commit()
        logger.info(f"Product image deleted: {image_id}")

    @staticmethod
    async def get_product(db: SessionDep, product_id: uuid.UUID) -> Product:
        cache_key = f"product:{product_id}"
        cached = get_cache(cache_key)
        if cached:
            return Product(**cached)
        
        statement = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.brand),
                selectinload(Product.images)
            )
        )
        result = db.exec(statement).first()
        if not result:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        
        set_cache(cache_key, result.model_dump(), expire=300)
        return result

    @staticmethod
    async def filter_products(
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
    ) -> PaginatedProducts:
        query = select(Product)
        count_query = select(Product)

        if category_id:
            query = query.where(Product.category_id == category_id)
            count_query = count_query.where(Product.category_id == category_id)
        if brand_id:
            query = query.where(Product.brand_id == brand_id)
            count_query = count_query.where(Product.brand_id == brand_id)
        if is_active is not None:
            query = query.where(Product.is_active == is_active)
            count_query = count_query.where(Product.is_active == is_active)
        if name:
            query = query.where(Product.name.ilike(f"%{name}%"))
            count_query = count_query.where(Product.name.ilike(f"%{name}%"))
        if min_rating is not None:
            query = query.where(Product.rating >= min_rating)
            count_query = count_query.where(Product.rating >= min_rating)
        if max_rating is not None:
            query = query.where(Product.rating <= max_rating)
            count_query = count_query.where(Product.rating <= max_rating)
        if min_stock is not None:
            query = query.where(Product.stock >= min_stock)
            count_query = count_query.where(Product.stock >= min_stock)

        total_items = db.exec(select(func.count()).select_from(count_query)).one()
        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 1
        current_page = max(1, min(page, total_pages))
        skip = (current_page - 1) * page_size

        products = db.exec(query.offset(skip).limit(page_size)).all()
        logger.info(
            f"Retrieved {len(products)} products with filters: "
            f"category_id={category_id}, brand_id={brand_id}, is_active={is_active}, "
            f"name={name}, min_rating={min_rating}, max_rating={max_rating}, "
            f"min_stock={min_stock}, page={current_page}, page_size={page_size}"
        )

        return PaginatedProducts(
            items=products,
            total_items=total_items,
            total_pages=total_pages,
            current_page=current_page,
            page_size=page_size
        )
    
    @staticmethod
    def update_stock(db: SessionDep, product_id: uuid.UUID, quantity_change: int) -> Optional[Product]:
        db_product = db.get(Product, product_id)
        if not db_product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        new_stock = db_product.stock + quantity_change
        if new_stock < 0:
            logger.warning(f"Insufficient stock for product {product_id}. Current: {db_product.stock}, Change: {quantity_change}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
        

        event = {
            "correlation_id": str(product_id),
            "event_type": "ProductUpdated",
            "product": db_product.model_dump(),
        }
        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event, default=str)
        )

        # Atomic: Use SQLAlchemy transaction
        try:
            db_product.stock = new_stock
            db.add(db_product)
            db.add(outbox_entry)
            db.commit()
            db.refresh(db_product)
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise

        logger.info(f"Stock updated for product {product_id}: {db_product.stock}")
        return db_product
