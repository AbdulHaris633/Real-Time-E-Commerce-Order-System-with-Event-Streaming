# app/services/webhook_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
import secrets
import logging

from app.models.webhook import Webhook, WebhookLog
from app.schemas.webhook import WebhookCreate

logger = logging.getLogger(__name__)


class WebhookService:

    @staticmethod
    async def register(
        db: AsyncSession, user_id: uuid.UUID, data: WebhookCreate
    ) -> Webhook:
        secret = data.secret or secrets.token_hex(32)
        webhook = Webhook(
            user_id=user_id,
            url=str(data.url),
            secret=secret,
            event_types=data.event_types,
        )
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        logger.info(f"Webhook registered: {webhook.webhook_id} → {webhook.url}")
        return webhook

    @staticmethod
    async def list_webhooks(db: AsyncSession, user_id: uuid.UUID) -> List[Webhook]:
        result = await db.execute(
            select(Webhook).where(Webhook.user_id == user_id, Webhook.is_active == True)
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_webhook(
        db: AsyncSession, webhook_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        result = await db.execute(
            select(Webhook).where(Webhook.webhook_id == webhook_id, Webhook.user_id == user_id)
        )
        webhook = result.scalar_one_or_none()
        if not webhook:
            return False
        webhook.is_active = False
        await db.commit()
        return True
