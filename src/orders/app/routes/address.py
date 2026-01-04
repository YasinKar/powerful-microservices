import uuid

from fastapi import APIRouter, status, HTTPException

from services.address_service import AddressService
from models.address import UserAddress
from core.authentication import CurrentUserDep


router = APIRouter(prefix="/addresses", tags=["Address"])


@router.get("/", response_model=list[UserAddress], status_code=status.HTTP_200_OK)
async def get_user_addresses(current_user: CurrentUserDep):
    """Get all addresses for the current user"""
    addresses = await AddressService.get_user_addresses(current_user.sub)
    return addresses


@router.get("/{address_id}", response_model=UserAddress)
async def get_user_address(address_id: uuid.UUID, current_user: CurrentUserDep):
    """Get a single address"""
    address = await AddressService.get_user_address(str(address_id), current_user.sub)
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    return address


@router.post("/", response_model=UserAddress, status_code=status.HTTP_201_CREATED)
async def create_address(address: UserAddress, current_user: CurrentUserDep):
    """Create a new address"""
    address.user_id = current_user.sub
    new_address = await AddressService.create_address(address)
    return new_address


@router.patch("/{address_id}", response_model=UserAddress)
async def update_address(address_id: uuid.UUID, address_update: UserAddress, current_user: CurrentUserDep):
    """Update an existing address"""
    updated = await AddressService.update_address(str(address_id), current_user.sub, address_update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Address not found or not owned by user")
    return updated


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(address_id: uuid.UUID, current_user: CurrentUserDep):
    """Delete an address"""
    success = await AddressService.delete_address(str(address_id), current_user.sub)
    if not success:
        raise HTTPException(status_code=404, detail="Address not found or not owned by user")
    return {"message": "Address deleted successfully"}