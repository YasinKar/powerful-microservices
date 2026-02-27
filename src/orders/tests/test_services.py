import asyncio
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from models.address import UserAddress
from models.cart import Cart
from services.address_service import AddressService
from services.cart_service import CartService
from services.order_service import OrderService
from services.product_service import ProductService


def run(coro):
    return asyncio.run(coro)


def seed_product():
    ProductService.create_product({"id": "p1", "name": "Phone", "price": 100, "stock": 5})


def seed_address(user_id="user-1"):
    address = UserAddress(
        user_id=user_id,
        street="Main",
        city="NY",
        state="NY",
        country="US",
        postal_code="10001",
    )
    return run(AddressService.create_address(address))


def seed_cart(user_id="user-1"):
    seed_product()
    return run(CartService.create_cart_item(user_id=user_id, product_id="p1", quantity=1))


def test_product_service_crud():
    ProductService.create_product({"id": "p1", "name": "Phone", "price": 100, "stock": 5})
    ProductService.create_product({"id": "p1", "name": "Phone", "price": 100, "stock": 5})
    assert ProductService.get_product("p1")["name"] == "Phone"

    ProductService.update_product({"id": "p1", "name": "Phone 2"})
    assert ProductService.get_product("p1")["name"] == "Phone 2"

    ProductService.delete_product({"id": "p1"})
    assert ProductService.get_product("p1") is None


def test_address_service_flow():
    created = seed_address()
    addresses = run(AddressService.get_user_addresses("user-1"))
    assert len(addresses) == 1

    fetched = run(AddressService.get_user_address(created.id, "user-1"))
    assert fetched is not None

    updated = run(AddressService.update_address(created.id, "user-1", {"city": "Boston"}))
    assert updated.city == "Boston"

    assert run(AddressService.delete_address(created.id, "user-1")) is True


def test_cart_service_flow():
    seed_product()
    cart = run(CartService.create_cart("user-1"))
    assert cart.user_id == "user-1"

    updated = run(CartService.create_cart_item("user-1", "p1", 2))
    assert len(updated.items) == 1
    assert updated.total_price == 200

    item_id = updated.items[0].id
    updated = run(CartService.delete_cart_item("user-1", item_id))
    assert updated.items == []

    assert run(CartService.delete_cart("user-1")) is True


def test_cart_service_rejects_missing_product():
    with pytest.raises(HTTPException) as exc:
        run(CartService.create_cart_item("user-1", "missing", 1))
    assert exc.value.status_code == 404


def test_order_service_create_and_list():
    seed_address()
    cart = seed_cart()

    order = run(OrderService.create_order("user-1", cart, cart.user_id and run(AddressService.get_user_addresses("user-1"))[0].id))
    assert order.user_id == "user-1"
    assert order.status == "pending"

    orders = run(OrderService.get_orders("user-1"))
    assert len(orders) == 1


def test_order_service_create_rejects_empty_cart():
    seed_address()
    with pytest.raises(HTTPException) as exc:
        run(OrderService.create_order("user-1", Cart(user_id="user-1", items=[]), "missing"))
    assert exc.value.status_code == 400


def test_order_mark_paid_and_cancel():
    address = seed_address()
    cart = seed_cart()
    order = run(OrderService.create_order("user-1", cart, address.id))

    paid = run(OrderService.mark_order_paid("user-1", order.id))
    assert paid.status == "paid"

    cancelled = run(OrderService.cancel_order("user-1", order.id))
    assert cancelled is True


def test_order_mark_paid_invalid_status():
    address = seed_address()
    cart = seed_cart()
    order = run(OrderService.create_order("user-1", cart, address.id))
    run(OrderService.mark_order_paid("user-1", order.id))
    with pytest.raises(HTTPException) as exc:
        run(OrderService.mark_order_paid("user-1", order.id))
    assert exc.value.status_code == 400
