# Quick Start: Deploy to Render in 10 Minutes

## Prerequisites
- New GitHub account with forked repo
- That's it! No credit card needed

## Step-by-Step (Ultra Simple)

### 1. Sign Up for Render
```
https://render.com → Sign Up → Use GitHub → Authorize
```

### 2. Deploy Backend (5 minutes)
1. Render Dashboard → **New +** → **Web Service**
2. Select your `cloudcost-optimizer` repo
3. Settings:
   - Name: `cloudcost-api`
   - Runtime: `Python 3`
   - Build: `pip install --upgrade pip && pip install -r requirements.txt`
   - Start: `alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - Plan: **Free**
4. Add these environment variables (no Redis required):
   ```
   DATABASE_URL = <from Render PostgreSQL - see below>
   SECRET_KEY = <run: openssl rand -base64 32>
   DEBUG = false
   ENVIRONMENT = production
   CORS_ORIGINS = http://localhost:5173
   ```
5. Click **Create Web Service**
6. ✅ Wait 5 minutes → Backend live!

### 3. Create PostgreSQL (2 minutes)
1. Render Dashboard → **New +** → **PostgreSQL**
2. Settings:
   - Name: `cloudcost-db`
   - Plan: **Free**
3. Click **Create Database**
4. Copy **Internal Database URL**
5. Go back to your web service → **Environment**
6. Update `DATABASE_URL` with the copied URL
7. Click **Save** (triggers redeploy)

### 4. Get Redis URL (2 minutes)
1. Go to https://upstash.com
2. Sign up with GitHub
3. Create database → Get REST API URL & Token
4. Build URL: `redis://default:<TOKEN>@<HOST>:6379`
5. Update `REDIS_URL` in Render backend environment

### 5. Deploy Frontend (1 minute)
1. Render Dashboard → **New +** → **Static Site**
2. Select your repo
3. Settings:
   - Name: `cloudcost-app`
   - Root Dir: `frontend`
   - Build: `npm install && npm run build`
   - Publish: `dist`
   - Add env var:
     ```
     VITE_API_URL = https://cloudcost-api.onrender.com
     ```
4. Click **Create Static Site**
5. ✅ Wait 3 minutes → Frontend live!

### 5. Update CORS (30 seconds)
1. Go to backend service → **Environment**
2. Update `CORS_ORIGINS`:
   ```
   https://cloudcost-api.onrender.com,https://cloudcost-app.onrender.com
   ```
3. Click **Save**

## Test It
```bash
curl https://cloudcost-api.onrender.com/health
```

Open: `https://cloudcost-app.onrender.com`

## Done! 🎉

### Auto-Deploy Enabled
Every `git push` = automatic deployment!

---

**Need help?** See `DEPLOY_TO_RENDER.md` for detailed guide with screenshots.
