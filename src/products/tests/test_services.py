import asyncio
import uuid

import pytest
from fastapi import HTTPException
from sqlmodel import select

from models.category import Brand, BrandCreate, Category, CategoryCreate, CategoryUpdate
from models.outbox import Outbox
from models.product import (
    Product,
    ProductCreate,
    ProductImage,
    ProductImageCreate,
    ProductImageUpdate,
    ProductUpdate,
)
from services.category_service import CategoryService
from services.product_service import ProductImageService, ProductService


def run(coro):
    return asyncio.run(coro)


def create_category_brand(session):
    category = Category(name="Category A")
    brand = Brand(name="Brand A")
    session.add(category)
    session.add(brand)
    session.commit()
    session.refresh(category)
    session.refresh(brand)
    return category, brand


def create_product(session):
    category, brand = create_category_brand(session)
    product = Product(
        name="Phone",
        description="Demo",
        price=1000,
        stock=5,
        category_id=category.id,
        brand_id=brand.id,
        is_active=True,
        rating=4.3,
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product, category, brand


def test_add_category_success(session):
    created = run(CategoryService.add_category(session, CategoryCreate(name="Electronics", is_active=True)))
    assert created.name == "Electronics"


def test_add_category_duplicate_fails(session):
    run(CategoryService.add_category(session, CategoryCreate(name="Electronics", is_active=True)))
    with pytest.raises(HTTPException) as exc:
        run(CategoryService.add_category(session, CategoryCreate(name="Electronics", is_active=True)))
    assert exc.value.status_code == 400


def test_get_all_categories_paginated(session):
    run(CategoryService.add_category(session, CategoryCreate(name="Cat 1", is_active=True)))
    run(CategoryService.add_category(session, CategoryCreate(name="Cat 2", is_active=True)))
    paginated = run(CategoryService.get_all_categories(session, page=1, page_size=1))
    assert paginated.total_items == 2
    assert len(paginated.items) == 1


def test_update_and_delete_category(session):
    category = run(CategoryService.add_category(session, CategoryCreate(name="Old", is_active=True)))
    updated = run(CategoryService.update_category(session, category.id, CategoryUpdate(name="New", is_active=False)))
    assert updated.name == "New"
    run(CategoryService.delete_category(session, category.id))
    assert session.get(Category, category.id) is None


def test_delete_category_with_products_fails(session):
    product, category, brand = create_product(session)  # noqa: F841
    with pytest.raises(HTTPException) as exc:
        run(CategoryService.delete_category(session, category.id))
    assert exc.value.status_code == 400


def test_brand_flow(session):
    brand = run(CategoryService.add_brand(session, BrandCreate(name="Brand 1", is_active=True)))
    fetched = run(CategoryService.get_brand(session, brand.id))
    assert fetched.name == "Brand 1"
    run(CategoryService.delete_brand(session, brand.id))
    assert session.get(Brand, brand.id) is None


def test_add_product_creates_outbox_and_images(session):
    category, brand = create_category_brand(session)
    payload = ProductCreate(
        name="Tablet",
        description="Tab",
        price=2000,
        stock=3,
        category_id=category.id,
        brand_id=brand.id,
        is_active=True,
        rating=4.0,
        images=[ProductImageCreate(image_url="products/x.png", alt_text="front")],
    )

    created = run(ProductService.add_product(session, payload))

    assert created.name == "Tablet"
    assert len(session.exec(select(Outbox)).all()) == 1
    assert len(session.exec(select(ProductImage)).all()) == 1


def test_add_product_requires_valid_category_and_brand(session):
    category, brand = create_category_brand(session)
    payload = ProductCreate(
        name="Laptop",
        description="L",
        price=5000,
        stock=3,
        category_id=uuid.uuid4(),
        brand_id=brand.id,
        is_active=True,
        rating=4.0,
        images=[],
    )
    with pytest.raises(HTTPException) as exc:
        run(ProductService.add_product(session, payload))
    assert exc.value.status_code == 404

    payload = ProductCreate(
        name="Laptop",
        description="L",
        price=5000,
        stock=3,
        category_id=category.id,
        brand_id=uuid.uuid4(),
        is_active=True,
        rating=4.0,
        images=[],
    )
    with pytest.raises(HTTPException) as exc2:
        run(ProductService.add_product(session, payload))
    assert exc2.value.status_code == 404


def test_update_product_and_delete_product(session):
    product, category, brand = create_product(session)
    payload = ProductUpdate(name="Updated", price=1100, stock=6, category_id=category.id, brand_id=brand.id, images=[])
    updated = run(ProductService.update_product(session, product.id, payload))
    assert updated.name == "Updated"
    run(ProductService.delete_product(session, product.id))
    assert session.get(Product, product.id) is None


def test_get_product_uses_cache_when_hit(session, monkeypatch):
    product, category, brand = create_product(session)  # noqa: F841
    monkeypatch.setattr(
        "services.product_service.get_cache",
        lambda key: {
            "id": product.id,
            "name": "Cached Phone",
            "description": "Cached",
            "price": 1200,
            "stock": 8,
            "category_id": product.category_id,
            "brand_id": product.brand_id,
            "is_active": True,
            "rating": 4.2,
        },
    )

    result = run(ProductService.get_product(session, product.id))
    assert result.name == "Cached Phone"


def test_get_product_sets_cache_on_miss(session, monkeypatch):
    product, category, brand = create_product(session)  # noqa: F841
    cache_calls = []
    monkeypatch.setattr("services.product_service.get_cache", lambda key: None)
    monkeypatch.setattr("services.product_service.set_cache", lambda key, value, expire=300: cache_calls.append((key, value)))

    result = run(ProductService.get_product(session, product.id))

    assert result.id == product.id
    assert cache_calls


def test_filter_products_and_update_stock(session):
    product, category, brand = create_product(session)
    filtered = run(ProductService.filter_products(session, name="Pho", page=1, page_size=10))
    assert filtered.total_items == 1

    updated = ProductService.update_stock(session, product.id, -2)
    assert updated.stock == 3

    with pytest.raises(HTTPException) as exc:
        ProductService.update_stock(session, product.id, -10)
    assert exc.value.status_code == 400


def test_product_image_service_crud(session):
    product, category, brand = create_product(session)  # noqa: F841
    created = run(ProductImageService.create_image(session, ProductImageCreate(image_url="p/a.png", alt_text="a"), product.id))
    fetched = run(ProductImageService.get_image(session, created.id))
    assert fetched.id == created.id

    updated = run(ProductImageService.update_image(session, created.id, ProductImageUpdate(alt_text="new")))
    assert updated.alt_text == "new"

    paginated = run(ProductImageService.get_images(session, page=1, page_size=10))
    assert paginated.total_items == 1

    run(ProductImageService.delete_image(session, created.id))
    assert session.get(ProductImage, created.id) is None


def test_product_image_get_images_validates_pagination(session):
    with pytest.raises(HTTPException) as exc:
        run(ProductImageService.get_images(session, page=0, page_size=10))
    assert exc.value.status_code == 400
