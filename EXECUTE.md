# TradingFlow - Run and Manage

Detailed guide for running and managing TradingFlow locally.

## 📋 Requirements

### General
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Git

### Backend dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Frontend dependencies
```bash
cd frontend
npm install
```

## 🗄️ Infrastructure (PostgreSQL, Redis, Qdrant)

Start infrastructure services through Docker Compose:

```bash
docker-compose up -d
```

Check status:
```bash
docker-compose ps
```

Stop:
```bash
docker-compose down
```

**Note**: If you already have PostgreSQL/Redis/Qdrant running on the same ports, you can start only necessary services or change ports in `docker-compose.yml`.

## 🚀 Starting Backend

1. **Configure environment variables** (if needed):
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

2. **Start the server**:
   ```bash
   cd backend
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Or use `uvicorn` directly:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```

3. **Verify backend is running**:
   - API docs: http://localhost:8000/docs
   - Health check: http://localhost:8000/health
   - API: http://localhost:8000/api

4. **Stop backend**:
   - Press `Ctrl+C` in the terminal where the server is running
   - Or find and kill the process:
     ```bash
     pkill -f "uvicorn app.main:app"
     ```

## 🎨 Starting Frontend

1. **Start dev server**:
   ```bash
   cd frontend
   npm run dev
   ```

   Server will be available at: http://localhost:3000

2. **Build for production** (optional):
   ```bash
   cd frontend
   npm run build
   ```

   Built files will be in `frontend/dist/`

3. **Stop frontend**:
   - Press `Ctrl+C` in the terminal where the dev server is running
   - Or find the process (usually `vite` or `node`) and kill it

## 🔄 Full Startup Process

### Starting from scratch:

```bash
# 1. Start infrastructure (in separate terminal)
docker-compose up -d

# 2. Start backend (in separate terminal)
cd backend
python3 -m uvicorn app.main:app --reload --port 8000

# 3. Start frontend (in separate terminal)
cd frontend
npm run dev
```

### Verification:

1. Open http://localhost:8000/docs - should see Swagger UI
2. Open http://localhost:3000 - frontend should load
3. Register a new user through the interface
4. Create a workflow and run it

## 🛑 Stopping All Services

### Quick stop:

```bash
# Stop backend
pkill -f "uvicorn app.main:app"

# Stop frontend (find Vite process)
pkill -f "vite"

# Stop Docker services
docker-compose down
```

### Full cleanup (including volumes):

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove built images (optional)
docker system prune -a
```

## 🔧 Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'email_validator'`
```bash
cd backend
pip install email-validator
```

**Error**: `ModuleNotFoundError: No module named 'passlib'`
```bash
cd backend
pip install passlib[bcrypt]
```

**Error**: Database connection failed
- Ensure PostgreSQL is running: `docker-compose ps`
- Check settings in `.env` (DATABASE_URL)
- Check if port 5432 is free

### Frontend won't start

**Error**: `tsc: command not found`
```bash
cd frontend
npm install
```

**Error**: Cannot find module 'react' or other dependencies
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Error**: Proxy errors (cannot connect to backend)
- Ensure backend is running on port 8000
- Check proxy settings in `frontend/vite.config.ts`

### Docker services won't start

```bash
# Check Docker Desktop is running
docker --version
docker-compose --version

# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache
docker-compose up -d
```

## 📝 Environment Configuration

### .env file settings

```bash
# Database
DATABASE_URL=postgresql+psycopg2://tradingflow:tradingflow@localhost:5433/tradingflow

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production-make-it-long-and-random-at-least-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Qdrant (Vector Database)
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=tradingflow_docs

# Encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-encryption-key-change-in-production

# Celery (Task Queue)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Application
APP_NAME=TradingFlow
APP_URL=http://localhost:3000
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

## 🔐 Security Notes

1. **Change default secrets** in `.env` before production:
   - `SECRET_KEY` - for JWT signing
   - `ENCRYPTION_KEY` - for API key encryption

2. **Generate strong keys**:
   ```bash
   # JWT secret (at least 32 chars)
   openssl rand -base64 32
   
   # Encryption key
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

3. **Never commit `.env`** - it's already in `.gitignore`

## 📊 Monitoring

### Health checks
```bash
# Backend
curl http://localhost:8000/health

# Database
docker-compose exec postgres pg_isready -U tradingflow

# Redis
docker-compose exec redis redis-cli ping

# Qdrant
curl http://localhost:6333/dashboard
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f qdrant

# Backend (if running in foreground)
# Check terminal where uvicorn is running
```

## 🧹 Cleanup

### Remove all Docker resources
```bash
# Stop and remove everything
docker-compose down -v

# Remove orphaned containers
docker-compose down --remove-orphans

# Clean up unused images, containers, volumes
docker system prune -a --volumes
```

### Reset database
```bash
# Stop services
docker-compose down

# Remove PostgreSQL data volume
docker volume rm tradingflow_postgres_data

# Restart (will initialize fresh DB)
docker-compose up -d
```

### Clean Python cache
```bash
find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find backend -name "*.pyc" -delete 2>/dev/null
```

### Clean npm cache
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## 🚀 Production Deployment

For production deployment:

1. **Set DEBUG=false** in `.env`
2. **Use strong secrets** (generate new keys)
3. **Enable HTTPS** (configure reverse proxy: Nginx/Traefik)
4. **Use environment variables** for all secrets
5. **Set up backups** for PostgreSQL
6. **Configure monitoring** (Prometheus, Grafana, etc.)
7. **Enable rate limiting** on backend
8. **Use process manager** (systemd, supervisor) for backend
9. **Build frontend** for production: `npm run build`
10. **Serve frontend** via Nginx or CDN

## 📚 Additional Documentation

- **README.md** - Project overview and features
- **ADMINISTRATION.md** - API reference and usage guide
- **CONTEXT.md** - Architecture and technical details
- **EXECUTE.md** - This file (run and manage guide)

## 🆘 Getting Help

1. Check logs: `docker-compose logs` and backend terminal
2. Verify all services are running: `docker-compose ps`
3. Test API: http://localhost:8000/docs
4. Check health: http://localhost:8000/health
5. Review documentation in this repository

---

**Document version:** 1.0  
**Last updated:** 2026-03-02  
**Compatible with:** TradingFlow v0.1.0