# Deploy to Render (Free Tier) - Complete Guide

## Why Render?
- **Truly Free**: No credit card required
- **Auto-Deploy**: Git push = instant deployment
- **Free PostgreSQL**: 90 days (then we'll migrate to Neon)
- **Simple Setup**: 10 minutes total

---

## Part 1: Setup Your New GitHub Account

### Step 1: Create Fresh GitHub Account
1. Go to https://github.com/signup
2. Use a **new email** (Gmail, Outlook, etc.)
3. Complete verification
4. **Important**: Write down your credentials!

### Step 2: Fork or Import This Project
You have two options:

**Option A: Fork (Easier)**
1. Log into your **original** GitHub account
2. Go to your `cloudcost-optimizer` repo
3. Click **Fork** → Select your **new** account
4. Done!

**Option B: Import (Clean Start)**
1. Log into your **new** GitHub account
2. Go to https://github.com/new/import
3. Paste your original repo URL
4. Name it: `cloudcost-optimizer`
5. Click **Begin Import**
6. Wait 2-3 minutes

---

## Part 2: Deploy Backend to Render

### Step 1: Sign Up for Render
1. Go to https://render.com
2. Click **Sign Up**
3. Select **GitHub**
4. Authorize your **new** GitHub account
5. ✅ No credit card needed!

### Step 2: Create PostgreSQL Database
1. In Render dashboard, click **New +** → **PostgreSQL**
2. Settings:
   - **Name**: `cloudcost-db`
   - **Database**: `cloudcost`
   - **User**: `cloudcost_user`
   - **Region**: `Oregon (US West)` (free)
   - **PostgreSQL Version**: 16
   - **Plan**: **Free** (important!)
3. Click **Create Database**
4. Wait 2-3 minutes for provisioning
5. **SAVE THIS**: Copy the **Internal Database URL** (starts with `postgresql://`)

### Step 3: Create Redis (Using Upstash)
Render's free tier doesn't include Redis, so we'll use Upstash (free forever):

1. Go to https://upstash.com
2. Sign up with GitHub
3. Click **Create Database**
4. Settings:
   - **Name**: `cloudcost-redis`
   - **Type**: Global
   - **Region**: Choose nearest
   - **Eviction**: Enable (important for free tier)
5. Click **Create**
6. On the database page:
   - Scroll to **REST API** section
   - **SAVE THIS**: Copy both:
     - `UPSTASH_REDIS_REST_URL` (e.g., `https://xxx.upstash.io`)
     - `UPSTASH_REDIS_REST_TOKEN` (long string)

### Step 4: Deploy Backend Web Service
1. In Render dashboard, click **New +** → **Web Service**
2. Connect your **new** GitHub account (if not already)
3. Select your `cloudcost-optimizer` repository
4. Settings:
   - **Name**: `cloudcost-api` (or any name you want)
   - **Region**: `Oregon (US West)` (same as database)
   - **Branch**: `main` (or `master`)
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: **Free** (important!)

5. Click **Advanced** → **Add Environment Variables**:
   ```
   DATABASE_URL = <paste Internal Database URL from Step 2>
   REDIS_URL = redis://default:<UPSTASH_TOKEN>@<UPSTASH_HOST>:6379
   SECRET_KEY = <generate random 32-char string>
   DEBUG = false
   ENVIRONMENT = production
   CORS_ORIGINS = http://localhost:5173,http://localhost:3000
   AWS_REGION = us-east-1
   AWS_ACCESS_KEY_ID = <optional - leave blank for now>
   AWS_SECRET_ACCESS_KEY = <optional - leave blank for now>
   ```

   **How to build REDIS_URL from Upstash**:
   - If `UPSTASH_REDIS_REST_URL` = `https://free-kangaroo-12345.upstash.io`
   - And `UPSTASH_REDIS_REST_TOKEN` = `AbCdEf123456...`
   - Then `REDIS_URL` = `redis://default:AbCdEf123456...@free-kangaroo-12345.upstash.io:6379`

   **How to generate SECRET_KEY**:
   - Run in terminal: `openssl rand -base64 32`
   - Copy the output

6. Click **Create Web Service**
7. Wait 5-10 minutes for first deployment
8. ✅ Your backend will be live at: `https://cloudcost-api.onrender.com` (or your chosen name)

### Step 5: Update CORS
1. In Render dashboard, go to your `cloudcost-api` service
2. Go to **Environment** tab
3. Find `CORS_ORIGINS` variable
4. Click **Edit**
5. Update to:
   ```
   https://cloudcost-api.onrender.com,http://localhost:5173,http://localhost:3000
   ```
6. Click **Save Changes** (this will trigger a redeploy)

---

## Part 3: Deploy Frontend to Render

### Step 1: Create Frontend Static Site
1. In Render dashboard, click **New +** → **Static Site**
2. Select your `cloudcost-optimizer` repository again
3. Settings:
   - **Name**: `cloudcost-app` (or any name)
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**:
     ```bash
     npm install && npm run build
     ```
   - **Publish Directory**: `dist`

4. Click **Advanced** → **Add Environment Variable**:
   ```
   VITE_API_URL = https://cloudcost-api.onrender.com
   ```
   (Replace with your actual backend URL from Part 2, Step 4)

5. Click **Create Static Site**
6. Wait 3-5 minutes
7. ✅ Your frontend will be live at: `https://cloudcost-app.onrender.com`

### Step 2: Final CORS Update
Now that you have your frontend URL:

1. Go back to your backend service (`cloudcost-api`)
2. Go to **Environment** tab
3. Find `CORS_ORIGINS` variable
4. Click **Edit**
5. Update to include your frontend URL:
   ```
   https://cloudcost-api.onrender.com,https://cloudcost-app.onrender.com,http://localhost:5173
   ```
6. Click **Save Changes**

---

## Part 4: Test Everything

### Backend Health Check
```bash
curl https://cloudcost-api.onrender.com/health
```
**Expected**: `{"status": "healthy", ...}`

### Frontend
1. Open: `https://cloudcost-app.onrender.com`
2. Should see the landing page
3. Click **Login**
4. Register a new account
5. ✅ Success!

---

## Part 5: Auto-Deploy Setup

### Already Done!
Render automatically:
- Watches your GitHub repo
- Deploys on every push to `main`
- Shows build logs in real-time
- Notifies you of deployment status

To trigger a deploy:
```bash
git add .
git commit -m "Update app"
git push origin main
```

---

## Important Notes

### Free Tier Limitations
- **Backend**: Spins down after 15 minutes of inactivity (first request will be slow, ~30s)
- **PostgreSQL**: Free for 90 days, then $7/month (or migrate to Neon - free forever)
- **Frontend**: Always instant (it's just static files)

### When Free PostgreSQL Expires (Day 85)
We'll migrate to Neon (free forever):
1. Go to https://neon.tech
2. Sign up with GitHub
3. Create a database
4. Copy connection string
5. Update `DATABASE_URL` in Render backend environment variables
6. No code changes needed!

### Monitor Your Apps
1. Go to Render dashboard
2. Each service shows:
   - Live logs
   - Deploy history
   - Metrics
   - Health status

---

## Troubleshooting

### Backend Not Starting
1. Check logs: Render dashboard → Service → **Logs** tab
2. Common issues:
   - Missing environment variables
   - Wrong `DATABASE_URL` format
   - Database not ready (wait 2 more minutes)

### Frontend Shows 404 Errors
1. Check `VITE_API_URL` in frontend environment variables
2. Make sure backend is healthy first
3. Check CORS settings in backend

### Database Connection Errors
1. Use **Internal Database URL** (not External)
2. Ensure backend and database are in **same region**
3. Check database status (should be green/active)

### Redis Connection Errors
1. Double-check Upstash connection string format
2. Make sure token doesn't have spaces
3. Test in Upstash console first

---

## Quick Command Reference

### View Backend Logs
```bash
# In Render dashboard
Go to Service → Logs tab
```

### Trigger Manual Deploy
```bash
# In Render dashboard
Go to Service → Manual Deploy → Deploy latest commit
```

### Rollback to Previous Version
```bash
# In Render dashboard
Go to Service → Events → Click previous deploy → Rollback
```

---

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| Render Backend | **$0** | Free tier (750 hrs/month) |
| Render Frontend | **$0** | Free forever |
| Render PostgreSQL | **$0** | Free for 90 days |
| Upstash Redis | **$0** | Free forever (10K commands/day) |
| GitHub (new account) | **$0** | Free forever |
| **TOTAL** | **$0/month** | For 90 days |

After 90 days, either:
- Pay $7/month for Render PostgreSQL
- Or migrate to Neon (free forever) - 5 minutes

---

## Next Steps

1. ✅ Deploy backend (Part 2)
2. ✅ Deploy frontend (Part 3)
3. ✅ Test everything (Part 4)
4. 🎉 Share your live app URL!
5. (Optional) Set up custom domain

---

## Need Help?

Just ask! I'm here to help with:
- Any error messages you see
- Environment variable questions
- Database connection issues
- Frontend-backend connection problems

Good luck! 🚀
