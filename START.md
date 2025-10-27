# Starting the AI Inventory System

## Prerequisites
- Podman and Podman Compose installed
- OpenRouter API key (get from https://openrouter.ai/)

## Steps to Run

1. **Create .env file in root directory:**
   ```
   OPENROUTER_API_KEY=your_actual_api_key_here
   ```

2. **Start all services:**
   ```bash
   podman-compose up -d
   ```

3. **Run database migrations:**
   ```bash
   podman-compose exec backend alembic upgrade head
   ```

4. **Seed initial data (optional):**
   ```bash
   podman-compose exec backend python seed.py
   ```

5. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Verify Services

Check if all services are running:
```bash
podman-compose ps
```

You should see:
- ai-inventory-db (PostgreSQL with pgvector)
- ai-inventory-redis
- ai-inventory-backend (FastAPI)
- ai-inventory-celery (Background worker)
- ai-inventory-frontend (React)

## View Logs

```bash
# All services
podman-compose logs -f

# Specific service
podman-compose logs -f backend
podman-compose logs -f celery_worker
podman-compose logs -f frontend
```

## Stop Services

```bash
podman-compose down
```

## Troubleshooting

If you encounter issues:

1. **Port conflicts:** Make sure ports 3000, 5432, 6379, 8000 are available
2. **Database connection:** Wait for PostgreSQL to be fully ready (check with `podman-compose logs db`)
3. **API key:** Verify your OPENROUTER_API_KEY is set correctly
4. **Rebuild containers:** `podman-compose down && podman-compose up --build -d`
