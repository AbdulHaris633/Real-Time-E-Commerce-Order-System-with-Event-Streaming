# app/schemas/webhook.py
from pydantic import BaseModel, HttpUrl, Field, UUID4
from typing import List, Optional
from datetime import datetime


class WebhookCreate(BaseModel):
    url: HttpUrl
    event_types: List[str] = Field(..., min_length=1)
    secret: Optional[str] = Field(None, min_length=8, max_length=100)

    model_config = {
        "json_schema_extra": {
            "example": {
                "url": "https://myapp.com/webhook",
                "event_types": ["order.created", "order.shipped", "order.delivered"],
                "secret": "my-webhook-secret"
            }
        }
    }


class WebhookResponse(BaseModel):
    webhook_id: UUID4
    user_id: UUID4
    url: str
    event_types: List[str]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookLogResponse(BaseModel):
    log_id: UUID4
    webhook_id: UUID4
    order_id: Optional[UUID4]
    event_type: str
    response_status: Optional[int]
    attempts: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
