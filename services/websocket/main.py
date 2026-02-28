# services/ websocket/main.py
"""
WebSocket Service
=================
Provides real-time order status updates to connected clients.
- Subscribes to Redis pub/sub channels per user
- Heartbeat ping/pong every 30 seconds
- Connection management with Redis session tracking
- Consumes Kafka events and broadcasts to clients
"""
import asyncio
import json
import logging
import os
import uuid
from typing import Dict

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("websocket_service")

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
HEARTBEAT_INTERVAL = 30  # seconds

app = FastAPI(
    title="WebSocket Service",
    description="Real-time order status updates",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    """Manages active WebSocket connections per user."""

    def __init__(self):
        # user_id →  {connection_id → websocket}
        self.connections: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket) -> str:
        connection_id = str(uuid.uuid4())
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = {}
        self.connections[user_id][connection_id] = websocket
        logger.info(f"Connected: user={user_id} conn={connection_id} | total_users={len(self.connections)}")
        return connection_id

    def disconnect(self, user_id: str, connection_id: str):
        if user_id in self.connections:
            self.connections[user_id].pop(connection_id, None)
            if not self.connections[user_id]:
                del self.connections[user_id]
        logger.info(f"Disconnected: user={user_id} conn={connection_id}")

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id not in self.connections:
            return
        dead = []
        for conn_id, ws in self.connections[user_id].items():
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(conn_id)
        for conn_id in dead:
            self.disconnect(user_id, conn_id)

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self.connections.values())


manager = ConnectionManager()


async def redis_subscriber(user_id: str, connection_id: str, websocket: WebSocket):
    """Subscribe to user's Redis channel and forward messages to WebSocket."""
    redis = await aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    pubsub = redis.pubsub()
    channel = f"orders:{user_id}"
    await pubsub.subscribe(channel)
    logger.info(f"Subscribed to Redis channel: {channel}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
    except asyncio.CancelledError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await redis.close()


@app.websocket("/ws/orders/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time order updates.
    Connect: ws://localhost:8001/ws/orders/{user_id}
    Send "ping" → receive "pong" for heartbeat
    """
    connection_id = await manager.connect(user_id, websocket)

    # Start Redis subscriber as background task
    subscriber_task = asyncio.create_task(
        redis_subscriber(user_id, connection_id, websocket)
    )

    # Send welcome message
    await websocket.send_json({
        "type": "connected",
        "message": f"Real-time updates active for user {user_id}",
        "connection_id": connection_id,
    })

    try:
        while True:
            try:
                # Wait for client messages with timeout for heartbeat
                data = await asyncio.wait_for(websocket.receive_text(), timeout=HEARTBEAT_INTERVAL)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send server heartbeat
                await websocket.send_json({"type": "heartbeat", "status": "alive"})

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: user={user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        subscriber_task.cancel()
        manager.disconnect(user_id, connection_id)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "websocket-service",
        "active_users": len(manager.connections),
        "total_connections": manager.total_connections,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
