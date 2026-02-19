# TECHNICAL ARCHITECTURE

# Real-Time E-Commerce Order System
## Complete Architecture, Database Design & File Structure

**Document Type:** Technical Architecture Specification  
**Version:** 1.0

---

## TABLE OF CONTENTS

1. System Architecture Overview
2. Complete File Structure
3. Database Architecture
4. Kafka Event Architecture
5. API Architecture
6. Docker Architecture
7. Redis Data Structures
8. WebSocket Architecture
9. Security Architecture
10. Network Architecture

---

## 1. System Architecture Overview

The system follows a microservices architecture with event-driven communication patterns. Each component is containerized and can scale independently.

### 1.1 High-Level Architecture

| Layer | Component | Technology | Port |
|-------|-----------|------------|------|
| API Gateway | Nginx | Nginx 1.25 | 80, 443 |
| Application | Order API | FastAPI + Uvicorn | 8000 |
| Application | WebSocket Service | FastAPI + WebSockets | 8001 |
| Workers | Kafka Consumers | Python 3.11 | N/A |
| Message Broker | Apache Kafka | Kafka 3.5 | 9092 |
| Database | PostgreSQL | PostgreSQL 15 | 5432 |
| Cache | Redis | Redis 7 | 6379 |

---

## 2. Complete File Structure

The project follows a modular structure with clear separation of concerns. Each service is independently deployable.

### 2.1 Root Directory Structure

```
ecommerce-order-system/
├── .env                          # Environment variables
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Docker orchestration
├── docker-compose.prod.yml      # Production override
├── README.md                    # Project documentation
├── Makefile                     # Build automation
│
├── api/                         # Order API Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini             # Database migrations config
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI application
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database connection
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   │
│   │   ├── models/             # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── order.py
│   │   │   ├── user.py
│   │   │   ├── webhook.py
│   │   │   └── order_event.py
│   │   │
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── order.py
│   │   │   ├── user.py
│   │   │   └── webhook.py
│   │   │
│   │   ├── routes/             # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── orders.py
│   │   │   ├── webhooks.py
│   │   │   ├── health.py
│   │   │   └── auth.py
│   │   │
│   │   ├── services/           # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── order_service.py
│   │   │   ├── kafka_producer.py
│   │   │   ├── redis_service.py
│   │   │   └── webhook_service.py
│   │   │
│   │   ├── middleware/         # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── rate_limit.py
│   │   │   ├── logging.py
│   │   │   └── error_handler.py
│   │   │
│   │   └── utils/              # Utility functions
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       ├── jwt.py
│   │       └── helpers.py
│   │
│   ├── alembic/                # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   └── tests/                  # API tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_orders.py
│       ├── test_webhooks.py
│       └── test_auth.py
```

### 2.2 Workers Directory Structure

```
├── workers/                     # Background Workers
│   ├── common/                 # Shared worker code
│   │   ├── __init__.py
│   │   ├── kafka_consumer.py
│   │   ├── kafka_producer.py
│   │   └── database.py
│   │
│   ├── order_validator/        # Order validation worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   └── validator.py
│   │
│   ├── payment_processor/      # Payment processing worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── payment_gateway.py
│   │   └── payment_service.py
│   │
│   ├── inventory_manager/      # Inventory management worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   └── inventory_service.py
│   │
│   ├── fulfillment/           # Order fulfillment worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── shipping_service.py
│   │   └── warehouse_api.py
│   │
│   └── notification/          # Notification worker
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── main.py
│       ├── email_service.py
│       ├── sms_service.py
│       └── templates/
│           ├── order_confirmation.html
│           ├── order_shipped.html
│           └── order_delivered.html
```

### 2.3 Services Directory Structure

```
├── services/                    # Microservices
│   ├── websocket/              # WebSocket service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py
│   │   ├── connection_manager.py
│   │   ├── redis_pubsub.py
│   │   └── kafka_consumer.py
│   │
│   └── webhook_dispatcher/     # Webhook delivery service
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── main.py
│       ├── dispatcher.py
│       ├── retry_logic.py
│       └── signature.py
```

### 2.4 Infrastructure & Configuration

```
├── docker/                      # Docker configurations
│   ├── nginx/
│   │   ├── Dockerfile
│   │   ├── nginx.conf
│   │   └── ssl/
│   │       ├── cert.pem
│   │       └── key.pem
│   │
│   └── kafka/
│       └── topics.sh           # Kafka topic creation
│
├── config/                      # Configuration files
│   ├── development.env
│   ├── staging.env
│   ├── production.env
│   └── logging.yaml
│
├── scripts/                     # Utility scripts
│   ├── setup.sh               # Initial setup
│   ├── migrate.sh             # Run migrations
│   ├── seed.sh                # Seed data
│   ├── test.sh                # Run tests
│   └── deploy.sh              # Deployment script
│
├── monitoring/                  # Monitoring configs
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── datasources/
│   └── alertmanager/
│       └── config.yml
│
├── docs/                        # Documentation
│   ├── api/
│   │   ├── openapi.yaml
│   │   └── postman_collection.json
│   ├── architecture/
│   │   ├── diagrams/
│   │   └── decisions/
│   └── guides/
│       ├── deployment.md
│       └── troubleshooting.md
│
└── tests/                       # Integration tests
    ├── integration/
    ├── e2e/
    └── performance/
```

---

## 3. Database Architecture

### 3.1 PostgreSQL Schema Design

#### Table: orders

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| **order_id** | UUID | PRIMARY KEY | Unique order identifier |
| user_id | UUID | NOT NULL, INDEX | Customer who placed order |
| status | ENUM | NOT NULL, INDEX | Order status |
| items | JSONB | NOT NULL | Order items array |
| total_amount | DECIMAL(10,2) | NOT NULL | Total order amount |
| shipping_address | JSONB | NOT NULL | Delivery address |
| payment_method | VARCHAR(50) | NOT NULL | Payment method used |
| created_at | TIMESTAMP | DEFAULT NOW() | Order creation time |
| updated_at | TIMESTAMP | ON UPDATE | Last update time |
| metadata | JSONB | DEFAULT '{}' | Additional metadata |

**Indexes:**
- idx_orders_user_id ON user_id
- idx_orders_status ON status
- idx_orders_created_at ON created_at
- idx_orders_user_status ON (user_id, status)

### 3.2 Complete Database Schema SQL

```sql
-- Create extension for UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Order Status Enum
CREATE TYPE order_status AS ENUM (
    'pending',
    'validated',
    'processing',
    'paid',
    'fulfilled',
    'shipped',
    'delivered',
    'cancelled',
    'failed'
);

-- Orders Table
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    status order_status NOT NULL DEFAULT 'pending',
    items JSONB NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address JSONB NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    CONSTRAINT chk_total_amount CHECK (total_amount >= 0)
);

-- Order Items Table
CREATE TABLE order_items (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id UUID NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_quantity CHECK (quantity > 0),
    CONSTRAINT chk_unit_price CHECK (unit_price >= 0)
);

-- Order Events Table
CREATE TABLE order_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Webhooks Table
CREATE TABLE webhooks (
    webhook_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(100) NOT NULL,
    event_types TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook Logs Table
CREATE TABLE webhook_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id UUID NOT NULL REFERENCES webhooks(webhook_id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(order_id),
    event_type VARCHAR(50) NOT NULL,
    request_payload JSONB,
    response_status INTEGER,
    response_body TEXT,
    attempts INTEGER DEFAULT 1,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users Table (simplified)
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_events_order_id ON order_events(order_id);
CREATE INDEX idx_order_events_type_time ON order_events(event_type, created_at);
CREATE INDEX idx_webhooks_user_id ON webhooks(user_id);
CREATE INDEX idx_webhooks_active ON webhooks(is_active);
CREATE INDEX idx_webhook_logs_webhook_id ON webhook_logs(webhook_id);
CREATE INDEX idx_webhook_logs_status ON webhook_logs(status);
```

---

## 4. Kafka Event Architecture

### 4.1 Kafka Topics Configuration

| Topic Name | Partitions | Replicas | Consumer Group |
|------------|------------|----------|----------------|
| order_created | 3 | 3 | order-validator-group |
| order_validated | 3 | 3 | payment-processor-group |
| order_payment_processed | 3 | 3 | inventory-group, fulfillment-group |
| order_fulfilled | 3 | 3 | notification-group, websocket-group |
| order_shipped | 3 | 3 | notification-group, websocket-group |
| order_cancelled | 3 | 3 | inventory-group, notification-group |

### 4.2 Event Schemas

#### OrderCreatedEvent

```json
{
  "event_type": "order.created",
  "order_id": "uuid",
  "user_id": "uuid",
  "items": [
    {
      "product_id": "uuid",
      "quantity": "integer",
      "price": "decimal"
    }
  ],
  "total_amount": "decimal",
  "shipping_address": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string"
  },
  "payment_method": "string",
  "status": "pending",
  "created_at": "timestamp"
}
```

#### OrderValidatedEvent

```json
{
  "event_type": "order.validated",
  "order_id": "uuid",
  "validation_result": {
    "inventory_check": "boolean",
    "pricing_check": "boolean",
    "customer_check": "boolean"
  },
  "validated_at": "timestamp"
}
```

---

## 5. API Architecture

### 5.1 REST API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | /api/v1/orders | Create new order | 20/min |
| GET | /api/v1/orders/{id} | Get order details | 100/min |
| GET | /api/v1/orders | List user orders | 100/min |
| DELETE | /api/v1/orders/{id} | Cancel order | 20/min |
| POST | /api/v1/webhooks | Register webhook | 10/hour |
| GET | /api/v1/webhooks | List webhooks | 100/min |
| WS | /ws/orders/{user_id} | WebSocket connection | 5 concurrent |

### 5.2 Authentication Flow

1. User sends credentials to `/api/v1/auth/login`
2. Server validates and returns JWT token
3. Client includes token in `Authorization: Bearer <token>` header
4. Middleware validates token on each request
5. Token expires after 15 minutes
6. Refresh token valid for 7 days

### 5.3 Rate Limiting Strategy

**Redis Key Structure:**
```
ratelimit:{user_id}:{endpoint}:{window_start_timestamp}
```

**Algorithm:** Sliding Window

**Headers Returned:**
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Timestamp when limit resets

---

## 6. Docker Architecture

### 6.1 Production Docker Compose

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - order-api
      - websocket-service
    networks:
      - frontend

  order-api:
    build: ./api
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - KAFKA_BROKERS=${KAFKA_BROKERS}
    depends_on:
      - postgres
      - redis
      - kafka
    networks:
      - frontend
      - backend

  websocket-service:
    build: ./services/websocket
    deploy:
      replicas: 2
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=${REDIS_URL}
      - KAFKA_BROKERS=${KAFKA_BROKERS}
    networks:
      - frontend
      - backend

  order-validator:
    build: ./workers/order_validator
    deploy:
      replicas: 3
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - KAFKA_BROKERS=${KAFKA_BROKERS}
    networks:
      - backend

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=orders_db
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  kafka_data:
```

---

## 7. Redis Data Structures

### 7.1 Rate Limiting

```
Key: ratelimit:user:{user_id}:{endpoint}
Type: String (counter)
TTL: 60 seconds
Value: Request count
```

### 7.2 WebSocket Sessions

```
Key: websocket:session:{user_id}
Type: Hash
Fields:
  - connection_id: UUID
  - connected_at: timestamp
  - last_ping: timestamp
TTL: 3600 seconds
```

### 7.3 Order Cache

```
Key: order:{order_id}
Type: Hash
Fields: All order fields
TTL: 1800 seconds (30 minutes)
```

---

## 8. WebSocket Architecture

### 8.1 Connection Flow

1. Client connects to `ws://api.example.com/ws/orders/{user_id}`
2. Server validates JWT token from query params or headers
3. Connection added to ConnectionManager
4. User subscribed to their order updates channel in Redis
5. Heartbeat ping/pong every 30 seconds
6. On disconnect, cleanup from ConnectionManager and Redis

### 8.2 Message Format

```json
{
  "type": "order.update",
  "order_id": "uuid",
  "status": "shipped",
  "message": "Your order has been shipped",
  "timestamp": "2026-02-17T10:30:00Z",
  "data": {
    "tracking_number": "1Z999AA1234567890",
    "carrier": "UPS",
    "estimated_delivery": "2026-02-20"
  }
}
```

---

## 9. Security Architecture

### 9.1 Authentication & Authorization

- **JWT Tokens:** RS256 algorithm with public/private key pairs
- **Token Storage:** Client-side (localStorage/sessionStorage)
- **Token Rotation:** Automatic refresh before expiry
- **RBAC:** Role-based access control (admin, user, system)

### 9.2 Data Encryption

- **At Rest:** AES-256 encryption for sensitive fields
- **In Transit:** TLS 1.3 for all communications
- **Database:** PostgreSQL native encryption
- **Secrets:** HashiCorp Vault or AWS Secrets Manager

### 9.3 API Security

- **Rate Limiting:** Per-user and per-IP limits
- **Input Validation:** Pydantic schemas for all inputs
- **SQL Injection Prevention:** Parameterized queries
- **XSS Prevention:** Content Security Policy headers
- **CORS:** Restricted to allowed origins

---

## 10. Network Architecture

### 10.1 Network Segmentation

```
Internet
    ↓
[Load Balancer]
    ↓
[API Gateway - Nginx]
    ↓
┌────────────────────┐
│  Frontend Network  │
│  - API Services    │
│  - WebSocket       │
└────────────────────┘
    ↓
┌────────────────────┐
│  Backend Network   │
│  - Workers         │
│  - Kafka           │
│  - PostgreSQL      │
│  - Redis           │
└────────────────────┘
```

### 10.2 Port Assignments

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Nginx | 80, 443 | 80, 443 | HTTP/HTTPS |
| Order API | 8000 | - | HTTP |
| WebSocket | 8001 | 8001 | WS/WSS |
| PostgreSQL | 5432 | - | TCP |
| Redis | 6379 | - | TCP |
| Kafka | 9092 | - | TCP |

---

**End of Technical Architecture Document**
