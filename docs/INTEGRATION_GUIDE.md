# 🔗 Frontend-Backend Integration Guide

## 🎯 Quick Answer: DON'T Move Anything!

Your folders stay separate. They communicate via HTTP (like any API).

---

## 📁 Current Setup (Perfect!)

```
C:\Users\swapn\OneDrive\Documents\
│
├── Jarvis\Jarvis_Backend\JARVIS3.0_BACKEND\Jarvis3.0\  ← BACKEND (stays here)
│   ├── simple_main.py           # FastAPI runs on http://localhost:8000
│   ├── docker-compose.yml       # Start with: docker-compose up
│   └── ...
│
└── [YourFrontendFolder]\         ← FRONTEND (stays in its location)
    ├── .env.local               # Add one line (see below)
    ├── lib\api.js              # API client (see below)
    └── ...
```

**NO MOVING REQUIRED!** They talk via HTTP.

---

## 🚀 Integration Steps (3 minutes)

### **Step 1: Start Backend** (in this folder)

```powershell
# Backend terminal (this folder)
cd C:\Users\swapn\OneDrive\Documents\Jarvis\Jarvis_Backend\JARVIS3.0_BACKEND\Jarvis3.0
docker-compose up

# Backend now running at: http://localhost:8000
# API docs at: http://localhost:8000/docs
```

---

### **Step 2: Configure Frontend** (in your frontend folder)

```powershell
# Frontend terminal (your frontend folder)
cd C:\path\to\your\frontend

# Create .env.local file
echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
```

**That's it!** The environment variable tells your frontend where the backend is.

---

### **Step 3: Use API in Frontend**

**Create `lib/api.js`** (if not already exists):

```javascript
// lib/api.js
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 (redirect to login)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

### **Step 4: Make API Calls**

```javascript
// Example: Track mood
import api from '@/lib/api';

// Login
const login = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  localStorage.setItem('access_token', response.data.access_token);
  return response.data;
};

// Track event
const trackMood = async (mood, intensity) => {
  return await api.post('/events', {
    category: 'mood',
    event_type: 'check-in',
    feeling: mood,
    data: { intensity }
  });
};

// Get insights
const getInsights = async () => {
  const response = await api.get('/insights');
  return response.data;
};
```

---

## 🔄 Development Workflow

### **Both Running Locally:**

```
Terminal 1 (Backend):                Terminal 2 (Frontend):
─────────────────────                ─────────────────────
cd backend/                          cd frontend/
docker-compose up                    npm run dev

Backend: http://localhost:8000       Frontend: http://localhost:3000
                                     ↓
                                     Calls backend at localhost:8000
```

**Frontend makes HTTP requests to backend. That's the integration!**

---

## 🌐 Production Setup

When you deploy, just update the environment variable:

```javascript
// Frontend .env.production
NEXT_PUBLIC_API_URL=https://jarvis-api.onrender.com

// That's it! Same code works in production.
```

---

## ❓ FAQ

### **Q: Do I need to move files?**
**A:** NO! Keep them separate. They talk via HTTP.

### **Q: How do they communicate?**
**A:** Frontend makes HTTP requests (like `axios.get()`) to backend URL.

### **Q: What if they're on different computers?**
**A:** Still works! Just use the IP address:
```javascript
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
```

### **Q: Is this slower than combining them?**
**A:** NO! This is the standard way. Actually faster because:
- Frontend can be on CDN (Vercel)
- Backend near database (Render)
- Independent scaling

---

## ✅ Integration Checklist

- [ ] Backend running at `http://localhost:8000`
- [ ] Frontend has `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Frontend has `lib/api.js` with axios setup
- [ ] API calls use `api.get('/endpoint')` instead of hardcoded URLs
- [ ] JWT token stored in localStorage after login
- [ ] CORS enabled on backend (already configured in `simple_main.py`)

---

## 🎯 Summary

**Integration = Environment Variable + HTTP Calls**

1. Backend runs on port 8000
2. Frontend has env var pointing to backend
3. Frontend makes HTTP requests
4. **NO FILE MOVING NEEDED!**

**Diagram:**
```
Frontend (localhost:3000)
    ↓
    HTTP Request (axios.get)
    ↓
Backend (localhost:8000)
    ↓
    Database (Supabase)
```

**That's it!** No monorepo, no file moving, just standard API integration. 🚀

---

## 📚 See Also

- `docs/FRONTEND_BACKEND_CONNECTION.md` - Complete examples with React components
- `docs/API_ENDPOINTS.md` - All available endpoints
- `docs/COMPLETE_SETUP_SUMMARY.md` - Full deployment guide

