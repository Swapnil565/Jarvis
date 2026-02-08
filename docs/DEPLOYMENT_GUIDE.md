# 🚀 JARVIS 3.0 - Cloud Deployment Guide

## Prerequisites

- ✅ Docker containers tested locally and working
- ✅ Supabase PostgreSQL database configured
- ✅ All environment variables ready
- ✅ GitHub repository with code

---

## Option 1: Railway (Recommended - Easiest)

### Why Railway?
- 🚀 Fastest deployment (< 5 minutes)
- 💰 $5/month free tier
- 🐳 Native Docker support
- 🔄 Auto-deploys from GitHub
- 📊 Built-in metrics
- 🗄️ Managed Redis available

### Step-by-Step

#### 1. Install Railway CLI
```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Mac/Linux
npm install -g @railway/cli
```

#### 2. Login to Railway
```bash
railway login
```

#### 3. Initialize Project
```bash
cd Jarvis3.0
railway init
```

#### 4. Add Services

**Create 4 services in Railway dashboard:**

1. **API Service**
   - Dockerfile: `Dockerfile`
   - Port: 8000
   - Build command: Auto-detected
   - Start command: Auto from Dockerfile

2. **Worker Service**
   - Dockerfile: `Dockerfile.worker`
   - No exposed port
   - Build command: Auto-detected
   - Start command: Auto from Dockerfile

3. **Beat Service**
   - Dockerfile: `Dockerfile.beat`
   - No exposed port
   - Build command: Auto-detected
   - Start command: Auto from Dockerfile

4. **Redis Service**
   - Use Railway's managed Redis
   - Click "Add Service" → "Database" → "Redis"
   - Copy the connection URL

#### 5. Set Environment Variables

For **API service**:
```bash
railway variables set JARVIS_ENV=production
railway variables set DATABASE_URL=your_supabase_url
railway variables set DATABASE_URL_POOLED=your_supabase_pooled_url
railway variables set REDIS_URL=${{Redis.REDIS_URL}}
railway variables set CELERY_BROKER_URL=${{Redis.REDIS_URL}}/1
railway variables set CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}/2
railway variables set SECRET_KEY=your-secret-key
railway variables set LOG_LEVEL=INFO
railway variables set DEBUG=false

# AI API Keys
railway variables set CEREBRAS_API_KEY=your_key
railway variables set GEMINI_API_KEY=your_key
railway variables set GROQ_API_KEY=your_key
railway variables set OPENROUTER_API_KEY=your_key
railway variables set HF_API_KEY=your_key
```

For **Worker and Beat services** - same as API

#### 6. Deploy
```bash
railway up
```

#### 7. Run Database Migration
```bash
# After API is deployed
railway run python -m alembic upgrade head
```

#### 8. Monitor
- Railway dashboard: https://railway.app/dashboard
- Flower monitoring: https://your-api-url.railway.app:5555

### Railway Pricing
- Free tier: $5 credit/month
- Pro: $20/month (includes $20 usage credit)
- Estimated cost for JARVIS:
  - API: ~$5/month
  - Worker: ~$3/month
  - Beat: ~$2/month
  - Redis: Free (included)
  - **Total: ~$10/month**

---

## Option 2: Render

### Why Render?
- 💰 Free tier available
- 🐳 Docker support
- 🔄 Auto-deploys from GitHub
- 📊 Good monitoring
- 🗄️ Managed Redis included

### Step-by-Step

#### 1. Create `render.yaml`

Create this file in your repo root:

```yaml
services:
  # API Service
  - type: web
    name: jarvis-api
    runtime: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: JARVIS_ENV
        value: production
      - key: DATABASE_URL
        sync: false
      - key: DATABASE_URL_POOLED
        sync: false
      - key: REDIS_URL
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: SECRET_KEY
        sync: false
      - key: LOG_LEVEL
        value: INFO
    healthCheckPath: /health
    
  # Celery Worker Service
  - type: worker
    name: jarvis-worker
    runtime: docker
    dockerfilePath: ./Dockerfile.worker
    envVars:
      - key: JARVIS_ENV
        value: production
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
    
  # Celery Beat Service
  - type: worker
    name: jarvis-beat
    runtime: docker
    dockerfilePath: ./Dockerfile.beat
    envVars:
      - key: JARVIS_ENV
        value: production
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString
      - key: CELERY_RESULT_BACKEND
        fromService:
          type: redis
          name: jarvis-redis
          property: connectionString

databases:
  # Redis for Celery
  - name: jarvis-redis
    plan: starter
```

#### 2. Deploy to Render

1. Push code to GitHub
2. Go to https://dashboard.render.com
3. Click "New" → "Blueprint"
4. Connect your GitHub repository
5. Render will detect `render.yaml` and create all services
6. Add secret environment variables in dashboard:
   - `DATABASE_URL`
   - `DATABASE_URL_POOLED`
   - `SECRET_KEY`
   - All AI API keys

#### 3. Monitor
- Render dashboard: https://dashboard.render.com
- View logs for each service
- Check metrics and health

### Render Pricing
- Free tier: Limited but works for testing
- Starter: $7/month per service
- Estimated cost for JARVIS:
  - API: $7/month
  - Worker: $7/month
  - Beat: $7/month
  - Redis: Free
  - **Total: ~$21/month**

---

## Option 3: Fly.io

### Why Fly.io?
- ⚡ Fast deployments globally
- 💰 Generous free tier
- 🐳 Docker-native
- 🌍 Multi-region support

### Step-by-Step

#### 1. Install Fly CLI
```bash
# Windows (PowerShell)
iwr https://fly.io/install.ps1 -useb | iex

# Mac/Linux
curl -L https://fly.io/install.sh | sh
```

#### 2. Login
```bash
fly auth login
```

#### 3. Initialize App
```bash
cd Jarvis3.0
fly launch --no-deploy
```

#### 4. Edit `fly.toml`

```toml
app = "jarvis-api"
primary_region = "sin"  # Singapore (closest to ap-south-1)

[build]
  dockerfile = "Dockerfile"

[env]
  JARVIS_ENV = "production"
  LOG_LEVEL = "INFO"
  DEBUG = "false"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = "30s"
    timeout = "10s"
    grace_period = "5s"
    method = "GET"
    path = "/health"

[processes]
  app = "uvicorn simple_main:app --host 0.0.0.0 --port 8000"
  worker = "celery -A celery_app worker --loglevel=info"
  beat = "celery -A celery_app beat --loglevel=info"
```

#### 5. Add Redis
```bash
fly redis create jarvis-redis
fly secrets set REDIS_URL=<your-redis-url>
```

#### 6. Set Secrets
```bash
fly secrets set DATABASE_URL=your_supabase_url
fly secrets set DATABASE_URL_POOLED=your_supabase_pooled_url
fly secrets set SECRET_KEY=your_secret_key
fly secrets set CEREBRAS_API_KEY=your_key
fly secrets set GEMINI_API_KEY=your_key
fly secrets set GROQ_API_KEY=your_key
```

#### 7. Deploy
```bash
fly deploy
```

#### 8. Scale Services
```bash
# Start worker and beat processes
fly scale count worker=1 beat=1
```

### Fly.io Pricing
- Free tier: 3 shared VMs
- Hobby: $1.94/month per VM
- Estimated cost for JARVIS:
  - API: $1.94/month
  - Worker: $1.94/month
  - Beat: $1.94/month
  - Redis: Free tier
  - **Total: ~$6/month**

---

## Post-Deployment Checklist

### 1. Verify Services
```bash
# Check API
curl https://your-app-url.com/health

# Check Flower monitoring
curl https://your-app-url.com:5555
```

### 2. Run Database Migration
```bash
# Railway
railway run python -m alembic upgrade head

# Render
render run python -m alembic upgrade head

# Fly.io
fly ssh console
python -m alembic upgrade head
```

### 3. Test Celery Tasks
```bash
# Via Flower UI
# Go to http://your-app:5555
# Click "Tasks" → Test a task manually
```

### 4. Configure Monitoring
- Set up Sentry for error tracking
- Configure uptime monitoring (UptimeRobot, Pingdom)
- Set up log aggregation (Papertrail, Logtail)

### 5. Set Up CI/CD
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Railway
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      
      # Or Render
      # - name: Deploy to Render
      #   uses: johnbeynon/render-deploy-action@v0.0.8
      #   with:
      #     service-id: ${{ secrets.RENDER_SERVICE_ID }}
      #     api-key: ${{ secrets.RENDER_API_KEY }}
```

---

## Troubleshooting Production

### Service Won't Start
```bash
# Check logs
railway logs --service api
render logs --service jarvis-api
fly logs
```

### Database Connection Issues
```bash
# Test connection
railway run python -c "from db_sqlalchemy import engine; print(engine.connect())"
```

### Celery Worker Not Processing
```bash
# Check worker logs
railway logs --service worker

# Inspect in Flower
# Go to http://your-app:5555/workers
```

### High Memory Usage
```bash
# Scale down worker concurrency in Dockerfile.worker
# Change: CMD ["celery", "-A", "celery_app", "worker", "--concurrency=2"]
```

---

## Cost Comparison

| Platform | Monthly Cost | Free Tier | Ease of Use | Best For |
|----------|-------------|-----------|-------------|----------|
| **Railway** | ~$10 | $5 credit | ⭐⭐⭐⭐⭐ | Quick deployment |
| **Render** | ~$21 | Limited | ⭐⭐⭐⭐ | Production apps |
| **Fly.io** | ~$6 | 3 VMs | ⭐⭐⭐ | Cost-conscious |

---

## Recommended: Railway

For JARVIS 3.0, **Railway is recommended** because:
- ✅ Fastest setup (< 5 minutes)
- ✅ Best Docker support
- ✅ Managed Redis included
- ✅ Easy environment variable management
- ✅ Good free tier ($5/month)
- ✅ Excellent monitoring

**Deploy now with Railway:**
```bash
railway login
railway init
railway up
```

---

*Last updated: 2025-11-16*
*Status: Production Ready ✅*
