from models.address import UserAddress
from models.cart import Cart, CartItem
from models.order import Order


def test_address_from_mongo_maps_id():
    obj = UserAddress.from_mongo(
        {
            "_id": "mongo1",
            "user_id": "u1",
            "street": "Main",
            "city": "NY",
            "state": "NY",
            "country": "US",
            "postal_code": "10001",
        }
    )
    assert obj.id == "mongo1"


def test_cart_calculate_total(monkeypatch):
    monkeypatch.setattr("models.cart.ProductService.get_product", lambda pid: {"price": 10})
    cart = Cart(user_id="u1", items=[CartItem(product_id="p1", quantity=2), CartItem(product_id="p2", quantity=1)])
    assert cart.calculate_total() == 30


def test_order_calculate_total(monkeypatch):
    monkeypatch.setattr("models.cart.ProductService.get_product", lambda pid: {"price": 15})
    address = UserAddress(
        user_id="u1",
        street="Main",
        city="NY",
        state="NY",
        country="US",
        postal_code="10001",
    )
    order = Order(user_id="u1", items=[CartItem(product_id="p1", quantity=2)], shipping_address=address)
    assert order.calculate_total() == 30
