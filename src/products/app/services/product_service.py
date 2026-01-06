from typing import Optional
import uuid,logging, math, json

from fastapi import HTTPException, status
from sqlmodel import select, func
from sqlalchemy.orm import selectinload

from core.redis_cache import get_cache, set_cache
from dependencies import SessionDep
from models.product import (
    Product, ProductCreate,
    ProductUpdate, Category,
    Brand, ProductImage,
    PaginatedProducts, ProductImageCreate,
    PaginatedProductImages, ProductImageUpdate
)
from models.outbox import Outbox
from events.schemas.product_created import ProductCreatedPayload, ProductCreatedEvent
from events.schemas.product_updated import ProductUpdatedEvent, ProductUpdatedPayload
from events.schemas.product_deleted import ProductDeletedEvent, ProductDeletedPayload
from events.schemas.base import ProductEventDTO


logger = logging.getLogger(__name__)


class ProductService:
    @staticmethod
    async def add_product(db: SessionDep, product_data: ProductCreate) -> Product:
        category = db.get(Category, product_data.category_id)
        if not category:
            logger.warning(f"Category not found: {product_data.category_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        brand = db.get(Brand, product_data.brand_id)
        if not brand:
            logger.warning(f"Brand not found: {product_data.brand_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        
        db_product = Product(**product_data.model_dump(exclude={'images'}))

        # Prepare event (use db_product before commit, as ID will be generated on add)
        payload = ProductCreatedPayload(
            product=ProductEventDTO.from_model(db_product)
        )
        event = ProductCreatedEvent.create(payload)

        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event.to_dict(), default=str),
            retry_count=0
        )

        # Atomic: Add product, images, and outbox
        try:
            db.add(db_product)
            db.add(outbox_entry)
            # Add images after product ID is available
            for image in product_data.images:
                db_image = ProductImage(
                    product_id=db_product.id, 
                    image_url=image.image_url, 
                    alt_text=image.alt_text
                )
                db.add(db_image)

            db.commit()
            db.refresh(db_product)
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to add product")

        logger.info(f"Product created: {db_product.name}")
        return db_product

    @staticmethod
    async def update_product(db: SessionDep, product_id: uuid.UUID, product_data: ProductUpdate) -> Product:
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

        payload = ProductUpdatedPayload(
            product=ProductEventDTO.from_model(db_product)
        )
        event = ProductUpdatedEvent.create(payload)
        
        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event.to_dict(), default=str),
            retry_count=0
        )

        # Atomic: Update product, handle images, add outbox
        try:
            db.add(db_product)
            db.add(outbox_entry)
            # Add images after product ID is available
            for image in product_data.images:
                db_image = ProductImage(
                    product_id=db_product.id, 
                    image_url=image.image_url, 
                    alt_text=image.alt_text
                )
                db.add(db_image)

            db.commit()
            db.refresh(db_product)
        except Exception as e:
            db.rollback()
            logger.error(f"Transaction failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to update product")

        logger.info(f"Product updated: {db_product.name}")
        return db_product

    @staticmethod
    async def delete_product(db: SessionDep, product_id: uuid.UUID) -> None:
        db_product = db.get(Product, product_id)
        if not db_product:
            logger.warning(f"Product not found: {product_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        payload = ProductDeletedPayload(
            product=ProductEventDTO.from_model(db_product)
        )
        event = ProductDeletedEvent.create(payload)

        outbox_entry = Outbox(
            topic="products",
            value=json.dumps(event.to_dict(), default=str),
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


class ProductImageService:
    @staticmethod
    async def create_image(
        db: SessionDep,
        image_data: ProductImageCreate,
        product_id: uuid.UUID,
    ) -> ProductImage:
        db_image = ProductImage(
            product_id=product_id,
            image_url=image_data.image_url,
            alt_text=image_data.alt_text,
        )

        try:
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create product image: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product image"
            )

        logger.info(f"Product image created: {db_image.id}")
        return db_image

    @staticmethod
    async def get_image(
        db: SessionDep,
        image_id: uuid.UUID
    ) -> ProductImage:
        image = db.get(ProductImage, image_id)
        if not image:
            logger.warning(f"Product image not found: {image_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product image not found"
            )
        return image

    @staticmethod
    async def get_images(
        db: SessionDep,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedProductImages:

        if page < 1 or page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pagination parameters"
            )

        total_items = db.exec(
            select(func.count()).select_from(ProductImage)
        ).one()

        total_pages = math.ceil(total_items / page_size)

        statement = (
            select(ProductImage)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .order_by(ProductImage.id)
        )

        items = db.exec(statement).all()

        return PaginatedProductImages(
            items=items,
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
        )
    
    @staticmethod
    async def update_image(
        db: SessionDep,
        image_id: uuid.UUID,
        image_data: ProductImageUpdate
    ) -> ProductImage:

        db_image = db.get(ProductImage, image_id)
        if not db_image:
            logger.warning(f"Product image not found: {image_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product image not found"
            )

        update_data = image_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_image, key, value)

        try:
            db.add(db_image)
            db.commit()
            db.refresh(db_image)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update product image: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update product image"
            )

        logger.info(f"Product image updated: {image_id}")
        return db_image

    @staticmethod
    async def delete_image(
        db: SessionDep,
        image_id: uuid.UUID
    ) -> None:
        db_image = db.get(ProductImage, image_id)
        if not db_image:
            logger.warning(f"Product image not found: {image_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product image not found"
            )

        try:
            db.delete(db_image)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete product image: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product image"
            )

        logger.info(f"Product image deleted: {image_id}")