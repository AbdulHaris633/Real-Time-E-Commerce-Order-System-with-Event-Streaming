# app/schemas/order.py
from pydantic import BaseModel, Field, UUID4, field_validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from app.models.order import OrderStatus


# ── Sub-schemas ────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: str = Field(..., description="Product UUID")
    quantity: int = Field(..., gt=0, description="Quantity must be positive")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")

    @property
    def total_price(self) -> Decimal:
        return self.quantity * self.unit_price


class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = {"from_attributes": True}


class ShippingAddress(BaseModel):
    street: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    zip: str = Field(..., min_length=1, max_length=20)
    country: str = Field(default="US", min_length=2, max_length=2)


# ── Request Schemas ────────────────────────────────────────────────────────────

class OrderCreate(BaseModel):
    user_id: UUID4
    items: List[OrderItemCreate] = Field(..., min_length=1)
    total_amount: Decimal = Field(..., ge=0)
    shipping_address: ShippingAddress
    payment_method: str = Field(..., min_length=1, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("total_amount")
    @classmethod
    def validate_total(cls, v, info):
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "items": [
                    {"product_id": "prod-001", "quantity": 2, "unit_price": 29.99}
                ],
                "total_amount": 59.98,
                "shipping_address": {
                    "street": "123 Main St",
                    "city": "New York",
                    "state": "NY",
                    "zip": "10001",
                    "country": "US"
                },
                "payment_method": "CREDIT_CARD"
            }
        }
    }


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    metadata: Optional[Dict[str, Any]] = None


# ── Response Schemas ───────────────────────────────────────────────────────────

class OrderResponse(BaseModel):
    order_id: UUID4
    user_id: UUID4
    status: OrderStatus
    items: List[Dict[str, Any]]
    total_amount: Decimal
    shipping_address: Dict[str, Any]
    payment_method: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
