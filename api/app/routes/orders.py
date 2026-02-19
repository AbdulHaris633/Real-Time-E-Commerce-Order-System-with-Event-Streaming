# app/routes/orders.py
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderResponse, OrderUpdate, OrderListResponse
from app.services.order_service import OrderService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=OrderResponse, status_code=201, summary="Create Order")
@limiter.limit("20/minute")
async def create_order(
    request: Request,
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new order and publish an event to Kafka for async processing.
    - **Rate limit:** 20 requests/minute per IP
    """
    order = await OrderService.create_order(db, order_data)
    return order


@router.get("/", response_model=OrderListResponse, summary="List Orders")
@limiter.limit("100/minute")
async def list_orders(
    request: Request,
    user_id: UUID = Query(..., description="Filter orders by user ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all orders for a user with optional status filtering and pagination.
    - **Rate limit:** 100 requests/minute per IP
    """
    skip = (page - 1) * page_size
    orders, total = await OrderService.list_orders(db, user_id, skip, page_size, status)
    return OrderListResponse(
        orders=orders,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(skip + page_size) < total,
    )


@router.get("/{order_id}", response_model=OrderResponse, summary="Get Order")
@limiter.limit("100/minute")
async def get_order(
    request: Request,
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get details of a specific order. Served from Redis cache when available.
    - **Rate limit:** 100 requests/minute per IP
    """
    order = await OrderService.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}", response_model=OrderResponse, summary="Update Order Status")
@limiter.limit("20/minute")
async def update_order(
    request: Request,
    order_id: UUID,
    update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update order status. Triggers a Kafka event and WebSocket notification.
    - **Rate limit:** 20 requests/minute per IP
    """
    order = await OrderService.update_order_status(db, order_id, update)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=200, summary="Cancel Order")
@limiter.limit("20/minute")
async def cancel_order(
    request: Request,
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an order (only if not yet shipped/delivered).
    - **Rate limit:** 20 requests/minute per IP
    """
    order = await OrderService.cancel_order(db, order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found or cannot be cancelled (already shipped/delivered)"
        )
    return {"message": "Order cancelled successfully", "order_id": str(order_id)}
