import uuid
from typing import Optional

from fastapi import APIRouter, status, HTTPException, Body, Query

from core.authentication import CurrentUserDep
from services.order_service import OrderService
from models.order import Order


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=list[Order], status_code=status.HTTP_200_OK)
async def get_user_orders(
    current_user: CurrentUserDep,
    status_filter: Optional[str] = Query(None, alias="status")
):
    orders = await OrderService.get_orders(current_user.id, status_filter)
    return orders


@router.get("/{order_id}", response_model=Order)
async def get_user_order(order_id: uuid.UUID, current_user: CurrentUserDep):
    order = await OrderService.get_order(current_user.id, str(order_id))
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/create", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    current_user: CurrentUserDep,
    order_data: dict = Body(...)
):
    try:
        order_data["user_id"] = current_user.id
        order = await OrderService.create_order(order_data)
        return order
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cancel/{order_id}", status_code=status.HTTP_200_OK)
async def cancel_order(order_id: uuid.UUID, current_user: CurrentUserDep):
    success = await OrderService.cancel_order(current_user.id, str(order_id))
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel this order")
    return {"detail": "Order canceled successfully"}