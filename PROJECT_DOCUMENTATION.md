# Complete Project Documentation
## Real-Time E-Commerce Order Management System

---

# TABLE OF CONTENTS

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Technology Stack](#3-technology-stack)
4. [System Design & Flow](#4-system-design--flow)
5. [Project Structure](#5-project-structure)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Kafka Event Flow](#8-kafka-event-flow)
9. [Workers](#9-workers)
10. [WebSocket](#10-websocket)
11. [Frontend](#11-frontend)
12. [Docker Configuration](#12-docker-configuration)
13. [Environment Variables](#13-environment-variables)
14. [Running the Project](#14-running-the-project)
15. [Security](#15-security)
16. [API Documentation](#16-api-documentation)

---

# 1. PROJECT OVERVIEW

## 1.1 What is this Project?

This is a **Real-Time E-Commerce Order Management System** built with FastAPI, Kafka, PostgreSQL, Redis, and WebSockets. It provides a complete order processing pipeline with asynchronous worker services, real-time notifications, and a responsive frontend.

## 1.2 Key Features

- **RESTful API** for order management (create, read, update, delete)
- **JWT Authentication** for secure user login/registration
- **Kafka-based Event Streaming** for asynchronous order processing
- **Real-time WebSocket Notifications** for order status updates
- **Redis Caching** for fast order retrieval
- **Rate Limiting** to prevent abuse
- **Microservices Architecture** with isolated workers
- **Docker Containerization** for easy deployment
- **Frontend** for managing orders

## 1.3 Order Processing Pipeline

```
User creates order → API saves to DB → Kafka: order_created
    ↓
[Order Validator Worker] → Validates order → Kafka: order_validated
    ↓
[Payment Processor Worker] → Processes payment → Kafka: order_payment_processed
    ↓
[Inventory Manager Worker] → Manages inventory → Kafka: order_fulfilled
    ↓
[Fulfillment Worker] → Ships order → Kafka: order_shipped
    ↓
User receives real-time notification via WebSocket
```

---

# 2. ARCHITECTURE OVERVIEW

## 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        NGINX (Port 8082)                                │
│                    API Gateway / Load Balancer                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────┐   ┌───────────────────────────────────────────┐
│   ORDER API (Port 8000)   │   │       WEBSOCKET SERVICE (Port 8001)        │
│   - FastAPI Application   │   │   - Real-time order status notifications   │
│   - Authentication       │   │   - Redis pub/sub subscriber               │
│   - Order CRUD            │   │   - Connection manager                     │
│   - Rate Limiting         │   └───────────────────────────────────────────┘
│   - Kafka Producer        │
└───────────────────────────┘
            │                               │                       │
            ▼                               │                       │
┌───────────────────────────┐               │                       ▼
│     POSTGRESQL (5432)     │               │           ┌─────────────────────┐
│   - Orders Table          │               │           │     REDIS (6379)     │
│   - Users Table           │               │           │  - Rate limiting     │
│   - Webhooks Table        │               │           │  - Order caching     │
│   - Order Events Table    │               │           │  - Pub/Sub for WS    │
└───────────────────────────┘               │           └─────────────────────┘
            │                               │
            │ Kafka Topics                  │
            ▼                               │
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND SERVICES (Workers)                          │
├─────────────────┬─────────────────┬─────────────────┬─────────────────┤
│  Order Validator│ Payment Processor│ Inventory Manager│   Fulfillment   │
│  - Validates    │ - Processes      │ - Manages        │ - Ships orders  │
│    orders       │   payments       │   inventory      │ - Generates    │
│                 │                  │                  │   tracking      │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   APACHE KAFKA (Port 9092)                             │
│  Topics: order_created → order_validated → order_payment_processed →   │
│          order_fulfilled → order_shipped                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Network Architecture

The system uses two Docker networks:
- **Frontend Network** (`orders_frontend`): Connects nginx, API, WebSocket
- **Backend Network** (`orders_backend`): Connects workers, Kafka, PostgreSQL, Redis

---

# 3. TECHNOLOGY STACK

## 3.1 Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| API Framework | FastAPI | Latest | REST API with async support |
| ASGI Server | Uvicorn | Latest | High-performance ASGI server |
| Database | PostgreSQL | 15 | Primary data store |
| ORM | SQLAlchemy | 2.x | Async database operations |
| Message Broker | Apache Kafka | 7.5.0 | Event streaming |
| Cache | Redis | 7 | Caching & pub/sub |
| Authentication | JWT | - | Secure token-based auth |
| Password Hashing | bcrypt | - | Secure password storage |
| Rate Limiting | slowapi | Latest | Per-IP/user rate limiting |
| Validation | Pydantic | Latest | Request/response validation |

## 3.2 Worker Technologies

| Worker | Language | Kafka Consumer | Function |
|--------|----------|----------------|----------|
| Order Validator | Python 3.11 | order_created | Validates orders |
| Payment Processor | Python 3.11 | order_validated | Processes payments |
| Inventory Manager | Python 3.11 | order_payment_processed | Manages inventory |
| Fulfillment | Python 3.11 | order_fulfilled | Ships orders |

## 3.3 Infrastructure Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| Container Runtime | Docker | Application containerization |
| Orchestration | Docker Compose | Multi-container management |
| Web Server | Nginx | API Gateway, static files |
| Frontend | HTML/CSS/JS | User interface |

---

# 4. SYSTEM DESIGN & FLOW

## 4.1 Order Creation Flow

```
1. User registers/login via frontend
2. Frontend stores JWT token
3. User creates order with items, shipping address, payment method
4. API validates request with Pydantic
5. API saves order to PostgreSQL
6. API creates "order.created" event in database
7. API publishes "order.created" event to Kafka
8. API caches order in Redis
9. API returns order response to user
10. WebSocket pushes real-time status updates to user
```

## 4.2 Async Processing Flow

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────────┐
│   ORDER API   │────▶│   KAFKA BROKER     │────▶│ ORDER VALIDATOR      │
│  (Producer)   │     │  order_created    │     │  (Consumer)           │
└──────────────┘     └───────────────────┘     └──────────────────────┘
                                                        │
                                                        ▼
                       ┌───────────────────┐     ┌──────────────────────┐
                       │  KAFKA BROKER      │◀────│  PAYMENT PROCESSOR   │
                       │  order_validated   │     │  (Consumer)           │
                       └───────────────────┘     └──────────────────────┘
                                                        │
                                                        ▼
                       ┌───────────────────┐     ┌──────────────────────┐
                       │  KAFKA BROKER      │◀────│  INVENTORY MANAGER    │
                       │  order_payment_    │     │  (Consumer)           │
                       │  processed         │     └──────────────────────┘
                       └───────────────────┘            │
                                                        ▼
                       ┌───────────────────┐     ┌──────────────────────┐
                       │  KAFKA BROKER      │◀────│  FULFILLMENT         │
                       │  order_fulfilled   │     │  (Consumer)           │
                       └───────────────────┘     └──────────────────────┘
                                                        │
                                                        ▼
                                                ┌──────────────────────┐
                                                │  WebSocket notifies  │
                                                │  user of status      │
                                                └──────────────────────┘
```

## 4.3 Data Flow

```
User Request
    │
    ▼
┌─────────────┐
│   NGINX     │ ─── Static files (frontend)
└─────────────┘
    │
    ▼
┌─────────────┐
│  FastAPI    │ ─── JWT Auth, Rate Limit
└─────────────┘
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
┌─────────┐      ┌──────────┐       ┌────────────┐
│ PostgreSQL│     │  Redis   │       │   Kafka    │
│ - Orders │     │ - Cache  │       │ - Events   │
│ - Users  │     │ - Rate   │       │            │
│ - Events │     │   Limit  │       │            │
└─────────┘      └──────────┘       └────────────┘
```

---

# 5. PROJECT STRUCTURE

```
FAST API/
├── docker-compose.yml          # Docker orchestration
├── .env                        # Environment variables
│
├── api/                        # Main API Service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pytest.ini
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI application entry
│       ├── config.py           # Settings & configuration
│       ├── database.py          # Database connection
│       │
│       ├── models/             # SQLAlchemy ORM models
│       │   ├── order.py        # Order model & OrderStatus enum
│       │   ├── user.py        # User model
│       │   ├── webhook.py      # Webhook model
│       │   └── order_event.py # Order event logging
│       │
│       ├── schemas/            # Pydantic request/response schemas
│       │   ├── order.py        # Order schemas
│       │   ├── user.py         # User schemas
│       │   └── webhook.py      # Webhook schemas
│       │
│       ├── routes/             # API endpoints
│       │   ├── orders.py       # Order CRUD endpoints
│       │   ├── auth.py         # Login/register endpoints
│       │   ├── webhooks.py    # Webhook management
│       │   └── health.py       # Health check
│       │
│       ├── services/           # Business logic
│       │   ├── order_service.py    # Order operations
│       │   ├── kafka_producer.py   # Kafka event publishing
│       │   ├── redis_service.py    # Redis caching & pub/sub
│       │   └── webhook_service.py   # Webhook delivery
│       │
│       └── utils/
│           └── jwt.py          # JWT token utilities
│
├── services/                   # Microservices
│   ├── websocket/              # WebSocket service
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py             # WebSocket connection manager
│   │
│   └── webhook_dispatcher/     # Webhook delivery service
│       ├── Dockerfile
│       ├── requirements.txt
│       └── main.py
│
├── workers/                    # Background workers
│   ├── common/                 # Shared code
│   │   ├── kafka_consumer.py   # Kafka consumer base class
│   │   └── __init__.py
│   │
│   ├── order_validator/        # Order validation worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py             # Validates orders
│   │
│   ├── payment_processor/      # Payment processing worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py             # Processes payments
│   │
│   ├── inventory_manager/      # Inventory management worker
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── main.py             # Manages inventory
│   │
│   └── fulfillment/            # Order fulfillment worker
│       ├── Dockerfile
│       ├── requirements.txt
│       └── main.py             # Ships orders, generates tracking
│
├── frontend/                   # Frontend application
│   └── index.html              # Single-page application
│
└── docker/                     # Docker configurations
    ├── nginx/
    │   └── nginx.conf          # Nginx configuration
    └── kafka/
        └── init.sql            # Database initialization
```

---

# 6. DATABASE SCHEMA

## 6.1 Tables

### Users Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | PRIMARY KEY | Unique user ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| full_name | VARCHAR(255) | NULL | User's full name |
| phone | VARCHAR(20) | NULL | Phone number |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| tier | VARCHAR(20) | DEFAULT 'standard' | User tier |
| created_at | TIMESTAMP | DEFAULT NOW() | Registration time |

### Orders Table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| order_id | UUID | PRIMARY KEY | Unique order ID |
| user_id | UUID | FOREIGN KEY, INDEX | Customer ID |
| status | ENUM | DEFAULT 'pending' | Order status |
| items | JSONB | NOT NULL | Array of order items |
| total_amount | DECIMAL(10,2) | NOT NULL | Total amount |
| shipping_address | JSONB | NOT NULL | Delivery address |
| payment_method | VARCHAR(50) | NOT NULL | Payment method |
| created_at | TIMESTAMP | DEFAULT NOW() | Order creation time |
| updated_at | TIMESTAMP | ON UPDATE | Last update time |
| metadata | JSONB | DEFAULT '{}' | Additional data |

### Order Status Enum
```python
PENDING = "pending"           # Order created, awaiting validation
VALIDATED = "validated"       # Order validated successfully
PROCESSING = "processing"     # Payment being processed
PAID = "paid"                 # Payment successful
FULFILLED = "fulfilled"       # Order picked from warehouse
SHIPPED = "shipped"           # Order shipped to customer
DELIVERED = "delivered"       # Order delivered
CANCELLED = "cancelled"       # Order cancelled
FAILED = "failed"             # Order failed
```

### Order Events Table
| Column | Type | Description |
|--------|------|-------------|
| event_id | UUID | Unique event ID |
| order_id | UUID | FOREIGN KEY | Related order |
| event_type | VARCHAR(50) | Event type |
| event_data | JSONB | Event data |
| created_at | TIMESTAMP | Event timestamp |
| created_by | VARCHAR(100) | Source of event |

### Webhooks Table
| Column | Type | Description |
|--------|------|-------------|
| webhook_id | UUID | Unique webhook ID |
| user_id | UUID | Owner of webhook |
| url | VARCHAR(500) | Callback URL |
| secret | VARCHAR(100) | HMAC signature secret |
| event_types | TEXT[] | Subscribed events |
| is_active | BOOLEAN | Active status |

---

# 7. API ENDPOINTS

## 7.1 Authentication Endpoints

### POST /api/v1/auth/register
Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2026-02-20T00:00:00Z"
}
```

### POST /api/v1/auth/login
Login and receive JWT tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "expires_in": 900
}
```

## 7.2 Order Endpoints

### POST /api/v1/orders
Create a new order.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "user_id": "uuid",
  "items": [
    {
      "product_id": "prod-001",
      "quantity": 2,
      "unit_price": 29.99
    }
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
```

### GET /api/v1/orders
List orders for a user.

**Query Parameters:**
- `user_id` (required): Filter by user
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10)
- `status`: Filter by order status

### GET /api/v1/orders/{order_id}
Get order details.

### DELETE /api/v1/orders/{order_id}
Cancel an order (only if not shipped/delivered).

## 7.3 Webhook Endpoints

### POST /api/v1/webhooks
Register a webhook.

### GET /api/v1/webhooks
List user's webhooks.

### DELETE /api/v1/webhooks/{webhook_id}
Delete a webhook.

## 7.4 Health Endpoints

### GET /health
Health check endpoint.

---

# 8. KAFKA EVENT FLOW

## 8.1 Topics

| Topic | Partitions | Producer | Consumer |
|-------|------------|----------|----------|
| order_created | 3 | API | order-validator |
| order_validated | 3 | order-validator | payment-processor |
| order_payment_processed | 3 | payment-processor | inventory-manager, fulfillment |
| order_fulfilled | 3 | inventory-manager | fulfillment |
| order_shipped | 3 | fulfillment | webhook-dispatcher |
| order_cancelled | 3 | API | inventory-manager |

## 8.2 Event Schemas

### order.created
```json
{
  "event_type": "order.created",
  "order_id": "uuid",
  "user_id": "uuid",
  "items": [...],
  "total_amount": 59.98,
  "shipping_address": {...},
  "payment_method": "CREDIT_CARD",
  "status": "pending",
  "created_at": "2026-02-20T00:00:00Z"
}
```

### order.validated
```json
{
  "event_type": "order.validated",
  "order_id": "uuid",
  "validation_result": {
    "inventory_check": true,
    "pricing_check": true,
    "customer_check": true
  },
  "validated_at": "2026-02-20T00:00:00Z"
}
```

### order.shipped
```json
{
  "event_type": "order.shipped",
  "order_id": "uuid",
  "user_id": "uuid",
  "shipping": {
    "carrier": "UPS",
    "tracking_number": "1ZABC123456789",
    "shipped_at": "2026-02-20T00:00:00Z",
    "estimated_delivery": "2026-02-25"
  }
}
```

---

# 9. WORKERS

## 9.1 Order Validator Worker

**Subscribes to:** `order_created`  
**Produces:** `order_validated`

**Responsibilities:**
- Validates pricing consistency
- Checks inventory availability
- Verifies customer eligibility

**Logic:**
```python
def validate_order(order_data):
    # Check pricing matches items total
    pricing_ok = calculated_total == total_amount
    
    # Check inventory (mocked)
    inventory_ok = all(item.quantity > 0)
    
    # Check customer exists
    customer_ok = bool(order_data.user_id)
    
    return {
        "pricing_check": pricing_ok,
        "inventory_check": inventory_ok,
        "customer_check": customer_ok,
        "is_valid": pricing_ok and inventory_ok and customer_ok
    }
```

## 9.2 Payment Processor Worker

**Subscribes to:** `order_validated`  
**Produces:** `order_payment_processed`

**Responsibilities:**
- Processes payment (mocked)
- Updates order status to PAID

## 9.3 Inventory Manager Worker

**Subscribes to:** `order_payment_processed`, `order_cancelled`  
**Produces:** `order_fulfilled`

**Responsibilities:**
- Reserves inventory for order
- Updates inventory levels
- Produces fulfillment event when ready

## 9.4 Fulfillment Worker

**Subscribes to:** `order_fulfilled`  
**Produces:** `order_shipped`

**Responsibilities:**
- Picks items from warehouse
- Packs order
- Generates shipping label
- Selects carrier (UPS, FedEx, DHL, USPS)
- Generates tracking number

---

# 10. WEBSOCKET

## 10.1 Connection

**Endpoint:** `ws://localhost:8001/ws/orders/{user_id}`

**Connection Flow:**
1. Client connects with user_id
2. Server accepts connection
3. Redis subscribes to `orders:{user_id}` channel
4. Server broadcasts order updates to client

## 10.2 Messages

### Server → Client
```json
{
  "type": "order.update",
  "order_id": "uuid",
  "status": "shipped",
  "message": "Your order has been shipped"
}
```

### Heartbeat
```json
{
  "type": "heartbeat",
  "status": "alive"
}
```

---

# 11. FRONTEND

## 11.1 Features

- User registration and login
- Order creation with multiple items
- Order list view with status
- Real-time status updates via WebSocket
- Responsive design

## 11.2 Access

The frontend is served by nginx at **http://localhost:8082**

---

# 12. DOCKER CONFIGURATION

## 12.1 Services

| Service | Image | Ports | Networks |
|---------|-------|-------|----------|
| nginx | nginx:alpine | 8082:80 | frontend |
| order-api | fastapi-order-api | 8000:8000 | frontend, backend |
| websocket-service | fastapi-websocket-service | 8001:8001 | frontend, backend |
| order-validator | fastapi-order-validator | - | backend |
| payment-processor | fastapi-payment-processor | - | backend |
| inventory-manager | fastapi-inventory-manager | - | backend |
| fulfillment | fastapi-fulfillment | - | backend |
| webhook-dispatcher | fastapi-webhook-dispatcher | - | backend |
| postgres | postgres:15-alpine | 5432:5432 | backend |
| redis | redis:7-alpine | 6379:6379 | backend |
| kafka | confluentinc/cp-kafka:7.5.0 | 9092:9092 | backend |
| zookeeper | confluentinc/cp-zookeeper:7.5.0 | 2181 | backend |

## 12.2 Volumes

- `postgres_data`: PostgreSQL data
- `redis_data`: Redis persistence
- `kafka_data`: Kafka data
- `zookeeper_data`: Zookeeper data

---

# 13. ENVIRONMENT VARIABLES

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://... | PostgreSQL connection |
| REDIS_URL | redis://redis:6379/0 | Redis connection |
| KAFKA_BOOTSTRAP_SERVERS | kafka:29092 | Kafka servers |
| JWT_SECRET_KEY | your-secret-key | JWT signing key |
| JWT_ALGORITHM | HS256 | JWT algorithm |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 15 | Token expiry |
| RATE_LIMIT_PER_MINUTE | 100 | API rate limit |

---

# 14. RUNNING THE PROJECT

## 14.1 Prerequisites

- Docker Desktop
- Docker Compose

## 14.2 Start All Services

```bash
# Start all containers
docker compose up -d

# View logs
docker compose logs -f

# Check status
docker compose ps
```

## 14.3 Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:8082 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| WebSocket | ws://localhost:8001 |

## 14.4 Using the Frontend

1. Open http://localhost:8082
2. Register a new account
3. Login with credentials
4. Create a new order
5. Watch real-time status updates

---

# 15. SECURITY

## 15.1 Authentication

- JWT tokens for API authentication
- Access tokens expire in 15 minutes
- Refresh tokens valid for 7 days

## 15.2 Rate Limiting

- Per-IP and per-user limits
- Different limits per endpoint:
  - Order creation: 20/min
  - Order retrieval: 100/min
  - Authentication: 10/min

## 15.3 Data Protection

- Passwords hashed with bcrypt
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy
- CORS enabled for all origins (dev)

---

# 16. API DOCUMENTATION

## 16.1 Interactive API Docs

Access the interactive API documentation at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 16.2 Example Usage

### Create Order with cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Use token to create order
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "items": [{"product_id": "prod-001", "quantity": 2, "unit_price": 29.99}],
    "total_amount": 59.98,
    "shipping_address": {"street": "123 Main St", "city": "NYC", "state": "NY", "zip": "10001"},
    "payment_method": "CREDIT_CARD"
  }'
```

---

# APPENDIX: FILE QUICK REFERENCE

| File | Purpose |
|------|---------|
| `docker-compose.yml` | All services configuration |
| `api/app/main.py` | FastAPI app entry point |
| `api/app/config.py` | Settings |
| `api/app/database.py` | Database connection |
| `api/app/models/order.py` | Order model |
| `api/app/schemas/order.py` | Order schemas |
| `api/app/routes/orders.py` | Order endpoints |
| `api/app/routes/auth.py` | Auth endpoints |
| `api/app/services/order_service.py` | Order business logic |
| `api/app/services/kafka_producer.py` | Kafka producer |
| `api/app/services/redis_service.py` | Redis operations |
| `services/websocket/main.py` | WebSocket service |
| `workers/common/kafka_consumer.py` | Kafka consumer base |
| `workers/order_validator/main.py` | Order validator |
| `workers/payment_processor/main.py` | Payment processor |
| `workers/inventory_manager/main.py` | Inventory manager |
| `workers/fulfillment/main.py` | Fulfillment worker |
| `frontend/index.html` | Frontend application |
| `docker/nginx/nginx.conf` | Nginx configuration |

---

**End of Documentation**
