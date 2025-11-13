import uuid
from typing import Optional

from fastapi import APIRouter, status, HTTPException, Query, Body

from core.authentication import CurrentUserDep
from services.order_service import OrderService
from services.cart_service import CartService
from models.order import Order


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=list[Order], status_code=status.HTTP_200_OK)
async def get_user_orders(
    current_user: CurrentUserDep,
    status_filter: Optional[str] = Query(None, alias="status")
):
    orders = await OrderService.get_orders(current_user.sub, status_filter)
    return orders


@router.get("/{order_id}", response_model=Order)
async def get_user_order(order_id: uuid.UUID, current_user: CurrentUserDep):
    order = await OrderService.get_order(current_user.sub, str(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/create", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(current_user: CurrentUserDep, address_id: str = Body(..., embed=True)):
    current_order = await OrderService.get_user_current_order(current_user.sub)
    if current_order:
        return current_order
    
    user_cart = await CartService.get_cart(current_user.sub)
    if not user_cart or not user_cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    try:
        order = await OrderService.create_order(current_user.sub, user_cart, address_id)
        return order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Order creation failed: {str(e)}")


@router.post("/cancel/{order_id}", status_code=status.HTTP_200_OK)
async def cancel_order(order_id: uuid.UUID, current_user: CurrentUserDep):
    success = await OrderService.cancel_order(current_user.sub, str(order_id))
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel this order")
    return {"detail": "Order canceled successfully"}


@router.post("/pay/{order_id}", status_code=status.HTTP_200_OK, response_model=dict)
async def pay_order(order_id: uuid.UUID, current_user: CurrentUserDep):
    try:
        updated = await OrderService.mark_order_paid(current_user.sub, str(order_id))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment failed: {str(e)}")

    if not updated:
        raise HTTPException(status_code=400, detail="Cannot mark this order as paid")

    return {"detail": "Payment confirmed", "order": updated}