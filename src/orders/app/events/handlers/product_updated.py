import logging
from services.product_service import ProductService

logger = logging.getLogger(__name__)

def handle_product_updated(data):
    product = data.get("data").get("product")
    ProductService.update_product(product)
    logger.info(f"Product updated sync: {product.get('id')}")