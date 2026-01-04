from fastapi import APIRouter, status, HTTPException, Body

from services.cart_service import CartService
from models.cart import Cart
from core.authentication import CurrentUserDep


router = APIRouter(prefix="/carts", tags=["Cart"])


@router.get("/checkout", response_model=Cart, status_code=status.HTTP_200_OK)
async def get_user_cart(current_user: CurrentUserDep):
    """Get current user's cart"""
    cart = await CartService.get_cart(current_user.sub)
    if not cart:
        cart = await CartService.create_cart(current_user.sub)
    return cart


@router.post("/add-item", response_model=Cart)
async def add_item_to_cart(
    current_user: CurrentUserDep,
    product_id: str = Body(...),
    quantity: int = Body(default=1),
):
    """Add or update an item in the user's cart"""
    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    cart = await CartService.create_cart_item(
        user_id=current_user.sub,
        product_id=product_id,
        quantity=quantity,
    )
    
    return cart


@router.post("/remove-item", response_model=Cart)
async def remove_item_from_cart(
    current_user: CurrentUserDep,
    item_id: str = Body(..., embed=True)
):
    """Remove an item from the user's cart"""
    cart = await CartService.delete_cart_item(current_user.sub, item_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found or empty")
    return cart


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(current_user: CurrentUserDep):
    """Delete entire cart"""
    success = await CartService.delete_cart(current_user.sub)
    if not success:
        raise HTTPException(status_code=404, detail="Cart not found")
    return {"message": "Cart deleted successfully"}