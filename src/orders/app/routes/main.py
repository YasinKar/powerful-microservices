from fastapi import APIRouter

from routes import cart, address, order


api_router = APIRouter()
api_router.include_router(cart.router)
api_router.include_router(address.router)
api_router.include_router(order.router)