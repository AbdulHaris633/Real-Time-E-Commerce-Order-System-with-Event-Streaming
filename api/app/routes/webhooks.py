# app/routes/webhooks.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import List

from app.database import get_db
from app.schemas.webhook import WebhookCreate, WebhookResponse
from app.services.webhook_service import WebhookService

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=WebhookResponse, status_code=201, summary="Register Webhook")
@limiter.limit("10/hour")
async def register_webhook(
    request: Request,
    data: WebhookCreate,
    user_id: UUID,   # In production this comes from JWT
    db: AsyncSession = Depends(get_db),
):
    """
    Register a webhook endpoint to receive order event notifications.
    - **Rate limit:** 10 requests/hour per IP
    """
    webhook = await WebhookService.register(db, user_id, data)
    return webhook


@router.get("/", response_model=List[WebhookResponse], summary="List Webhooks")
@limiter.limit("100/minute")
async def list_webhooks(
    request: Request,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all active webhooks for a user."""
    webhooks = await WebhookService.list_webhooks(db, user_id)
    return webhooks


@router.delete("/{webhook_id}", status_code=200, summary="Delete Webhook")
@limiter.limit("20/minute")
async def delete_webhook(
    request: Request,
    webhook_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a registered webhook."""
    deleted = await WebhookService.delete_webhook(db, webhook_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"message": "Webhook deleted", "webhook_id": str(webhook_id)}
