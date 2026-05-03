# 🚀 JARVIS 3.0 - OFFICIAL LAUNCH GUIDE

Welcome to the deployment phase. We will launch **Jarvis Backend** on **Render** and **Jarvis Frontend** on **Vercel**.

---

## 📅 PHASE 1: PREPARATION

### 1. GitHub Setup
You currently have code in two folders. You need to push them to GitHub.

**Backend Repo:**
1. Go to [GitHub.com](https://github.com) and create a new repository named `jarvis-backend`.
2. Open a terminal in VS Code:
   ```powershell
   cd Jarvis3.0
   git init
   git add .
   git commit -m "Initial launch commit"
   git branch -M main
   # Replace with your actual repo URL
   git remote add origin https://github.com/YOUR_USERNAME/jarvis-backend.git
   git push -u origin main
   ```

**Frontend Repo:**
1. Create a new repository named `jarvis-frontend`.
2. Open a terminal:
   ```powershell
   cd ../Jarvis_Frontend/jarvis
   git init
   git add .
   git commit -m "Initial launch commit"
   git branch -M main
   # Replace with your actual repo URL
   git remote add origin https://github.com/YOUR_USERNAME/jarvis-frontend.git
   git push -u origin main
   ```

---

## ☁️ PHASE 2: DEPLOY BACKEND (Render)

1. **Create Account**: Go to [render.com](https://render.com) and sign up with GitHub.
2. **New Web Service**:
   - Click **"New +"** → **"Web Service"**.
   - Select your `jarvis-backend` repository.
3. **Configuration**:
   - **Name**: `jarvis-api`
   - **Region**: Singapore (or closest to you)
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`
4. **Environment Variables** (Click "Advanced" or "Environment"):
   Add these keys:
   - `JARVIS_ENV`: `production`
   - `SECRET_KEY`: `generate_a_random_string_here`
   - `OPENAI_API_KEY`: `sk-...` (Your OpenAI key)
   - `GROQ_API_KEY`: (Your Groq key if using it)
   - `LOG_LEVEL`: `INFO`
5. **Deploy**:
   - Click **"Create Web Service"**.
   - Wait ~5 minutes. You will get a URL like `https://jarvis-api.onrender.com`.
   - **COPY THIS URL.**

---

## ⚡ PHASE 3: DEPLOY FRONTEND (Vercel)

1. **Create Account**: Go to [vercel.com](https://vercel.com) and sign up with GitHub.
2. **New Project**:
   - Click "Add New..." → "Project".
   - Import your `jarvis-frontend` repository.
3. **Configure Project**:
   - **Framework Preset**: Next.js (should detect automatically).
   - **Root Directory**: `.` (default).
4. **Environment Variables**:
   - Expand "Environment Variables".
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: `https://jarvis-api.onrender.com` (The URL you copied from Render).
   - **IMPORTANT**: Remove any trailing slash (e.g., use `...onrender.com` NOT `...onrender.com/`).
5. **Deploy**:
   - Click **"Deploy"**.
   - Wait ~2 minutes.
   - You will get a URL like `https://jarvis-frontend.vercel.app`.

---

## 🚀 PHASE 4: THE LAUNCH

1. Open your **Vercel URL** in a browser.
2. You should see the Landing Page / Onboarding.
3. Complete the onboarding.
4. Check the **Render Dashboard Logs** to see the backend processing your requests.

**CONGRATULATIONS! JARVIS IS LIVE.** 🌍
