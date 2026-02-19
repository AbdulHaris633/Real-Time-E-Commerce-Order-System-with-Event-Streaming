# app/services/order_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid
import logging

from app.models.order import Order, OrderStatus
from app.models.order_event import OrderEvent
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.kafka_producer import produce_order_event
from app.services.redis_service import cache_set, cache_get, cache_delete, publish_order_update

logger = logging.getLogger(__name__)

CACHE_TTL = 1800  # 30 minutes


class OrderService:

    @staticmethod
    async def create_order(db: AsyncSession, order_data: OrderCreate) -> Order:
        order = Order(
            user_id=order_data.user_id,
            items=[item.model_dump() for item in order_data.items],
            total_amount=order_data.total_amount,
            shipping_address=order_data.shipping_address.model_dump(),
            payment_method=order_data.payment_method,
            status=OrderStatus.PENDING,
            metadata_=order_data.metadata or {},
        )
        db.add(order)
        await db.flush()

        # Audit event
        event = OrderEvent(
            order_id=order.order_id,
            event_type="order.created",
            event_data={"status": OrderStatus.PENDING.value},
            created_by="api",
        )
        db.add(event)
        await db.commit()
        await db.refresh(order)

        # Publish Kafka event
        await produce_order_event("order.created", order)

        # Cache the order
        await cache_set(f"order:{order.order_id}", _order_to_dict(order))

        logger.info(f"Order created: {order.order_id}")
        return order

    @staticmethod
    async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Optional[Order]:
        cache_key = f"order:{order_id}"
        cached = await cache_get(cache_key)
        if cached:
            logger.debug(f"Cache hit for order {order_id}")
            return cached   # Return dict from cache

        result = await db.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if order:
            await cache_set(cache_key, _order_to_dict(order))
        return order

    @staticmethod
    async def list_orders(
        db: AsyncSession,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 10,
        status: Optional[OrderStatus] = None,
    ) -> tuple[List[Order], int]:
        query = select(Order).where(Order.user_id == user_id)
        count_query = select(func.count()).select_from(Order).where(Order.user_id == user_id)

        if status:
            query = query.where(Order.status == status)
            count_query = count_query.where(Order.status == status)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        result = await db.execute(
            query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        )
        orders = result.scalars().all()
        return list(orders), total

    @staticmethod
    async def update_order_status(
        db: AsyncSession, order_id: uuid.UUID, update: OrderUpdate
    ) -> Optional[Order]:
        result = await db.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return None

        old_status = order.status
        if update.status:
            order.status = update.status
        if update.metadata:
            order.metadata_ = {**(order.metadata_ or {}), **update.metadata}

        # Audit event
        event = OrderEvent(
            order_id=order.order_id,
            event_type=f"order.status_changed",
            event_data={"from": old_status.value, "to": update.status.value if update.status else old_status.value},
            created_by="api",
        )
        db.add(event)
        await db.commit()
        await db.refresh(order)

        # Invalidate cache
        await cache_delete(f"order:{order_id}")

        # Notify via WebSocket pub/sub
        await publish_order_update(str(order.user_id), {
            "type": "order.update",
            "order_id": str(order.order_id),
            "status": order.status.value,
            "message": f"Your order status changed to {order.status.value}",
        })

        # Publish Kafka event
        await produce_order_event(f"order.{order.status.value}", order)

        return order

    @staticmethod
    async def cancel_order(db: AsyncSession, order_id: uuid.UUID) -> Optional[Order]:
        result = await db.execute(select(Order).where(Order.order_id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return None
        if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            return None  # Cannot cancel

        order.status = OrderStatus.CANCELLED
        event = OrderEvent(
            order_id=order.order_id,
            event_type="order.cancelled",
            event_data={},
            created_by="api",
        )
        db.add(event)
        await db.commit()
        await db.refresh(order)
        await cache_delete(f"order:{order_id}")
        await produce_order_event("order.cancelled", order)
        return order


def _order_to_dict(order: Order) -> dict:
    return {
        "order_id": str(order.order_id),
        "user_id": str(order.user_id),
        "status": order.status.value,
        "items": order.items,
        "total_amount": float(order.total_amount),
        "shipping_address": order.shipping_address,
        "payment_method": order.payment_method,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "metadata": order.metadata_ or {},
    }
