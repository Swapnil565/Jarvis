Redis Quickstart for JARVIS (Docker)

1) Start Redis (PowerShell):
   ./scripts/start_redis.ps1

2) Verify Redis is running (PowerShell):
   docker ps --filter "name=jarvis-redis"

3) Test connection from Python (PowerShell):
   python -c "import redis; r=redis.Redis(host='localhost', port=6379); print(r.ping())"

4) Stop Redis (PowerShell):
   docker compose -f docker-compose.redis.yml down

Notes:
- Requires Docker Desktop or Docker Engine installed on Windows.
- Uses redis:7-alpine image and persists data to a local Docker volume named `redis-data`.
