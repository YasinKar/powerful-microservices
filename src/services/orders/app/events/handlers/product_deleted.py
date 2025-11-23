import logging
from services.product_service import ProductService

logger = logging.getLogger(__name__)

def handle_product_deleted(data):
    product = data.get("product")
    ProductService.delete_product(product)
    logger.info(f"Product deleted sync: {product.get('id')}")
