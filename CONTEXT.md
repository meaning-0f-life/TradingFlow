# TradingFlow - Project Context

## 📋 Project Overview

**TradingFlow** is a visual workflow orchestration platform for financial market analysis and automated trading. It combines the visual node-based approach of n8n with advanced financial analysis capabilities inspired by TradingAgents, ai-hedge-fund, and other cutting-edge projects.

### Core Goals
- Provide a visual, no-code/low-code interface for building trading and analysis workflows
- Integrate multiple data sources (Yahoo Finance, Alpha Vantage, crypto exchanges, MT5)
- Support multiple LLM providers (OpenAI, Anthropic, OpenRouter, DeepSeek)
- Enable multi-agent systems for collaborative market analysis
- Ensure security through encrypted API key storage and JWT authentication
- Maintain extensibility for custom nodes and integrations

---

## 🏗️ Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)           │
│  • Visual workflow editor (React Flow)                     │
│  • Node configuration forms                                │
│  • Real-time execution monitoring (WebSocket)              │
│  • User dashboard & API key management                     │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTPS/REST + WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI - Python)                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer (app/api/)                                │  │
│  │  • auth.py      - Authentication (JWT)               │  │
│  │  • workflows.py - Workflow CRUD                     │  │
│  │  • execution.py - Workflow execution (background)   │  │
│  │  • keys.py      - API key management                │  │
│  │  • nodes.py     - Node type registry                │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Core Layer (app/core/)                              │  │
│  │  • engine.py    - WorkflowExecutor (async engine)   │  │
│  │  • database.py  - SQLAlchemy session management     │  │
│  │  • security.py  - JWT & password utils              │  │
│  │  • config.py    - Settings (Pydantic)               │  │
│  │  • websocket.py - Connection manager               │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Nodes Layer (app/nodes/)                            │  │
│  │  • base.py      - BaseNode abstract class           │  │
│  │  • llm_node.py  - LLM provider integration          │  │
│  │  • data_node.py - Market data fetchers              │  │
│  │  • __init__.py  - Node registry & discovery         │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services (app/services/)                            │  │
│  │  • encryption.py - API key encryption/decryption    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Models (app/models/)                                │  │
│  │  • user.py              - User account               │  │
│  │  • workflow.py          - Workflow definition        │  │
│  │  • workflow_execution.py - Execution history        │  │
│  │  • api_key.py           - Encrypted API keys        │  │
│  │  • schemas.py           - Pydantic schemas          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure (Docker Compose)               │
│  • PostgreSQL 15  - Primary database                      │
│  • Redis 7       - Cache & future Celery broker           │
│  • Qdrant        - Vector database for RAG                │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (async web framework)
- SQLAlchemy 2.0 (ORM)
- Pydantic v2 (validation)
- PostgreSQL (main database)
- Redis (caching & queues)
- Qdrant (vector storage)
- WebSockets (real-time updates)

**Frontend (planned):**
- React 18 + TypeScript
- React Flow (visual editor)
- Tailwind CSS (styling)
- Zustand (state management)

**Data & AI:**
- yfinance (Yahoo Finance data)
- alpha-vantage (technical indicators)
- ccxt (crypto exchanges)
- MetaTrader5 (forex/stocks)
- LangChain/LangGraph (multi-agent systems - future)
- OpenAI, Anthropic, OpenRouter, DeepSeek (LLM providers)

---

## 🗄️ Database Schema

### Core Tables

#### `users`
```sql
id (PK, integer)
email (varchar, unique)
username (varchar, unique)
hashed_password (varchar)
is_active (boolean, default true)
is_superuser (boolean, default false)
created_at (timestamp with time zone)
updated_at (timestamp with time zone)
```

#### `workflows`
```sql
id (PK, integer)
name (varchar, not null)
description (text, nullable)
owner_id (integer, FK → users.id)
is_active (boolean, default true)
config (jsonb)  -- Stores nodes, edges, and workflow structure
version (integer, default 1)
created_at (timestamp with time zone)
updated_at (timestamp with time zone)
```

#### `workflow_executions`
```sql
id (PK, integer)
workflow_id (integer, FK → workflows.id)
triggered_by (integer, FK → users.id)
status (varchar)  -- 'pending', 'running', 'completed', 'failed'
input_data (jsonb, default {})
result_data (jsonb, default {})  -- node results, execution order
error_message (text, nullable)
started_at (timestamp with time zone, default now())
completed_at (timestamp with time zone, nullable)
```

#### `api_keys`
```sql
id (PK, integer)
owner_id (integer, FK → users.id)
name (varchar, not null)  -- User-friendly name
service (enum: openai, anthropic, open_router, deepseek, alpha_vantage, yahoo_finance, binance, bybit, mt5, qdrant, redis, telegram)
encrypted_key (text, not null)  -- Encrypted API key
is_active (boolean, default true)
created_at (timestamp with time zone)
updated_at (timestamp with time zone)
```

**Note:** ForeignKey constraints are not yet implemented in the models but should be added in a future migration.

---

## 🔐 Security Implementation

### API Key Encryption
- **Algorithm:** Fernet (symmetric encryption)
- **Key Derivation:** SHA256 hash of master key
- **Storage:** All external API keys are encrypted at rest
- **Master Key:** Stored in `.env` as `ENCRYPTION_KEY`

### Authentication
- **Method:** JWT (JSON Web Tokens)
- **Algorithm:** HS256
- **Expiry:** Configurable (default 30 minutes)
- **Secret:** Stored in `.env` as `SECRET_KEY`

### Best Practices (to implement in production)
1. Change default secrets in `.env`
2. Use HTTPS only
3. Implement rate limiting
4. Add request logging & monitoring
5. Use HttpOnly cookies for JWT storage (not localStorage)
6. Implement CSRF protection
7. Add input validation on all endpoints

---

## 🔄 Workflow Execution Engine

### Execution Flow

1. **User triggers execution** via `POST /api/execution/run`
2. **Execution record created** with status `"running"`
3. **Background task started** using FastAPI `BackgroundTasks`
4. **WorkflowExecutor**:
   - Parses workflow config (nodes + edges)
   - Builds dependency graph
   - Validates for cycles
   - Executes nodes respecting dependencies
   - Uses semaphore for concurrency control (default max 10 concurrent)
   - Sends WebSocket updates for all events
5. **Results stored** in `workflow_executions.result_data`
6. **Status updated** to `"completed"` or `"failed"`

### Node Execution Model

- **Async:** All nodes execute asynchronously
- **Dependency-aware:** Nodes wait for upstream dependencies
- **Data flow:** Results passed through edges via `_gather_inputs()`
- **Error handling:** Configurable `fail_fast` mode (currently default `False`)
- **Concurrency:** Controlled by `max_concurrent` parameter

### WebSocket Updates

Clients connect to `WS /ws?client_id=execution_<id>` to receive:
- `node_started`: Node execution began
- `node_completed`: Node finished successfully
- `node_failed`: Node threw an error
- `completed`: Workflow finished
- `failed`: Workflow failed

---

## 🧩 Node System

### BaseNode Interface

All nodes must inherit from `BaseNode` and implement:

```python
class MyNode(BaseNode):
    display_name: str = "My Node"
    description: str = "Description"
    category: str = "general"

    async def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # inputs: data from connected nodes (keyed by port)
        # context: execution_id, db session, user_id
        # Returns: dict with output ports
        pass

    @classmethod
    def get_ui_schema(cls) -> Dict[str, Any]:
        # Returns JSON Schema for UI configuration
        # Includes parameters (config) and outputs
        pass
```

### Available Nodes

#### 1. LLMNode (`type: "llm"`)

**Providers:** OpenAI, Anthropic, OpenRouter, DeepSeek

**Config Parameters:**
- `provider`: Select from supported providers
- `model`: Model ID (dynamic based on provider)
- `temperature`: 0-2
- `max_tokens`: 1-4000
- `system_prompt`: Optional system message
- `user_prompt`: User message with `{{input.port_name}}` substitution

**Outputs:**
- `response`: Generated text
- `usage`: Token usage stats

**API Key:** Looks up encrypted key from `api_keys` table by service enum

#### 2. DataFetcherNode (`type: "data_fetcher"`)

**Sources:** Yahoo Finance, Alpha Vantage, Binance, Bybit, MetaTrader 5

**Key Features:**
- Multi-source data fetching
- Built-in caching (configurable TTL, default 1 hour)
- Technical indicators (Alpha Vantage)
- Financial statements (Yahoo Finance)
- Funding rates (Bybit futures)
- Symbol info (MT5)

**Config Parameters:**
- `source`: Data source
- `symbol`: Ticker/symbol
- `interval`: Candlestick interval
- `period`: Historical period (for Yahoo Finance)
- `start_date`/`end_date`: Custom date range
- `market_type`: spot/futures/options (crypto exchanges)
- `limit`: Max records to fetch
- `fetch_balance_sheet`, `fetch_cash_flow`, `fetch_income_stmt`: Financial statements flags
- `indicators`: List of technical indicators
- `indicator_interval`: Interval for indicators
- `mt5_symbol_info`: Fetch MT5 symbol details
- `cache_ttl`: Cache TTL in seconds

**Outputs:**
- `data`: OHLCV data array
- `latest_price`: Most recent price
- `info`: Asset information (Yahoo Finance)
- `balance_sheet`, `cash_flow`, `income_stmt`: Financial statements
- `indicators`: Technical indicator data
- `symbol_info`: MT5 symbol metadata
- `funding_rate`: Bybit funding rate

**Caching:** In-memory cache per node instance with MD5 key based on parameters

---

## 🔌 API Endpoints

### Authentication (`/api/auth`)
- `POST /register` - Create user account
- `POST /login` - Get JWT token
- `GET /me` - Current user info

### Workflows (`/api/workflows`)
- `GET /` - List user's workflows
- `POST /` - Create workflow
- `GET /{id}` - Get workflow details
- `PUT /{id}` - Update workflow (increments version)
- `DELETE /{id}` - Delete workflow

### Execution (`/api/execution`)
- `POST /run` - Start workflow (returns immediately, runs in background)
- `GET /executions` - List executions (optionally filter by workflow_id)
- `GET /executions/{id}` - Get execution details with results

### API Keys (`/api/keys`)
- `GET /` - List user's API keys (without values)
- `POST /` - Create new API key (encrypts before storage)
- `DELETE /{id}` - Delete API key
- `PUT /{id}/deactivate` - Soft-deactivate API key

### Nodes (`/api/nodes`)
- `GET /types` - Get all available node types with UI schemas

### WebSocket
- `WS /ws?client_id=execution_<id>` - Real-time execution updates

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# Database
POSTGRES_USER=tradingflow
POSTGRES_PASSWORD=change_this
POSTGRES_DB=tradingflow
DATABASE_URL=postgresql+psycopg2://tradingflow:change_this@localhost:5432/tradingflow

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=generate-a-very-long-random-string-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Vector DB (Qdrant)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=tradingflow_docs

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-encryption-key-here

# Celery (future)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Application
APP_NAME=TradingFlow
APP_URL=http://localhost:3000  # Used for OpenRouter headers
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### Docker Compose Services

```yaml
postgres:   # PostgreSQL 15 on port 5432
redis:      # Redis 7 on port 6379
qdrant:     # Qdrant vector DB on ports 6333 (HTTP) & 6334 (gRPC)
```

---

## 🚀 Current Implementation Status

### ✅ Completed (Phase 0 - Foundation)

- [x] Monorepo structure with backend/
- [x] FastAPI application setup with CORS
- [x] Database models (User, Workflow, WorkflowExecution, APIKey)
- [x] JWT authentication system
- [x] API key encryption service
- [x] Workflow CRUD endpoints
- [x] Execution endpoints with background tasks
- [x] WebSocket connection manager
- [x] Node registry system
- [x] LLMNode (OpenAI, Anthropic, OpenRouter, DeepSeek)
- [x] DataFetcherNode (Yahoo Finance, Alpha Vantage, Binance, Bybit, MT5)
- [x] Docker Compose with PostgreSQL, Redis, Qdrant
- [x] Environment configuration
- [x] Basic error handling & logging

### 🔄 In Progress / Partially Complete

- [ ] Multi-agent system (LangGraph integration) - not started
- [ ] RAG & vector database integration - infrastructure ready
- [ ] Trading execution nodes - infrastructure ready, needs implementation
- [ ] Backtesting engine - not started
- [ ] Frontend visual editor - not started

### ⚠️ Known Issues & Limitations

1. **ForeignKey constraints** not defined in SQLAlchemy models (should add)
2. **No Alembic migrations** - using `create_all()` (add migrations for production)
3. **LLMNode API key lookup** - only fetches first active key, not per-user in all cases
4. **DataFetcherNode cache** - in-memory only, not shared across instances (use Redis in future)
5. **WebSocket subscription model** - simple client_id matching, no channel subscriptions
6. **No rate limiting** on API endpoints
7. **No request validation** beyond Pydantic schemas
8. **Background tasks** use FastAPI's simple system, not Celery (scales poorly)
9. **Node execution** doesn't persist intermediate results to DB (only in memory)
10. **No user isolation** in some API key lookups (should filter by current_user.id)

---

## 📝 Key Design Decisions

### 1. Why FastAPI?
- Native async support for high concurrency
- Automatic OpenAPI docs
- Pydantic integration for validation
- Good performance for I/O-bound operations

### 2. Why BackgroundTasks instead of Celery?
- Simpler setup for MVP
- No external dependencies beyond Redis
- Adequate for low-to-medium load
- **Future:** Migrate to Celery/ARQ for production scaling

### 3. Why In-Memory Node Cache?
- Simplicity for single-instance deployments
- **Future:** Use Redis for distributed caching

### 4. Why Fernet for Encryption?
- Simple API
- Authenticated encryption (AEAD)
- No need to manage IVs separately
- Key derivation via SHA256 is sufficient for our threat model

### 5. Why JSONB for Workflow Config?
- Flexible schema for arbitrary node/edge structures
- PostgreSQL JSONB supports indexing and querying
- Easy to evolve without migrations

---

## 🔧 Development Setup

### Prerequisites
- Python 3.9+ (tested with 3.9)
- Docker & Docker Compose
- pip (or pip3)

### Local Setup

```bash
# 1. Clone & install
cd TradingFlow
cd backend
pip3 install -r requirements.txt

# 2. Configure environment
cp ../.env.example ../.env
# Edit .env and set strong SECRET_KEY and ENCRYPTION_KEY

# 3. Start infrastructure
cd ..
docker-compose up -d

# 4. Initialize database (optional - auto-created on startup)
# Tables are created automatically by FastAPI lifespan

# 5. Run backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
cd backend
python3 test_simple.py
```

This tests:
- Database connection & table creation
- Node registry
- Encryption service
- Workflow executor instantiation

---

## 📚 API Usage Examples

### 1. Register & Login

```bash
# Register
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"testuser","password":"mypassword"}'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"mypassword"}'
# Returns: {"access_token": "...", "token_type": "bearer"}
```

### 2. Add API Key

```bash
curl -X POST "http://localhost:8000/api/keys/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"OpenAI Key","service":"openai","key":"sk-..."}'
```

### 3. Create Workflow

```bash
curl -X POST "http://localhost:8000/api/workflows/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "Fetch AAPL data and analyze with GPT",
    "config": {
      "nodes": [
        {
          "id": "node1",
          "type": "data_fetcher",
          "name": "Get AAPL Price",
          "config": {
            "source": "yahoo_finance",
            "symbol": "AAPL",
            "period": "1mo"
          }
        },
        {
          "id": "node2",
          "type": "llm",
          "name": "Analyze with GPT",
          "config": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "user_prompt": "Analyze this stock data: {{input.data}}"
          }
        }
      ],
      "edges": [
        {"source": "node1", "target": "node2"}
      ]
    }
  }'
```

### 4. Execute Workflow

```bash
curl -X POST "http://localhost:8000/api/execution/run" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": 1, "input_data": {}}'
# Returns immediately with execution record (status: "running")
```

### 5. Check Execution Status

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/execution/executions/1"
```

### 6. WebSocket Connection

```javascript
// Connect to WebSocket for execution updates
const ws = new WebSocket(`ws://localhost:8000/ws?client_id=execution_1`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

---

## 🎯 Roadmap & Future Work

### Phase 1: Core Infrastructure (✅ Complete)
- [x] Basic node system
- [x] Workflow execution engine
- [x] LLM & Data nodes
- [x] Authentication & API key management

### Phase 2: Multi-Agent System (Next)
- [ ] Integrate LangGraph for agent orchestration
- [ ] Create AgentNode with configurable agent roles
- [ ] Implement debate/consensus mechanisms
- [ ] Add agent-specific tools (research, analysis, risk assessment)
- [ ] Build agent visualizer in UI

### Phase 3: RAG & Knowledge Management
- [ ] Qdrant vector database integration
- [ ] Document ingestion nodes (PDF, CSV, text)
- [ ] Text chunking & embedding
- [ ] Retrieval nodes with similarity search
- [ ] Knowledge base management UI

### Phase 4: Trading Execution
- [ ] TradingNode with broker integrations
- [ ] Order management (Binance, Bybit, MT5)
- [ ] Portfolio tracking
- [ ] Risk management rules
- [ ] Paper trading mode
- [ ] Trade confirmation workflow

### Phase 5: Backtesting
- [ ] Historical data caching
- [ ] BacktestNode with performance metrics
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulations
- [ ] Performance dashboard

### Phase 6: Frontend Visual Editor
- [ ] React Flow integration
- [ ] Node palette & drag-and-drop
- [ ] Dynamic form generation from node schemas
- [ ] Real-time execution visualization
- [ ] Workflow template library

### Phase 7: Advanced Features
- [ ] Plugin system for custom nodes
- [ ] Workflow scheduling & triggers
- [ ] Alerting & notifications
- [ ] Advanced analytics dashboards
- [ ] Team collaboration features
- [ ] Marketplace for node templates

---

## 🧪 Testing Strategy

### Unit Tests
- Node implementations (each node type)
- Encryption service
- Database models
- Utility functions

### Integration Tests
- Workflow execution end-to-end
- API endpoints
- Database transactions
- WebSocket communication

### Manual Testing Checklist
- [ ] User registration/login
- [ ] API key creation/encryption/decryption
- [ ] Workflow creation with various node combinations
- [ ] Execution with LLM node (requires API key)
- [ ] Execution with DataFetcher node (Yahoo Finance)
- [ ] WebSocket updates during execution
- [ ] Error handling (invalid workflow, missing API key, etc.)

---

## 🔐 Security Considerations

### Implemented
- Encrypted API key storage
- JWT authentication
- Password hashing with bcrypt
- CORS configuration
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)

### Needed for Production
1. **Rate limiting** - Prevent abuse
2. **Request logging** - Audit trail
3. **HTTPS enforcement** - TLS everywhere
4. **Secure JWT storage** - HttpOnly cookies, not localStorage
5. **CSRF protection** - For state-changing operations
6. **API key rotation** - Allow users to rotate keys
7. **Secret management** - Use Vault or AWS Secrets Manager
8. **Database connection pooling** - Already in SQLAlchemy but tune for production
9. **Backup & recovery** - Database backups
10. **Penetration testing** - Security audit

---

## 📦 Dependencies

### Core (requirements.txt)
- fastapi - Web framework
- uvicorn[standard] - ASGI server
- pydantic, pydantic-settings - Validation & config
- sqlalchemy - ORM
- psycopg2-binary - PostgreSQL driver
- python-jose[cryptography] - JWT
- passlib[bcrypt] - Password hashing
- python-multipart - Form parsing
- websockets - WebSocket support
- redis - Redis client
- cryptography - Encryption
- pandas, numpy - Data processing

### Optional (install as needed)
- yfinance - Yahoo Finance data
- alpha-vantage - Alpha Vantage API
- ccxt - Crypto exchanges
- MetaTrader5 - MT5 integration
- openai - OpenAI API
- anthropic - Anthropic API
- langchain, langgraph - Multi-agent systems (future)

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'jose'"
**Fix:** Install `python-jose[cryptography]` (not just `jose`)

### "ImportError: cannot import name 'PBKDF2'"
**Fix:** Use `from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2` - already fixed in current code

### Database connection errors
**Check:**
- PostgreSQL is running: `docker-compose ps`
- `.env` has correct `DATABASE_URL`
- Port 5432 is not blocked

### WebSocket not connecting
**Check:**
- Client uses correct `client_id` format: `execution_<id>`
- CORS allows WebSocket origin
- Server is running

### LLM node fails with "No API key found"
**Fix:**
1. Add API key via `POST /api/keys/`
2. Ensure `service` matches provider (e.g., `openai` for OpenAI)
3. Check that key is active (`is_active: true`)

### DataFetcher node fails for crypto exchanges
**Check:**
- CCXT package is installed: `pip install ccxt`
- Symbol format is correct (e.g., `BTC/USDT` not `BTCUSDT`)
- Interval is supported by exchange

---

## 📖 References & Inspirations

1. **n8n** - Workflow automation platform
   - Node-based visual editor
   - 400+ integrations
   - https://github.com/n8n-io/n8n

2. **TradingAgents** - Multi-agent trading system
   - LangGraph for agent orchestration
   - Role-based agent teams
   - Dynamic debates between agents
   - https://github.com/TauricResearch/TradingAgents

3. **ai-hedge-fund** - AI-powered investing
   - Agent profiles (Buffett, Ackman styles)
   - Analysis types (valuation, sentiment, technicals)
   - Backtesting integration
   - https://github.com/virattt/ai-hedge-fund

4. **ContestTrade** - Agent competition framework
   - Internal contest mechanism
   - "Textual factors" for news transformation
   - Customizable beliefs for researchers
   - https://github.com/FinStep-AI/ContestTrade

5. **TradingGoose** - Full-stack trading platform
   - React + Tailwind frontend
   - Alpaca integration
   - Portfolio management
   - RBAC with Supabase
   - https://github.com/TradingGoose/TradingGoose.github.io

---

## 📄 License

MIT License - see LICENSE file

---

## ⚠️ Disclaimer

This software is for educational and research purposes only. Not financial advice. Use at your own risk. Authors not responsible for any financial losses.