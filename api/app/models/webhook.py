# app/models/webhook.py
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, Text, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    webhook_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(100), nullable=False)
    event_types = Column(JSON, nullable=False)    # List of event type strings
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="webhooks")
    logs = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Webhook(webhook_id={self.webhook_id}, url={self.url})>"


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.webhook_id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.order_id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    request_payload = Column(JSON)
    response_status = Column(Integer)
    response_body = Column(Text)
    attempts = Column(Integer, default=1)
    status = Column(String(20), nullable=False, index=True)  # success, failed, retrying
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    webhook = relationship("Webhook", back_populates="logs")

    def __repr__(self):
        return f"<WebhookLog(log_id={self.log_id}, status={self.status})>"
