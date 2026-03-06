# TradingFlow API - Administration Guide

Complete guide for using the TradingFlow API for administrators and developers.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Users](#users)
4. [Workflows](#workflows)
5. [Execution](#execution)
6. [Nodes](#nodes)
7. [API Keys](#api-keys)
8. [WebSocket](#websocket)
9. [Usage Examples](#usage-examples)

---

## Quick Start

### Start the server

```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### API Documentation

- **Swagger UI (interactive):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

---

## Authentication

TradingFlow uses JWT (JSON Web Tokens) for authentication.

### 1. Register a new user

**Endpoint:** `POST /api/auth/register`

**Request body (JSON):**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "your_password"
}
```

**Curl example:**
```bash
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"myuser","password":"mypassword123"}'
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "myuser",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-03-02T10:00:00.000000Z"
}
```

### 2. Login (get token)

**Endpoint:** `POST /api/auth/login`

**Request body (JSON):**
```json
{
  "username": "username",
  "password": "password"
}
```

**Curl example:**
```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"mypassword123"}'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save the token for subsequent requests:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"myuser","password":"mypassword123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### 3. Get current user info

**Endpoint:** `GET /api/auth/me`

**Headers:** `Authorization: Bearer <your_token>`

**Curl example:**
```bash
curl -s -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "myuser",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2026-03-02T10:00:00.000000Z"
}
```

---

## Users

### Get user list

**Endpoint:** `GET /api/auth/users` (superusers only)

**Headers:** `Authorization: Bearer <superuser_token>`

**Curl example:**
```bash
curl -s -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer $TOKEN"
```

---

## Workflows

Workflows are the main objects containing the visual node graph representation.

### 1. Get workflows list

**Endpoint:** `GET /api/workflows/`

**Query parameters:**
- `skip` (optional): number of records to skip (default 0)
- `limit` (optional): maximum number of records (default 100)

**Curl example:**
```bash
curl -s -X GET "http://localhost:8000/api/workflows/?skip=0&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "My First Workflow",
    "description": "Apple stock analysis",
    "owner_id": 1,
    "is_active": true,
    "config": {
      "nodes": [...],
      "edges": [...]
    },
    "version": 1,
    "created_at": "2026-03-02T10:00:00.000000Z",
    "updated_at": null
  }
]
```

### 2. Create new workflow

**Endpoint:** `POST /api/workflows/`

**Request body (JSON):**
```json
{
  "name": "Workflow Name",
  "description": "Description (optional)",
  "config": {
    "nodes": [],
    "edges": []
  }
}
```

**Curl example:**
```bash
curl -s -X POST http://localhost:8000/api/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "A test workflow",
    "config": {
      "nodes": [],
      "edges": []
    }
  }'
```

**Response:**
```json
{
  "id": 2,
  "name": "Test Workflow",
  "description": "A test workflow",
  "owner_id": 1,
  "is_active": true,
  "config": {
    "nodes": [],
    "edges": []
  },
  "version": 1,
  "created_at": "2026-03-02T10:05:00.000000Z",
  "updated_at": null
}
```

### 3. Get specific workflow

**Endpoint:** `GET /api/workflows/{workflow_id}`

**Curl example:**
```bash
curl -s -X GET http://localhost:8000/api/workflows/2 \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Update workflow

**Endpoint:** `PUT /api/workflows/{workflow_id}`

**Request body (JSON) - only include fields to update:**
```json
{
  "name": "New Name",
  "config": {
    "nodes": [...],
    "edges": [...]
  }
}
```

**Curl example:**
```bash
curl -s -X PUT http://localhost:8000/api/workflows/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Workflow",
    "config": {
      "nodes": [
        {
          "id": "node1",
          "type": "llm",
          "position": {"x": 100, "y": 100},
          "data": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000,
            "system_prompt": "You are a helpful assistant",
            "user_prompt": "Hello!"
          }
        }
      ],
      "edges": []
    }
  }'
```

### 5. Delete workflow

**Endpoint:** `DELETE /api/workflows/{workflow_id}`

**Curl example:**
```bash
curl -s -X DELETE http://localhost:8000/api/workflows/2 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Execution

### Run a workflow

**Endpoint:** `POST /api/execution/run`

**Request body (JSON):**
```json
{
  "workflow_id": 1,
  "input_data": {}
}
```

**Curl example:**
```bash
curl -s -X POST http://localhost:8000/api/execution/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": 2,
    "input_data": {}
  }'
```

**Response (immediate, runs in background):**
```json
{
  "id": 5,
  "workflow_id": 2,
  "triggered_by": 1,
  "status": "running",
  "input_data": {},
  "result_data": {},
  "error_message": null,
  "started_at": "2026-03-02T10:10:00.000000Z",
  "completed_at": null
}
```

### Get executions list

**Endpoint:** `GET /api/execution/executions`

**Query parameters:**
- `workflow_id` (optional): filter by specific workflow
- `skip` (optional): pagination
- `limit` (optional): pagination

**Curl example:**
```bash
curl -s -X GET "http://localhost:8000/api/execution/executions?workflow_id=2&skip=0&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "id": 5,
    "workflow_id": 2,
    "triggered_by": 1,
    "status": "completed",
    "input_data": {},
    "result_data": {
      "node_results": {
        "node1": {
          "response": "Hello! I'm doing well, thank you for asking!",
          "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
        }
      },
      "execution_order": ["node1"],
      "errors": []
    },
    "error_message": null,
    "started_at": "2026-03-02T10:10:00.000000Z",
    "completed_at": "2026-03-02T10:10:05.000000Z"
  }
]
```

### Get specific execution

**Endpoint:** `GET /api/execution/executions/{execution_id}`

**Curl example:**
```bash
curl -s -X GET http://localhost:8000/api/execution/executions/5 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Nodes

### Get available node types

**Endpoint:** `GET /api/nodes/types`

**Curl example:**
```bash
curl -s -X GET http://localhost:8000/api/nodes/types \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "llm": {
    "name": "llm",
    "display_name": "LLM Call",
    "description": "Call an LLM model (OpenAI, Anthropic, OpenRouter, DeepSeek, etc.)",
    "category": "ai",
    "ui_schema": {
      "parameters": [
        {
          "name": "provider",
          "type": "select",
          "title": "Provider",
          "default": "openai",
          "options": [
            {"value": "openai", "label": "Openai"},
            {"value": "anthropic", "label": "Anthropic"},
            {"value": "openrouter", "label": "Openrouter"},
            {"value": "deepseek", "label": "Deepseek"}
          ],
          "description": "LLM provider to use"
        },
        {
          "name": "model",
          "type": "select",
          "title": "Model",
          "default": "gpt-4",
          "options": [...],
          "description": "Model to use"
        },
        {
          "name": "temperature",
          "type": "number",
          "title": "Temperature",
          "default": 0.7,
          "minimum": 0,
          "maximum": 2,
          "step": 0.1,
          "description": "Controls randomness"
        },
        {
          "name": "max_tokens",
          "type": "number",
          "title": "Max Tokens",
          "default": 1000,
          "minimum": 1,
          "maximum": 4000,
          "description": "Maximum tokens in response"
        },
        {
          "name": "system_prompt",
          "type": "textarea",
          "title": "System Prompt",
          "default": "",
          "description": "System prompt to set context"
        },
        {
          "name": "user_prompt",
          "type": "textarea",
          "title": "User Prompt",
          "default": "",
          "description": "User prompt. Use {{input.port_name}} to insert data from connected nodes"
        }
      ],
      "outputs": [
        {"name": "response", "type": "string", "description": "LLM response text"},
        {"name": "usage", "type": "object", "description": "Token usage statistics"}
      ]
    }
  },
  "data_fetcher": {
    "name": "data_fetcher",
    "display_name": "Data Fetcher",
    "description": "Fetch financial data from Yahoo Finance, Alpha Vantage, Binance, Bybit, MetaTrader5",
    "category": "data",
    "ui_schema": { ... }
  }
}
```

---

## API Keys

Manage API keys for external services (OpenAI, Alpha Vantage, etc.). Keys are encrypted at rest.

### 1. Get API keys list

**Endpoint:** `GET /api/keys/`

**Curl example:**
```bash
curl -s -X GET http://localhost:8000/api/keys/ \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "OpenAI API Key",
    "service": "openai",
    "is_active": true,
    "created_at": "2026-03-02T10:00:00.000000Z"
  }
]
```

### 2. Create API key

**Endpoint:** `POST /api/keys/`

**Request body (JSON):**
```json
{
  "name": "My OpenAI Key",
  "service": "openai",
  "key": "sk-..."
}
```

**Curl example:**
```bash
curl -s -X POST http://localhost:8000/api/keys/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI API Key",
    "service": "openai",
    "key": "sk-your-actual-api-key-here"
  }'
```

**Response:**
```json
{
  "id": 1,
  "name": "OpenAI API Key",
  "service": "openai",
  "is_active": true,
  "created_at": "2026-03-02T10:00:00.000000Z"
}
```

**Available services:**
- `openai`
- `anthropic`
- `open_router`
- `deepseek`
- `alpha_vantage`
- `yahoo_finance`
- `binance`
- `bybit`
- `mt5`
- `qdrant`
- `redis`
- `telegram`

### 3. Deactivate API key

**Endpoint:** `PUT /api/keys/{key_id}/deactivate`

**Curl example:**
```bash
curl -s -X PUT http://localhost:8000/api/keys/1/deactivate \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Delete API key

**Endpoint:** `DELETE /api/keys/{key_id}`

**Curl example:**
```bash
curl -s -X DELETE http://localhost:8000/api/keys/1 \
  -H "Authorization: Bearer $TOKEN"
```

---

## WebSocket

Use WebSocket for real-time workflow execution updates with subscription-based model.

**Endpoint:** `WS /ws`

**Connection flow:**
1. Connect to the WebSocket endpoint (no client_id required)
2. Send `subscribe` message for specific execution IDs you want to monitor
3. Receive `execution_update` messages for subscribed executions
4. Send `unsubscribe` message to stop receiving updates

**Connection example (JavaScript):**
```javascript
// Connect to global WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');
  
  // Subscribe to execution 5
  ws.send(JSON.stringify({
    type: 'subscribe',
    execution_id: 5
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
  // data.type = "execution_update"
  // data.execution_id = 5
  // data.data = { ... }
};

// Unsubscribe when done
ws.send(JSON.stringify({
  type: 'unsubscribe',
  execution_id: 5
}));
```

**Client messages:**
- `subscribe`: Subscribe to updates for a specific execution ID
- `unsubscribe`: Unsubscribe from execution updates

**Server message types:**
- `execution_update`: Workflow execution update (node_started, node_completed, node_failed, completed, failed)
- `pong`: Ping response

**Subscription model:**
- Single WebSocket connection can subscribe to multiple executions
- Server tracks client subscriptions per execution
- Updates are only sent to clients subscribed to that execution
- When client disconnects, all subscriptions are automatically cleaned up

---

## Usage Examples

### Full cycle: create and run a workflow

```bash
# 1. Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@demo.com","username":"demo","password":"demo123"}'

# 2. Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"

# 3. Create workflow with LLM node
WORKFLOW=$(curl -s -X POST http://localhost:8000/api/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LLM Analysis",
    "description": "Simple LLM test",
    "config": {
      "nodes": [
        {
          "id": "llm_node_1",
          "type": "llm",
          "position": {"x": 100, "y": 100},
          "data": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 500,
            "system_prompt": "You are a financial analyst",
            "user_prompt": "Analyze this: {{input.data}}"
          }
        }
      ],
      "edges": []
    }
  }')

WORKFLOW_ID=$(echo $WORKFLOW | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Workflow ID: $WORKFLOW_ID"

# 4. Run workflow
curl -s -X POST http://localhost:8000/api/execution/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"workflow_id\": $WORKFLOW_ID, \"input_data\": {\"data\": \"AAPL stock performance\"}}"

# 5. Check execution status
sleep 2
curl -s -X GET "http://localhost:8000/api/execution/executions?workflow_id=$WORKFLOW_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### Working with Data Fetcher

```bash
# Create workflow to fetch Yahoo Finance data
curl -X POST http://localhost:8000/api/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Stock Data Fetcher",
    "config": {
      "nodes": [
        {
          "id": "data_1",
          "type": "data_fetcher",
          "position": {"x": 100, "y": 100},
          "data": {
            "source": "yahoo_finance",
            "symbol": "AAPL",
            "interval": "1d",
            "period": "1mo"
          }
        }
      ],
      "edges": []
    }
  }'
```

---

## Execution Statuses

- `pending` - job created but not started
- `running` - currently executing
- `completed` - successfully finished
- `failed` - error occurred

---

## Error Handling

API returns standard HTTP error codes:

- `400 Bad Request` - invalid request parameters
- `401 Unauthorized` - missing or invalid token
- `403 Forbidden` - insufficient permissions
- `404 Not Found` - resource not found
- `422 Unprocessable Entity` - data validation error
- `500 Internal Server Error` - internal server error

**Error response example:**
```json
{
  "detail": "Workflow not found"
}
```

---

## Pagination

For paginated endpoints, use:
- `skip` - number of records to skip
- `limit` - maximum number of records

**Example:**
```bash
curl -s -X GET "http://localhost:8000/api/workflows/?skip=20&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## CORS

Backend is configured to work with frontend on these domains:
- http://localhost:3000
- http://localhost:5173
- http://127.0.0.1:3000
- http://127.0.0.1:5173

Configure CORS in [`backend/app/core/config.py`](backend/app/core/config.py:16).

---

## Environment Variables

Key settings in `.env` file:

```bash
# Database
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption (for API keys)
ENCRYPTION_KEY=your-encryption-key

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=tradingflow_docs

# Application
APP_URL=http://localhost:3000
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

---

## Monitoring and Logs

### Health check
```bash
curl http://localhost:8000/health
```
Response: `{"status":"healthy"}`

### Backend logs
Logs are printed to console in `--reload` mode. For production:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
```

### Docker container logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs postgres
docker-compose logs redis
docker-compose logs qdrant

# tail -f
docker-compose logs -f
```

---

## Testing the API

### Quick health check

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Get OpenAPI schema
curl http://localhost:8000/openapi.json | python3 -m json.tool | head -50

# 3. Check endpoints without auth
curl -I http://localhost:8000/docs
curl -I http://localhost:8000/redoc
```

### Full test with registration

```bash
# Clean up test user (if needed)
# (execute through DB or API if endpoint exists)

# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testadmin","password":"TestPass123!"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testadmin","password":"TestPass123!"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Verify token
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me | python3 -m json.tool

# Get node types
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/nodes/types | python3 -m json.tool

# Create workflow
curl -X POST http://localhost:8000/api/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","config":{"nodes":[],"edges":[]}}' | python3 -m json.tool
```

---

## Troubleshooting

### Backend won't start

1. Check dependencies:
```bash
cd backend
pip3 install -r requirements.txt
```

2. Check if port 8000 is free:
```bash
lsof -ti:8000
```

3. Check environment variables:
```bash
python3 -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### Database connection error

1. Ensure PostgreSQL is running:
```bash
docker-compose ps postgres
```

2. Check logs:
```bash
docker-compose logs postgres
```

3. Check `.env` settings:
```bash
cat .env | grep DATABASE_URL
```

### 401 Unauthorized error

1. Verify token is passed correctly:
```bash
curl -v -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

2. Check token hasn't expired (default 30 minutes)

3. Re-login for a new token

### WebSocket won't connect

1. Check backend is running
2. Use correct URL: `ws://localhost:8000/ws?client_id=xxx`
3. Check CORS settings in config

---

## Performance

### Recommendations

1. **Use connection pooling** - already configured in SQLAlchemy
2. **Caching** - Redis is configured, use for frequent queries
3. **Pagination** - always use `limit` for large lists
4. **Database** - monitor PostgreSQL size and performance
5. **WebSocket** - use for real-time instead of polling

### Monitoring

```bash
# Database size
docker-compose exec postgres psql -U tradingflow -d tradingflow -c "\l+"

# Redis stats
docker-compose exec redis redis-cli info stats

# Qdrant stats
curl http://localhost:6333/dashboard/collections
```

---

## Security

### Production recommendations

1. **Change SECRET_KEY and ENCRYPTION_KEY** in `.env`:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2. **Enable HTTPS** (configure Nginx/Traefik reverse proxy)

3. **Use HttpOnly cookies** for JWT (configure in FastAPI)

4. **Enable rate limiting** (e.g., with `slowapi`)

5. **Configure CORS** only for trusted domains

6. **Regularly update dependencies**

7. **Enable file logging**

8. **Set up database backups**

---

## Additional Resources

- **FastAPI documentation:** https://fastapi.tiangolo.com
- **SQLAlchemy documentation:** https://docs.sqlalchemy.org
- **React Flow documentation:** https://reactflow.dev
- **Zustand documentation:** https://zustand-demo.pmnd.rs

---

## Support

For questions or issues:
1. Check backend logs: `docker-compose logs backend`
2. Check Swagger UI: http://localhost:8000/docs
3. Create an issue in the project repository

---

**Document version:** 1.0  
**Last updated:** 2026-03-02  
**API version:** v0.1.0
