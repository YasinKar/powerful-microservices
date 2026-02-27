from services.product_service import ProductService


def seed_product():
    ProductService.create_product({"id": "p1", "name": "Phone", "price": 100, "stock": 10})


def create_address(client):
    response = client.post(
        "/api/v1/addresses/",
        json={
            "street": "Main",
            "city": "NY",
            "state": "NY",
            "country": "US",
            "postal_code": "10001",
            "phone": "123",
            "is_default": True,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_address_routes(client):
    address_id = create_address(client)

    list_resp = client.get("/api/v1/addresses/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/v1/addresses/{address_id}")
    assert get_resp.status_code == 200

    patch_resp = client.patch(
        f"/api/v1/addresses/{address_id}",
        json={
            "street": "Main",
            "city": "Boston",
            "state": "MA",
            "country": "US",
            "postal_code": "10001",
            "phone": "123",
            "is_default": False,
        },
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["city"] == "Boston"

    delete_resp = client.delete(f"/api/v1/addresses/{address_id}")
    assert delete_resp.status_code == 204


def test_cart_routes(client):
    seed_product()
    checkout = client.get("/api/v1/carts/checkout")
    assert checkout.status_code == 200

    add_item = client.post("/api/v1/carts/add-item", json={"product_id": "p1", "quantity": 2})
    assert add_item.status_code == 200
    item_id = add_item.json()["items"][0]["id"]

    remove_item = client.post("/api/v1/carts/remove-item", json={"item_id": item_id})
    assert remove_item.status_code == 200

    clear = client.delete("/api/v1/carts/")
    assert clear.status_code == 204


def test_order_routes_flow(client):
    seed_product()
    address_id = create_address(client)
    client.post("/api/v1/carts/add-item", json={"product_id": "p1", "quantity": 1})

    create = client.post("/api/v1/orders/create", json={"address_id": address_id})
    assert create.status_code == 201, create.text
    order_id = create.json()["id"]

    orders = client.get("/api/v1/orders/")
    assert orders.status_code == 200
    assert len(orders.json()) == 1

    get_order = client.get(f"/api/v1/orders/{order_id}")
    assert get_order.status_code == 200

    pay = client.post(f"/api/v1/orders/pay/{order_id}")
    assert pay.status_code == 200

    cancel = client.post(f"/api/v1/orders/cancel/{order_id}")
    assert cancel.status_code == 200
