# 🔗 Frontend-Backend Connection Guide

## 🎯 How to Connect React/Next.js Frontend to JARVIS Backend

---

## 📋 Overview

### Backend (Already Done ✅)
- **API**: FastAPI with REST endpoints
- **URL**: `http://localhost:8000` (local) or `https://jarvis-api.onrender.com` (production)
- **Docs**: `/docs` (Swagger UI)
- **Auth**: JWT tokens

### Frontend (To Be Built)
- **Framework**: React / Next.js / Vue / Svelte
- **Communication**: HTTP requests (axios/fetch)
- **Auth**: Store JWT in localStorage/cookies
- **State**: React Context / Redux / Zustand

---

## 🚀 Quick Start: Connect Frontend in 3 Steps

### Step 1: Set Backend URL

Create `frontend/.env`:
```env
# Development
NEXT_PUBLIC_API_URL=http://localhost:8000

# Production (after deploying backend)
NEXT_PUBLIC_API_URL=https://jarvis-api.onrender.com
```

### Step 2: Create API Client

Create `frontend/lib/api.js`:
```javascript
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
});

// Add JWT token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Step 3: Use API in Components

Example: User Login
```javascript
// components/LoginForm.jsx
import { useState } from 'react';
import api from '@/lib/api';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Call backend /auth/login endpoint
      const response = await api.post('/auth/login', {
        username: email,
        password: password,
      });

      // Store JWT token
      localStorage.setItem('access_token', response.data.access_token);
      
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Login failed:', error);
      alert('Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

## 🔐 Authentication Flow

### 1. User Registration
```javascript
// Register new user
const register = async (userData) => {
  const response = await api.post('/auth/register', {
    email: userData.email,
    password: userData.password,
    full_name: userData.name,
  });
  return response.data;
};
```

### 2. User Login
```javascript
// Login and get JWT token
const login = async (email, password) => {
  const response = await api.post('/auth/login', {
    username: email,
    password: password,
  });
  
  // Store token
  localStorage.setItem('access_token', response.data.access_token);
  localStorage.setItem('user', JSON.stringify(response.data.user));
  
  return response.data;
};
```

### 3. Get Current User
```javascript
// Get logged-in user profile
const getCurrentUser = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};
```

### 4. Logout
```javascript
// Logout user
const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = '/login';
};
```

---

## 📊 Example API Calls for JARVIS Features

### 1. Track Event
```javascript
// Track a new event (mood, sleep, etc.)
const trackEvent = async (eventData) => {
  const response = await api.post('/events', {
    category: eventData.category,      // 'mood', 'sleep', 'activity'
    event_type: eventData.type,        // 'check-in', 'log'
    feeling: eventData.feeling,        // 'happy', 'anxious', etc.
    data: {
      intensity: eventData.intensity,  // 1-10
      notes: eventData.notes,
      timestamp: new Date().toISOString(),
    },
  });
  return response.data;
};

// Usage in component
const handleMoodLog = async () => {
  await trackEvent({
    category: 'mood',
    type: 'check-in',
    feeling: 'happy',
    intensity: 8,
    notes: 'Had a great day!',
  });
};
```

### 2. Get Insights
```javascript
// Get AI-generated insights
const getInsights = async () => {
  const response = await api.get('/insights');
  return response.data;
};

// Usage
const InsightsPage = () => {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const data = await getInsights();
        setInsights(data.insights);
      } catch (error) {
        console.error('Failed to fetch insights:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, []);

  return (
    <div>
      {loading ? (
        <p>Loading insights...</p>
      ) : (
        insights.map((insight) => (
          <div key={insight.id}>
            <h3>{insight.title}</h3>
            <p>{insight.message}</p>
          </div>
        ))
      )}
    </div>
  );
};
```

### 3. Get Patterns
```javascript
// Get detected patterns
const getPatterns = async () => {
  const response = await api.get('/patterns');
  return response.data;
};
```

### 4. Get Forecasts
```javascript
// Get predictions
const getForecasts = async (days = 7) => {
  const response = await api.get(`/forecasts?days=${days}`);
  return response.data;
};
```

### 5. Get Interventions
```javascript
// Get personalized interventions
const getInterventions = async () => {
  const response = await api.get('/interventions');
  return response.data;
};
```

### 6. Trigger Agent Analysis
```javascript
// Manually trigger AI agents
const runAgents = async () => {
  const response = await api.post('/agents/run');
  return response.data;
};
```

---

## 🎨 Example React Components

### Dashboard Component
```javascript
// pages/dashboard.jsx
import { useState, useEffect } from 'react';
import api from '@/lib/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        // Fetch multiple endpoints in parallel
        const [eventsRes, insightsRes, patternsRes] = await Promise.all([
          api.get('/events?limit=10'),
          api.get('/insights'),
          api.get('/patterns'),
        ]);

        setStats({
          events: eventsRes.data,
          insights: insightsRes.data,
          patterns: patternsRes.data,
        });
      } catch (error) {
        console.error('Dashboard load failed:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div className="dashboard">
      <h1>JARVIS Dashboard</h1>
      
      <section className="insights">
        <h2>Your Insights</h2>
        {stats.insights.map((insight) => (
          <div key={insight.id} className="insight-card">
            <h3>{insight.title}</h3>
            <p>{insight.message}</p>
          </div>
        ))}
      </section>

      <section className="patterns">
        <h2>Detected Patterns</h2>
        {stats.patterns.map((pattern) => (
          <div key={pattern.id} className="pattern-card">
            <h3>{pattern.pattern_type}</h3>
            <p>{pattern.description}</p>
            <span>Confidence: {(pattern.confidence * 100).toFixed(0)}%</span>
          </div>
        ))}
      </section>

      <section className="recent-events">
        <h2>Recent Activity</h2>
        {stats.events.map((event) => (
          <div key={event.id} className="event-card">
            <span>{event.category}</span>
            <span>{event.feeling}</span>
            <span>{new Date(event.timestamp).toLocaleString()}</span>
          </div>
        ))}
      </section>
    </div>
  );
}
```

### Mood Tracker Component
```javascript
// components/MoodTracker.jsx
import { useState } from 'react';
import api from '@/lib/api';

const MOODS = [
  { value: 'happy', emoji: '😊', label: 'Happy' },
  { value: 'sad', emoji: '😢', label: 'Sad' },
  { value: 'anxious', emoji: '😰', label: 'Anxious' },
  { value: 'calm', emoji: '😌', label: 'Calm' },
  { value: 'angry', emoji: '😠', label: 'Angry' },
  { value: 'excited', emoji: '🎉', label: 'Excited' },
];

export default function MoodTracker() {
  const [selectedMood, setSelectedMood] = useState(null);
  const [intensity, setIntensity] = useState(5);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!selectedMood) {
      alert('Please select a mood');
      return;
    }

    setLoading(true);
    try {
      await api.post('/events', {
        category: 'mood',
        event_type: 'check-in',
        feeling: selectedMood,
        data: {
          intensity: intensity,
          notes: notes,
          timestamp: new Date().toISOString(),
        },
      });

      // Reset form
      setSelectedMood(null);
      setIntensity(5);
      setNotes('');
      
      alert('Mood logged successfully!');
    } catch (error) {
      console.error('Failed to log mood:', error);
      alert('Failed to log mood');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mood-tracker">
      <h2>How are you feeling?</h2>
      
      <div className="mood-selector">
        {MOODS.map((mood) => (
          <button
            key={mood.value}
            className={selectedMood === mood.value ? 'selected' : ''}
            onClick={() => setSelectedMood(mood.value)}
          >
            <span className="emoji">{mood.emoji}</span>
            <span className="label">{mood.label}</span>
          </button>
        ))}
      </div>

      {selectedMood && (
        <>
          <div className="intensity-slider">
            <label>Intensity: {intensity}/10</label>
            <input
              type="range"
              min="1"
              max="10"
              value={intensity}
              onChange={(e) => setIntensity(parseInt(e.target.value))}
            />
          </div>

          <div className="notes">
            <label>Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="What's on your mind?"
              rows={3}
            />
          </div>

          <button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Logging...' : 'Log Mood'}
          </button>
        </>
      )}
    </div>
  );
}
```

---

## 🔄 Real-time Updates with WebSockets (Optional)

For real-time notifications when AI generates new insights:

### Backend Setup (Already in simple_main.py)
```python
# WebSocket endpoint for real-time updates
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket.accept()
    try:
        while True:
            # Send updates when new insights/interventions are generated
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected")
```

### Frontend WebSocket Client
```javascript
// lib/websocket.js
export const connectWebSocket = (userId) => {
  const ws = new WebSocket(
    `ws://localhost:8000/ws/${userId}`
  );

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('New update:', data);
    
    // Show notification
    if (data.type === 'intervention') {
      showNotification(data.message);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Reconnect after 5 seconds
    setTimeout(() => connectWebSocket(userId), 5000);
  };

  return ws;
};
```

---

## 🌐 CORS Configuration (Already Done ✅)

Backend already configured to allow frontend connections:

```python
# In simple_main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### For Production
Update to allow only your frontend domain:
```python
allow_origins=[
    "http://localhost:3000",           # Local development
    "https://your-app.vercel.app",     # Vercel deployment
    "https://your-domain.com",         # Custom domain
]
```

---

## 📱 Example: Complete Next.js App Structure

```
frontend/
├── pages/
│   ├── index.js              # Landing page
│   ├── login.js              # Login page
│   ├── register.js           # Registration page
│   ├── dashboard.js          # Main dashboard
│   ├── mood/
│   │   └── track.js          # Mood tracking
│   ├── insights/
│   │   └── index.js          # AI insights
│   └── patterns/
│       └── index.js          # Detected patterns
├── components/
│   ├── MoodTracker.jsx
│   ├── InsightCard.jsx
│   ├── PatternCard.jsx
│   └── Layout.jsx
├── lib/
│   ├── api.js                # API client
│   ├── auth.js               # Auth helpers
│   └── websocket.js          # WebSocket client
├── hooks/
│   ├── useAuth.js            # Auth hook
│   └── useInsights.js        # Insights hook
├── .env.local
└── next.config.js
```

---

## 🚀 Deploy Frontend

### Option 1: Vercel (Recommended for Next.js)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
# Enter: https://jarvis-api.onrender.com
```

### Option 2: Netlify
```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
netlify deploy --prod

# Set environment variable in Netlify dashboard
```

### Option 3: GitHub Pages (Static only)
```bash
# Build
npm run build

# Deploy to GitHub Pages
npm run deploy
```

---

## 🔗 Complete Connection Checklist

- [ ] Backend deployed and accessible
- [ ] Frontend `.env` file created with API URL
- [ ] API client (`lib/api.js`) created
- [ ] CORS configured on backend
- [ ] JWT token storage implemented
- [ ] Login/Register forms working
- [ ] Protected routes implemented
- [ ] API calls tested (events, insights, patterns)
- [ ] Error handling added
- [ ] Loading states implemented
- [ ] WebSocket connection (optional)
- [ ] Frontend deployed
- [ ] End-to-end testing complete

---

## 📚 API Endpoints Reference

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user (returns JWT)
- `GET /auth/me` - Get current user

### Events
- `POST /events` - Track new event
- `GET /events` - Get user's events
- `GET /events/{id}` - Get specific event

### Insights
- `GET /insights` - Get AI insights
- `POST /insights/generate` - Trigger insight generation

### Patterns
- `GET /patterns` - Get detected patterns
- `GET /patterns/{id}` - Get specific pattern

### Forecasts
- `GET /forecasts` - Get predictions
- `GET /forecasts?days=7` - Get 7-day forecast

### Interventions
- `GET /interventions` - Get personalized interventions
- `POST /interventions/{id}/acknowledge` - Mark as read

### Agents
- `POST /agents/run` - Manually trigger all agents
- `GET /agents/status` - Get agent status

### Health
- `GET /health` - Health check

---

## 🎯 Quick Start Template

Create a new Next.js project connected to JARVIS:

```bash
# Create Next.js app
npx create-next-app@latest jarvis-frontend --typescript --tailwind

cd jarvis-frontend

# Install dependencies
npm install axios

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Copy api.js from this guide to lib/api.js

# Start development
npm run dev
```

Your frontend will be at: http://localhost:3000  
Your backend is at: http://localhost:8000

**They're now connected!** 🎉

---

*Last updated: 2025-11-16*  
*Status: Ready to connect! 🔗*
