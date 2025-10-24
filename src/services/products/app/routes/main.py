from fastapi import APIRouter

from routes import product, category, brand


api_router = APIRouter()

api_router.include_router(product.router)
api_router.include_router(category.router)
api_router.include_router(brand.router)