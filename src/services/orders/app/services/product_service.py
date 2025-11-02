import logging
from typing import Dict, Any

from core.mongodb import db

logger = logging.getLogger(__name__)


class ProductService:
    collection = db["products"]

    @staticmethod
    def create_product(product_data: Dict[str, Any]):
        try:
            product_id = product_data.get("id")
            if not product_id:
                logger.warning("Product missing ID; skipping insert.")
                return

            existing = ProductService.collection.find_one({"id": product_id})
            if existing:
                logger.info(f"Product {product_id} already exists, skipping insert.")
                return

            ProductService.collection.insert_one(product_data)
            logger.info(f"Product {product_id} created in order service DB.")
        except Exception as e:
            logger.error(f"Failed to create product: {e}")

    @staticmethod
    def update_product(product_data: Dict[str, Any]):
        try:
            product_id = product_data.get("id")
            if not product_id:
                logger.warning("Product missing ID; cannot update.")
                return

            result = ProductService.collection.update_one(
                {"id": product_id},
                {"$set": product_data},
                upsert=True
            )

            if result.modified_count > 0:
                logger.info(f"Product {product_id} updated successfully.")
            else:
                logger.info(f"Product {product_id} was already up-to-date.")
        except Exception as e:
            logger.error(f"Failed to update product: {e}")

    @staticmethod
    def delete_product(product_data: Dict[str, Any]):
        try:
            product_id = product_data.get("id")
            if not product_id:
                logger.warning("Product missing ID; cannot delete.")
                return

            result = ProductService.collection.delete_one({"id": product_id})
            if result.deleted_count > 0:
                logger.info(f"Product {product_id} deleted from MongoDB.")
            else:
                logger.info(f"Product {product_id} not found in MongoDB.")
        except Exception as e:
            logger.error(f"Failed to delete product: {e}")