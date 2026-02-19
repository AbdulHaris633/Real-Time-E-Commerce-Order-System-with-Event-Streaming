# app/models/order.py
from sqlalchemy import Column, String, Numeric, DateTime, JSON, Enum as SAEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
import enum

from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    PROCESSING = "processing"
    PAID = "paid"
    FULFILLED = "fulfilled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Order(Base):
    __tablename__ = "orders"

    order_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    status = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)
    items = Column(JSON, nullable=False)               # List of {product_id, quantity, unit_price, total_price}
    total_amount = Column(Numeric(10, 2), nullable=False)
    shipping_address = Column(JSON, nullable=False)    # {street, city, state, zip, country}
    payment_method = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    metadata_ = Column("metadata", JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="orders")
    events = relationship("OrderEvent", back_populates="order", cascade="all, delete-orphan")

    # Composite index for common query pattern
    __table_args__ = (
        Index("idx_orders_user_status", "user_id", "status"),
        Index("idx_orders_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Order(order_id={self.order_id}, status={self.status})>"
