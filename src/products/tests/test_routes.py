from models.category import Brand, Category


def seed_category_brand(session):
    category = Category(name="Electronics")
    brand = Brand(name="Acme")
    session.add(category)
    session.add(brand)
    session.commit()
    session.refresh(category)
    session.refresh(brand)
    return category, brand


def test_category_routes_crud(client):
    create = client.post("/api/v1/categories/", json={"name": "Books", "is_active": True})
    assert create.status_code == 201
    category_id = create.json()["id"]

    get_one = client.get(f"/api/v1/categories/{category_id}")
    assert get_one.status_code == 200

    list_all = client.get("/api/v1/categories/?page=1&page_size=10")
    assert list_all.status_code == 200
    assert list_all.json()["total_items"] == 1

    patch = client.patch(f"/api/v1/categories/{category_id}", json={"name": "Books 2", "is_active": False})
    assert patch.status_code == 200

    delete = client.delete(f"/api/v1/categories/{category_id}")
    assert delete.status_code == 204


def test_brand_routes_crud(client):
    create = client.post("/api/v1/brands/", json={"name": "Brand X", "is_active": True})
    assert create.status_code == 201
    brand_id = create.json()["id"]

    get_one = client.get(f"/api/v1/brands/{brand_id}")
    assert get_one.status_code == 200

    patch = client.patch(f"/api/v1/brands/{brand_id}", json={"name": "Brand Y", "is_active": False})
    assert patch.status_code == 200

    delete = client.delete(f"/api/v1/brands/{brand_id}")
    assert delete.status_code == 204


def test_product_routes_create_read_update_delete(client, session, monkeypatch):
    monkeypatch.setattr("services.product_service.get_cache", lambda key: None)
    monkeypatch.setattr("services.product_service.set_cache", lambda key, value, expire=300: None)

    category, brand = seed_category_brand(session)

    create = client.post(
        "/api/v1/products/",
        data={
            "name": "Phone",
            "price": "1000",
            "description": "Demo",
            "stock": "5",
            "category_id": str(category.id),
            "brand_id": str(brand.id),
            "is_active": "true",
            "rating": "4.5",
        },
    )
    assert create.status_code == 201, create.text
    product_id = create.json()["id"]

    get_one = client.get(f"/api/v1/products/{product_id}")
    assert get_one.status_code == 200

    list_all = client.get("/api/v1/products/?name=Pho")
    assert list_all.status_code == 200
    assert list_all.json()["total_items"] == 1

    update = client.patch(
        f"/api/v1/products/{product_id}",
        data={
            "name": "Phone 2",
            "price": "1200",
            "description": "Demo 2",
            "stock": "8",
            "category_id": str(category.id),
            "brand_id": str(brand.id),
            "is_active": "true",
            "rating": "4.7",
        },
    )
    assert update.status_code == 200

    delete = client.delete(f"/api/v1/products/{product_id}")
    assert delete.status_code == 204


def test_product_create_rejects_mismatched_alt_texts(client, session):
    category, brand = seed_category_brand(session)

    response = client.post(
        "/api/v1/products/",
        data={
            "name": "Phone",
            "price": "1000",
            "description": "Demo",
            "stock": "5",
            "category_id": str(category.id),
            "brand_id": str(brand.id),
            "is_active": "true",
            "rating": "4.5",
            "alt_texts": ["a", "b"],
        },
        files=[("images", ("p1.jpg", b"one", "image/jpeg"))],
    )

    assert response.status_code == 400
