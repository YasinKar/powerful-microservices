import logging
from services.product_service import ProductService

logger = logging.getLogger(__name__)

def handle_product_created(data):
    product = data.get("data").get("product")
    ProductService.create_product(product)
    logger.info(f"Product created: {product.get('id')}")