from typing import Optional, List
import uuid
import logging

from fastapi import (
    APIRouter, status,
    HTTPException, Form,
    UploadFile, File
)

from dependencies import SessionDep
from core.authentication import StaffUserDep
from models.product import (
    PaginatedProducts, Product,
    ProductUpdate, ProductCreate,
    ProductImageCreate, ProductImageUpdate
)
from services.product_service import ProductService
from core.config import settings
from utils.upload import save_upload_file


router = APIRouter(prefix="/products", tags=["Products"])


logger = logging.getLogger(__name__)


### Product ###

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
async def create_product(
    db: SessionDep,
    current_user: StaffUserDep,
    name: str = Form(...),
    price: int = Form(...),
    description: Optional[str] = Form(None),
    stock: int = Form(0),
    category_id: uuid.UUID = Form(...),
    brand_id: uuid.UUID = Form(...),
    is_active: bool = Form(True),
    rating: Optional[float] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    alt_texts: Optional[List[str]] = Form(None)
):
    if alt_texts and images and len(alt_texts) != len(images):
        raise HTTPException(status_code=400, detail="Number of alt_texts must match number of images")
    
    uploaded_images = []
    if images:
        for i, file in enumerate(images):
            relative_path, _ = await save_upload_file(file, subdir="products")
            image_url = f"{settings.MEDIA_ROOT}/{relative_path}"
            alt_text = alt_texts[i] if alt_texts else None
            uploaded_images.append(ProductImageCreate(image_url=image_url, alt_text=alt_text))

    product_data = ProductCreate(
        name=name,
        price=price,
        description=description,
        stock=stock,
        category_id=category_id,
        brand_id=brand_id,
        is_active=is_active,
        rating=rating,
        images=uploaded_images
    )

    return await ProductService.add_product(db, product_data)


@router.patch("/{product_id}", response_model=Product)
async def update_product(
    db: SessionDep,
    current_user: StaffUserDep,
    product_id: uuid.UUID,
    name: str = Form(...),
    price: int = Form(...),
    description: Optional[str] = Form(None),
    stock: int = Form(0),
    category_id: uuid.UUID = Form(...),
    brand_id: uuid.UUID = Form(...),
    is_active: bool = Form(True),
    rating: Optional[float] = Form(None),
    images: Optional[List[UploadFile]] = File(None),
    alt_texts: Optional[List[str]] = Form(None)
):
    if alt_texts and images and len(alt_texts) != len(images):
        raise HTTPException(status_code=400, detail="Number of alt_texts must match number of images")
    
    uploaded_images = []
    if images:
        for i, file in enumerate(images):
            relative_path, _ = await save_upload_file(file, subdir="products")
            image_url = f"{settings.MEDIA_ROOT}/{relative_path}"
            alt_text = alt_texts[i] if alt_texts else None
            uploaded_images.append(ProductImageUpdate(image_url=image_url, alt_text=alt_text))

    product_update = ProductUpdate(
        name=name,
        price=price,
        description=description,
        stock=stock,
        category_id=category_id,
        brand_id=brand_id,
        is_active=is_active,
        rating=rating,
        images=uploaded_images
    )

    return await ProductService.update_product(db, product_id, product_update)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    db: SessionDep,
    current_user: StaffUserDep
):
    await ProductService.delete_product(db, product_id)
    return None


### ProductImage ###

