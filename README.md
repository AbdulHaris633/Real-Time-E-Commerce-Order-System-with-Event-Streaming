# 🛒 Real-Time E-Commerce Order System
### with Event Streaming Architecture

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-green)](https://fastapi.tiangolo.com)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-3.5-red)](https://kafka.apache.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 📋 Overview

A **scalable, real-time e-commerce order processing system** built with:
- ⚡ **FastAPI** — high-performance async REST API
- 📨 **Apache Kafka** — distributed event streaming
- 🔄 **WebSockets** — real-time order status updates
- 🛡️ **Rate Limiting** — multi-tier protection with Redis
- 🐳 **Docker** — full containerized deployment
- 🗄️ **PostgreSQL** — primary database
- ⚡ **Redis** — caching, rate limiting, pub/sub

---

## 🏗️ Architecture

```
Internet → [Nginx Gateway :80]
               ↓
       [FastAPI Order API :8000]
               ↓ publishes events
       [Apache Kafka :9092]
         ↙    ↓    ↘    ↓
  [Validator][Payment][Inventory][Fulfillment]
               ↓
       [WebSocket Service :8001]  ← real-time push to clients
               ↓
       [Webhook Dispatcher]       ← HTTP delivery to external systems
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone & Configure
```bash
git clone https://github.com/AbdulHaris633/Real-Time-E-Commerce-Order-System-with-Event-Streaming.git
cd Real-Time-E-Commerce-Order-System-with-Event-Streaming

# Copy environment config
cp .env.example .env
# Edit .env with your JWT secret and other settings
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Verify Services
```bash
docker-compose ps
curl http://localhost:8000/health
curl http://localhost/docs         # Swagger UI via Nginx
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/api/v1/auth/register` | Register user | 10/min |
| `POST` | `/api/v1/auth/login` | Get JWT token | 20/min |
| `POST` | `/api/v1/orders/` | Create order | 20/min |
| `GET` | `/api/v1/orders/` | List orders | 100/min |
| `GET` | `/api/v1/orders/{id}` | Get order | 100/min |
| `PATCH` | `/api/v1/orders/{id}` | Update status | 20/min |
| `DELETE` | `/api/v1/orders/{id}` | Cancel order | 20/min |
| `POST` | `/api/v1/webhooks/` | Register webhook | 10/hour |
| `WS` | `/ws/orders/{user_id}` | Real-time updates | 5 concurrent |

**Interactive Docs:** http://localhost:8000/docs

---

## 🔄 Event Flow

```
1. POST /api/v1/orders  →  order_created (Kafka)
2. OrderValidator        →  order_validated (Kafka)
3. PaymentProcessor      →  order_payment_processed (Kafka)
4. InventoryManager      →  order_fulfilled (Kafka)
5. Fulfillment           →  order_shipped (Kafka)
6. WebSocket Service     →  Real-time push to client
7. Webhook Dispatcher    →  HTTP POST to registered URLs
```

---

## 🐳 Docker Services

| Service | Container | Port |
|---------|-----------|------|
| Nginx Gateway | orders_nginx | 80 |
| Order API | orders_api | 8000 |
| WebSocket | orders_websocket | 8001 |
| Order Validator | orders_validator_worker | - |
| Payment Processor | orders_payment_worker | - |
| Inventory Manager | orders_inventory_worker | - |
| Fulfillment | orders_fulfillment_worker | - |
| Webhook Dispatcher | orders_webhook_dispatcher | - |
| PostgreSQL | orders_postgres | 5432 |
| Redis | orders_redis | 6379 |
| Kafka | orders_kafka | 9092 |
| Zookeeper | orders_zookeeper | 2181 |

---

## 🛡️ Rate Limiting Tiers

| Tier | Limit |
|------|-------|
| Free | 50 req/min |
| Standard | 100 req/min |
| Premium | 500 req/min |
| Enterprise | Unlimited |

Headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 🔌 WebSocket Usage

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/orders/{your_user_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Order update:', data);
  // { type: "order.update", order_id: "...", status: "shipped", message: "..." }
};

// Heartbeat
setInterval(() => ws.send('ping'), 25000);
```

---

## 🪝 Webhook Verification

```python
import hmac, hashlib

def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## 📁 Project Structure

```
ecommerce-order-system/
├── api/                    # FastAPI application
│   ├── app/
│   │   ├── main.py         # App entry point
│   │   ├── config.py       # Settings
│   │   ├── database.py     # DB connection
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── utils/          # Helpers
│   └── tests/              # Test suite
├── workers/                # Kafka consumers
│   ├── order_validator/
│   ├── payment_processor/
│   ├── inventory_manager/
│   └── fulfillment/
├── services/               # Microservices
│   ├── websocket/          # Real-time updates
│   └── webhook_dispatcher/ # HTTP delivery
├── docker/                 # Docker configs
│   ├── nginx/nginx.conf
│   └── kafka/init.sql
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🧪 Running Tests

```bash
cd api
pip install -r requirements.txt
pytest tests/ -v --cov=app
```

---

## 📈 Performance Targets

| Metric | Target |
|--------|--------|
| API p95 response time | < 200ms |
| Rate limiting overhead | < 5ms |
| WebSocket latency | < 100ms |
| Kafka throughput | 10,000+ msg/sec |
| Concurrent WebSockets | 50,000+ |

---

## 📄 Documentation

- 📋 [PRD.md](PRD.md) — Product Requirements
- 🛠️ [Implementation_Guide.md](Implementation_Guide.md) — Step-by-step guide
- 📐 [Technical_Architecture.md](Technical_Architecture.md) — Full technical spec

---

**Built with ❤️ | Version 1.0.0 | February 2026**
