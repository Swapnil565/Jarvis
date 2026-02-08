# 🆓 JARVIS 3.0 - Free Deployment Options

## 🎯 Best Free Platforms for JARVIS 3.0

| Platform | Free Tier | Best For | Limitations |
|----------|-----------|----------|-------------|
| **Render** | ⭐⭐⭐⭐⭐ | Full-stack apps | 750 hrs/month, spins down |
| **Railway** | ⭐⭐⭐⭐ | Docker apps | $5 credit/month |
| **Fly.io** | ⭐⭐⭐⭐ | Global apps | 3 VMs free |
| **Koyeb** | ⭐⭐⭐⭐ | Container apps | 1 web + 1 worker free |

---

## 🏆 RECOMMENDED: Render (100% Free for JARVIS)

### Why Render?
- ✅ **Completely FREE** for our use case
- ✅ Native Docker support
- ✅ Free PostgreSQL (already using Supabase)
- ✅ Free Redis (1 instance)
- ✅ Auto-deploys from GitHub
- ✅ Free SSL certificates
- ✅ 750 hours/month per service (enough for testing)

### Free Tier Details
- **Web Services**: 750 hours/month each (spins down after 15 min inactivity)
- **Background Workers**: 750 hours/month each
- **Redis**: 25 MB free
- **PostgreSQL**: 256 MB free (we're using Supabase)
- **Bandwidth**: 100 GB/month

---

## 🚀 Deploy to Render (Step-by-Step)

### Step 1: Prepare Your Repository

1. **Push code to GitHub**:
```bash
cd Jarvis3.0
git add .
git commit -m "Ready for deployment"
git push origin main
```

2. **Create `render.yaml` in repo root**:

```yaml
# render.yaml - Infrastructure as Code for Render
services:
  # ========================================
  # API Service (FastAPI)
  # ========================================
  - type: web
    name: jarvis-api
    runtime: docker
    dockerfilePath: ./Dockerfile
    dockerContext: .
    region: singapore  # Closest to ap-south-1 (Mumbai)
    plan: free
    healthCheckPath: /health
    envVars:
      - key: JARVIS_ENV
        value: production
      - key: DATABASE_URL
        sync: false  # Set in Render dashboard
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
      - key: JWT_SECRET_KEY
        sync: false
      - key: LOG_LEVEL
        value: INFO
      - key: DEBUG
        value: false
      # AI API Keys
      - key: CEREBRAS_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: HUGGINGFACE_API_KEY
        sync: false

  # ========================================
  # Celery Worker (Background Tasks)
  # ========================================
  - type: worker
    name: jarvis-worker
    runtime: docker
    dockerfilePath: ./Dockerfile.worker
    dockerContext: .
    region: singapore
    plan: free
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
      - key: CEREBRAS_API_KEY
        sync: false
      - key: GEMINI_API_KEY
        sync: false
      - key: GROQ_API_KEY
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: HUGGINGFACE_API_KEY
        sync: false

  # ========================================
  # Celery Beat (Scheduler)
  # ========================================
  - type: worker
    name: jarvis-beat
    runtime: docker
    dockerfilePath: ./Dockerfile.beat
    dockerContext: .
    region: singapore
    plan: free
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
  # ========================================
  # Redis (Free 25MB)
  # ========================================
  - name: jarvis-redis
    plan: free
    maxmemoryPolicy: noeviction
```

### Step 2: Deploy to Render

1. **Go to** https://dashboard.render.com
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub account
4. Select your repository
5. Render will detect `render.yaml` automatically
6. Click **"Apply"**

### Step 3: Add Secret Environment Variables

In Render dashboard, for **each service** (api, worker, beat):

1. Go to service → **Environment**
2. Add these secrets:

```env
DATABASE_URL=postgresql://postgres.ulnfnxvxlswjomqrobrd:YOUR_DB_PASSWORD@aws-1-ap-south-1.pooler.supabase.com:5432/postgres

DATABASE_URL_POOLED=postgresql://postgres.ulnfnxvxlswjomqrobrd:YOUR_DB_PASSWORD@aws-1-ap-south-1.pooler.supabase.com:6543/postgres

SECRET_KEY=your-super-secret-production-key-here-min-32-chars

JWT_SECRET_KEY=your-jwt-secret-production-key-here-min-32-chars

CEREBRAS_API_KEY=csk-44c3n6nehvh63vmw4r3n8hmkr5hx6pcdrdtt6fnem3cetpeh

GEMINI_API_KEY=YOUR_GEMINI_API_KEY

GROQ_API_KEY=YOUR_GROQ_API_KEY

OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY

HUGGINGFACE_API_KEY=YOUR_HUGGINGFACE_API_KEY
```

### Step 4: Run Database Migration

After API is deployed:

1. Go to **jarvis-api** service in Render
2. Click **"Shell"** tab
3. Run migration:
```bash
python -m alembic upgrade head
```

### Step 5: Test Your Deployment

Your API will be available at:
```
https://jarvis-api.onrender.com
```

Test it:
```bash
curl https://jarvis-api.onrender.com/health
```

---

## 🎓 Alternative: Koyeb (Also 100% Free)

### Why Koyeb?
- ✅ Always-on (no spin down!)
- ✅ 1 web + 1 worker FREE
- ✅ Global CDN
- ✅ Fast deployments

### Deploy to Koyeb

1. **Go to** https://www.koyeb.com
2. Sign up (GitHub login)
3. Click **"Create Service"**
4. Choose **"GitHub"** as source
5. Select your repository
6. Configure:
   - **Service type**: Web
   - **Dockerfile**: `Dockerfile`
   - **Port**: 8000
   - **Health check**: `/health`
7. Add environment variables (same as Render)
8. Click **"Deploy"**

Repeat for worker and beat (as "Worker" service type)

### Koyeb Free Tier
- **Web Service**: 1 instance, 512MB RAM, always-on
- **Worker**: 1 instance, 512MB RAM, always-on
- **Bandwidth**: 100GB/month
- **Build time**: Unlimited

---

## 🌐 Alternative: Fly.io (Free 3 VMs)

### Why Fly.io?
- ✅ 3 shared VMs FREE
- ✅ Global deployment
- ✅ Fast deploys

### Deploy to Fly.io

1. **Install Fly CLI**:
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

2. **Login**:
```bash
fly auth login
```

3. **Create `fly.toml`**:
```toml
app = "jarvis-api"
primary_region = "sin"  # Singapore

[build]
  dockerfile = "Dockerfile"

[env]
  JARVIS_ENV = "production"
  PORT = "8000"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.http_checks]]
    interval = "30s"
    timeout = "10s"
    method = "GET"
    path = "/health"

[[vm]]
  memory = '256mb'
  cpu_kind = 'shared'
  cpus = 1
```

4. **Launch**:
```bash
fly launch --no-deploy
fly secrets set DATABASE_URL=your_supabase_url
fly secrets set REDIS_URL=your_redis_url
fly deploy
```

---

## 💰 Cost Comparison (Free Tiers)

| Platform | Always-On? | Services | RAM | Bandwidth | Best Use |
|----------|-----------|----------|-----|-----------|----------|
| **Render** | ❌ (15min timeout) | Unlimited | 512MB | 100GB | Testing/Demo |
| **Koyeb** | ✅ Yes | 1 web + 1 worker | 512MB | 100GB | **Production** |
| **Fly.io** | ✅ Yes | 3 VMs | 256MB | 160GB | Production |
| **Railway** | ⚠️ ($5 credit) | Unlimited | 512MB | 100GB | Development |

---

## 🏆 FINAL RECOMMENDATION

### For Testing/Demo: **Render**
- Completely free
- Easy setup with render.yaml
- Auto-deploys from GitHub
- ⚠️ Spins down after 15 minutes (first request will be slow)

### For Production: **Koyeb**
- Always-on (no spin down!)
- 1 web + 1 worker free
- Fast and reliable
- Perfect for JARVIS's architecture

---

## 📝 What About Redis?

### Option 1: Render Free Redis (Recommended)
- 25MB free
- Included in render.yaml above
- Auto-connected to services

### Option 2: Upstash Redis (Alternative)
- 10,000 commands/day free
- Global edge network
- Sign up: https://upstash.com

```bash
# Add Upstash Redis URL to env vars:
REDIS_URL=rediss://default:password@region.upstash.io:6379
```

---

## 🎯 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `render.yaml` created in repo root
- [ ] Connected Render to GitHub
- [ ] Services deployed (api, worker, beat, redis)
- [ ] Environment variables added (DATABASE_URL, API keys)
- [ ] Database migration run (`alembic upgrade head`)
- [ ] Health check passing (`/health` returns 200)
- [ ] Celery worker connected (check logs)
- [ ] Celery beat running (check logs)
- [ ] Test API endpoints
- [ ] Monitor for 24 hours

---

## 🔍 Monitoring Your Free Deployment

### Check Service Status
- **Render**: https://dashboard.render.com → Your service → Logs
- **Koyeb**: https://app.koyeb.com → Services → Logs  
- **Fly.io**: `fly logs -a jarvis-api`

### Health Checks
```bash
# API
curl https://your-app.onrender.com/health

# Check all endpoints
curl https://your-app.onrender.com/docs
```

### Celery Monitoring
Access Flower (if deployed):
```
https://your-app.onrender.com:5555
```

---

## ⚠️ Free Tier Limitations & Solutions

### Problem: Service Spins Down (Render)
**Solution**: Use a free uptime monitor
- https://uptimerobot.com (50 monitors free)
- Ping your API every 5 minutes
- Keeps service awake

### Problem: Redis Memory Limit (25MB)
**Solution**: 
- Enable eviction policy: `noeviction` or `allkeys-lru`
- Or use Upstash (10K commands/day free)

### Problem: Build Time Limit
**Solution**:
- Already using multi-stage builds ✅
- Already using uv (fast builds) ✅
- Build time should be < 5 minutes

---

## 🚀 Next: Deploy NOW!

### Quickest Path (5 minutes):

1. **Create `render.yaml`** (copy from above)
2. **Push to GitHub**:
   ```bash
   git add render.yaml
   git commit -m "Add Render deployment config"
   git push
   ```
3. **Go to Render** → New Blueprint → Connect GitHub
4. **Add secrets** in dashboard
5. **Done!** 🎉

Your backend will be live at:
```
https://jarvis-api.onrender.com
```

---

*Last updated: 2025-11-16*  
*Status: Ready to deploy for FREE! 🆓*
