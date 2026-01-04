import logging
from datetime import datetime, timezone
from typing import List, Optional

from core.mongodb import db
from models.address import UserAddress


logger = logging.getLogger(__name__)


class AddressService:
    collection = db["addresses"]

    @staticmethod
    async def get_user_addresses(user_id: str) -> List[UserAddress]:
        """Get all addresses for a specific user"""
        addresses = list(AddressService.collection.find({"user_id": user_id}))
        return [UserAddress.from_mongo(addr) for addr in addresses]

    @staticmethod
    async def get_user_address(address_id: str, user_id: Optional[str] = None) -> Optional[UserAddress]:
        """Get one address by ID (optionally check owner)"""
        query = {"id": address_id}
        if user_id:
            query["user_id"] = user_id
        address = AddressService.collection.find_one(query)
        return UserAddress.from_mongo(address) if address else None

    @staticmethod
    async def create_address(address: UserAddress) -> UserAddress:
        """Create new address"""
        address.created_at = datetime.now(timezone.utc)
        address.updated_at = datetime.now(timezone.utc)

        AddressService.collection.insert_one(address.model_dump())
        return address

    @staticmethod
    async def update_address(address_id: str, user_id: str, update_data: dict) -> Optional[UserAddress]:
        """Update existing address"""
        update_data["updated_at"] = datetime.now(timezone.utc)
        result = AddressService.collection.update_one(
            {"id": address_id, "user_id": user_id},
            {"$set": update_data},
        )

        if result.matched_count == 0:
            return None

        updated = AddressService.collection.find_one({"id": address_id, "user_id": user_id})
        return UserAddress.from_mongo(updated)

    @staticmethod
    async def delete_address(address_id: str, user_id: str) -> bool:
        """Delete user's address"""
        result = AddressService.collection.delete_one({"id": address_id, "user_id": user_id})
        return result.deleted_count > 0
