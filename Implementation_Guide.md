# IMPLEMENTATION GUIDE

# Real-Time E-Commerce Order System
## Step-by-Step Development Guide

**Document Type:** Technical Implementation Guide  
**Audience:** Developers, DevOps Engineers  
**Date:** February 17, 2026

---

## GETTING STARTED CHECKLIST

### Before You Begin:

- ✓ Python 3.11+ installed
- ✓ Docker & Docker Compose installed
- ✓ Git installed and configured
- ✓ Code editor (VS Code recommended)
- ✓ Basic knowledge of Python, FastAPI, and Docker
- ✓ PostgreSQL client (psql) for database management
- ✓ Terminal/command line familiarity

### Estimated Time:

Complete implementation: 18-20 weeks

---

## PART 1: Initial Setup & Environment

### Day 1: Project Initialization

#### Step 1: Create Project Directory

Open your terminal and create the project structure:

```bash
mkdir ecommerce-order-system
cd ecommerce-order-system

# Create main directories
mkdir -p api workers services/websocket services/webhook
mkdir -p docker tests config docs
mkdir -p api/app api/app/models api/app/routes api/app/middleware
mkdir -p workers/order_validator workers/payment_processor
mkdir -p workers/inventory_manager workers/fulfillment
```

#### Step 2: Initialize Git Repository

```bash
git init
git branch -M main

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/
*.log
.DS_Store
*.db
*.sqlite3
node_modules/
.idea/
.vscode/
docker-compose.override.yml
EOF
```

#### Step 3: Create Environment Configuration

Create .env.example file for environment variables:

```bash
# .env.example
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/orders_db
DATABASE_TEST_URL=postgresql://user:password@postgres:5432/orders_test_db

# Redis
REDIS_URL=redis://redis:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# Environment
ENVIRONMENT=development
```

⚠️ **Important:** Copy .env.example to .env and update with your actual values

---

### Day 1-2: Docker Setup

#### Step 4: Create Docker Network Architecture

Create docker-compose.yml in the project root:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: orders_postgres
    environment:
      POSTGRES_DB: orders_db
      POSTGRES_USER: orderuser
      POSTGRES_PASSWORD: orderpass
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orderuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: orders_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Zookeeper for Kafka
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    container_name: orders_zookeeper
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data

  # Kafka Broker
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    container_name: orders_kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka_data:/var/lib/kafka/data

volumes:
  postgres_data:
  redis_data:
  zookeeper_data:
  kafka_data:

networks:
  default:
    name: orders_network
```

#### Step 5: Start Infrastructure Services

```bash
# Start all infrastructure services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

✓ **Success:** You should see all services healthy and running

---

## PART 2: Core API Development

### Week 2: FastAPI Application Setup

#### Step 6: Create Python Virtual Environment

```bash
cd api
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

#### Step 7: Install Dependencies

Create requirements.txt:

```txt
# requirements.txt
fastapi==0.110.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
redis[hiredis]==5.0.1
confluent-kafka==2.3.0
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
aiohttp==3.9.1
slowapi==0.1.9
alembic==1.13.1
pytest==7.4.3
pytest-asyncio==0.23.2
httpx==0.26.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

#### Step 8: Create Application Structure

Create the main FastAPI application (app/main.py):

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routes import orders, webhooks, health
from app.middleware.auth import AuthMiddleware

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="E-Commerce Order System API",
    description="Real-time order processing with event streaming",
    version="1.0.0"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    return {"message": "E-Commerce Order System API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

#### Step 9: Create Database Models

Create SQLAlchemy models (app/models/order.py):

```python
# app/models/order.py
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
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
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    items = Column(JSON, nullable=False)
    total_amount = Column(Float, nullable=False)
    shipping_address = Column(JSON, nullable=False)
    payment_method = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
```

#### Step 10: Create Database Connection

Set up async database connection (app/database.py):

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

#### Step 11: Create Order Routes

Implement order endpoints (app/routes/orders.py):

```python
# app/routes/orders.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderResponse
from app.services.kafka_producer import produce_order_event
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

@router.post("/", response_model=OrderResponse, status_code=201)
@limiter.limit("20/minute")  # Order creation rate limit
async def create_order(
    request: Request,
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    # Create order
    order = Order(
        user_id=order_data.user_id,
        items=order_data.items,
        total_amount=order_data.total_amount,
        shipping_address=order_data.shipping_address.dict(),
        payment_method=order_data.payment_method,
        status=OrderStatus.PENDING
    )
    
    db.add(order)
    await db.commit()
    await db.refresh(order)
    
    # Publish event to Kafka
    await produce_order_event("order.created", order)
    
    return order

@router.get("/{order_id}", response_model=OrderResponse)
@limiter.limit("100/minute")  # Read operations rate limit
async def get_order(
    request: Request,
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order

@router.get("/", response_model=List[OrderResponse])
@limiter.limit("100/minute")
async def list_orders(
    request: Request,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    orders = result.scalars().all()
    return orders
```

---

## PART 3: Kafka Event Streaming

### Week 3: Kafka Producer Setup

#### Step 12: Create Kafka Producer Service

Implement Kafka producer (app/services/kafka_producer.py):

```python
# app/services/kafka_producer.py
from confluent_kafka import Producer
import json
import os
import asyncio
from typing import Any, Dict

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

producer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'order-api-producer'
}

producer = Producer(producer_config)

def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f'Message delivered to {msg.topic()} [{msg.partition()}]')

async def produce_order_event(event_type: str, order: Any):
    event_data = {
        'event_type': event_type,
        'order_id': str(order.order_id),
        'user_id': str(order.user_id),
        'status': order.status,
        'total_amount': order.total_amount,
        'items': order.items,
        'timestamp': order.created_at.isoformat()
    }
    
    # Produce to Kafka
    producer.produce(
        topic=event_type.replace('.', '_'),
        key=str(order.order_id),
        value=json.dumps(event_data),
        callback=delivery_report
    )
    
    # Flush to ensure delivery
    producer.flush()
```

#### Step 13: Create Kafka Topics

Create a script to initialize Kafka topics (scripts/create_topics.sh):

```bash
#!/bin/bash
# scripts/create_topics.sh

KAFKA_CONTAINER="orders_kafka"

# Create topics
docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic order_created \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic order_validated \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

docker exec $KAFKA_CONTAINER kafka-topics --create \
  --topic order_payment_processed \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

echo "Topics created successfully!"
```

Run the script:

```bash
chmod +x scripts/create_topics.sh
./scripts/create_topics.sh
```

### Week 4: Kafka Consumer Workers

#### Step 14: Create Order Validator Worker

Implement the first background worker (workers/order_validator/main.py):

```python
# workers/order_validator/main.py
from confluent_kafka import Consumer, Producer
import json
import os
import asyncio

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

consumer_config = {
    'bootstrap.servers': KAFKA_SERVERS,
    'group.id': 'order-validator-group',
    'auto.offset.reset': 'earliest'
}

producer_config = {
    'bootstrap.servers': KAFKA_SERVERS,
    'client.id': 'order-validator-producer'
}

consumer = Consumer(consumer_config)
producer = Producer(producer_config)

async def validate_order(order_data: dict):
    # Validation logic
    print(f"Validating order: {order_data['order_id']}")
    
    # Check inventory, pricing, etc.
    is_valid = True  # Implement actual validation
    
    if is_valid:
        # Publish validated event
        validated_event = {
            'event_type': 'order.validated',
            'order_id': order_data['order_id'],
            'timestamp': order_data['timestamp']
        }
        
        producer.produce(
            topic='order_validated',
            key=order_data['order_id'],
            value=json.dumps(validated_event)
        )
        producer.flush()
        print(f"Order {order_data['order_id']} validated")
    else:
        print(f"Order {order_data['order_id']} validation failed")

def main():
    consumer.subscribe(['order_created'])
    
    print("Order Validator Worker started...")
    
    try:
        while True:
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"Error: {msg.error()}")
                continue
            
            # Process message
            order_data = json.loads(msg.value().decode('utf-8'))
            asyncio.run(validate_order(order_data))
            
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
```

---

## PART 4: WebSocket Real-Time Updates

### Week 5: WebSocket Implementation

#### Step 15: Create WebSocket Service

Implement WebSocket endpoint (services/websocket/main.py):

```python
# services/websocket/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
import redis.asyncio as redis
import json
import asyncio
import uuid

app = FastAPI()

# Connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/orders/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            # Keep connection alive with heartbeat
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"Client {user_id} disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## PART 5: Testing & Validation

### Week 6: Testing Strategy

#### Step 16: Create Unit Tests

Create test suite (tests/test_orders.py):

```python
# tests/test_orders.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_order():
    async with AsyncClient(app=app, base_url="http://test") as client:
        order_data = {
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "items": [
                {"product_id": "prod-1", "quantity": 2, "price": 29.99}
            ],
            "total_amount": 59.98,
            "shipping_address": {
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip": "10001"
            },
            "payment_method": "CREDIT_CARD"
        }
        
        response = await client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 201
        assert "order_id" in response.json()

@pytest.mark.asyncio
async def test_get_order():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create order first
        # ... (same as above)
        
        order_id = response.json()["order_id"]
        
        # Get order
        get_response = await client.get(f"/api/v1/orders/{order_id}")
        
        assert get_response.status_code == 200
        assert get_response.json()["order_id"] == order_id
```

Run tests:

```bash
pytest tests/ -v
```

---

## PART 6: Production Deployment

### Week 7: Docker Production Setup

#### Step 17: Create Production Dockerfile

Create optimized Dockerfile for API (api/Dockerfile):

```dockerfile
# api/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Step 18: Build and Deploy

```bash
# Build Docker image
docker build -t ecommerce-order-api:1.0 ./api

# Update docker-compose.yml to include API service
# Then start all services
docker-compose up -d

# Verify deployment
curl http://localhost:8000/health
```

✓ **Congratulations!** Your E-Commerce Order System is now running!

---

## Next Steps & Resources

### What to Do Next

1. Implement remaining workers (payment, inventory, fulfillment)
2. Add comprehensive monitoring with Prometheus and Grafana
3. Implement webhook delivery system
4. Add authentication and authorization
5. Set up CI/CD pipeline
6. Deploy to Kubernetes for production
7. Implement comprehensive logging and alerting
8. Load test the system

---

**End of Implementation Guide**
