# 🚀 FLY.IO MIGRATION GUIDE

**From**: Render  
**To**: Fly.io  
**Why**: Better free tier, global edge, scale to zero  
**Cost**: **$0/month** (within free tier!)

---

## 🎯 **WHAT YOU GET WITH FLY.IO**

### **Free Tier Includes:**
- ✅ **3 shared-cpu-1x VMs** (256 MB RAM each)
- ✅ **3GB persistent volume** storage
- ✅ **160GB bandwidth** per month
- ✅ **Global edge network** (apps deployed worldwide)
- ✅ **Scale to zero** (no cost when idle)
- ✅ **PostgreSQL** (3GB storage free)
- ✅ **Automatic HTTPS** (free SSL)
- ✅ **Auto-scaling** (based on load)

### **What We'll Use:**
```
1. Fly App (API):          FREE (256 MB, scales to zero)
2. Fly PostgreSQL:         FREE (3 GB storage)
3. GitHub Actions (Cron):  FREE (2,000 mins/month)

TOTAL: $0/month! 🎉
```

---

## 📋 **PREREQUISITES**

1. ✅ Fly.io account (free): https://fly.io/app/sign-up
2. ✅ flyctl CLI installed
3. ✅ GitHub account (for cron job)
4. ✅ AWS credentials (optional, for AWS spot prices)

---

## 🛠️ **STEP-BY-STEP MIGRATION**

### **STEP 1: Install Fly CLI** (5 mins)

#### **On Mac:**
```bash
brew install flyctl
```

#### **On Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

#### **On Windows:**
```powershell
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

**Verify installation:**
```bash
flyctl version
```

---

### **STEP 2: Login to Fly.io** (2 mins)

```bash
flyctl auth login
```

This opens browser for authentication.

---

### **STEP 3: Create PostgreSQL Database** (5 mins)

```bash
# Create database (FREE tier)
flyctl postgres create \
  --name cloudcost-db \
  --region iad \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 3

# Save the connection string shown (looks like):
# postgres://user:password@cloudcost-db.internal:5432/cloudcost
```

**IMPORTANT**: Save the connection details shown! You'll need them.

---

### **STEP 4: Create Fly App** (5 mins)

From your project directory:

```bash
# Initialize Fly app (uses fly.toml we created)
flyctl launch --no-deploy

# Answer the prompts:
# App name: cloudcost-optimizer (or your choice)
# Region: iad (or closest to you)
# PostgreSQL: No (we already created it)
# Redis: No (we'll use external if needed)
```

---

### **STEP 5: Set Environment Variables** (5 mins)

```bash
# Set database URL (from STEP 3)
flyctl secrets set DATABASE_URL="postgres://user:password@cloudcost-db.internal:5432/cloudcost"

# Set Groq API key (for CloudCost AI)
flyctl secrets set GROQ_API_KEY="your_groq_api_key"

# Set AWS credentials (optional, for AWS spot prices)
flyctl secrets set AWS_ACCESS_KEY_ID="your_aws_key"
flyctl secrets set AWS_SECRET_ACCESS_KEY="your_aws_secret"

# Set Redis URL (if using external Redis)
# flyctl secrets set REDIS_URL="redis://..."
```

**Get your secrets from Render**:
- Dashboard → Your Service → Environment → Copy values

---

### **STEP 6: Deploy to Fly.io** (10 mins)

```bash
# Deploy the application
flyctl deploy

# Watch the deployment
# This will:
# 1. Build Docker image
# 2. Run migrations
# 3. Fetch initial data
# 4. Start API server
```

**Expected output:**
```
==> Building image
==> Pushing image to registry
==> Creating release
==> Monitoring deployment
 1 desired, 1 placed, 1 healthy, 0 unhealthy

--> v0 deployed successfully!

Visit your app at: https://cloudcost-optimizer.fly.dev
```

---

### **STEP 7: Verify Deployment** (2 mins)

```bash
# Check app status
flyctl status

# View logs
flyctl logs

# Test API
curl https://cloudcost-optimizer.fly.dev/health

# Expected response:
# {"status":"healthy","service":"CloudCost Optimizer","version":"1.0.0"}
```

---

### **STEP 8: Set Up GitHub Actions for Cron** (10 mins)

#### **A. Add Secrets to GitHub**

Go to: `https://github.com/YOUR_USERNAME/cloudcost-optimizer/settings/secrets/actions`

Click **"New repository secret"** for each:

1. **DATABASE_URL**
   - Value: (Fly PostgreSQL connection string from STEP 3)
   
2. **AWS_ACCESS_KEY_ID** (optional)
   - Value: (Your AWS access key)
   
3. **AWS_SECRET_ACCESS_KEY** (optional)
   - Value: (Your AWS secret)

#### **B. Enable GitHub Actions**

1. Go to: `https://github.com/YOUR_USERNAME/cloudcost-optimizer/actions`
2. Click **"I understand my workflows, go ahead and enable them"**
3. Find **"Collect Spot Prices (Hourly)"** workflow
4. Click **"Enable workflow"**

#### **C. Test Manual Trigger**

1. Click **"Run workflow"** dropdown
2. Click **"Run workflow"** button
3. Wait ~2 minutes
4. Check logs to verify collection worked

**Expected logs:**
```
⏰ HOURLY SPOT PRICE COLLECTION
📊 AWS: Collected 1,234 spot prices
📊 GCP: Collected 567 preemptible prices
📊 Azure: Collected 890 spot prices
💾 Stored 2,691 historical price points
✅ COLLECTION COMPLETE
```

---

### **STEP 9: Update Frontend API URL** (5 mins)

Update your frontend environment variable:

#### **For GitHub Pages:**

Update `frontend/.env.production`:
```bash
VITE_API_URL=https://cloudcost-optimizer.fly.dev
```

Then rebuild and deploy:
```bash
cd frontend
npm run build
git add dist
git commit -m "Update API URL to Fly.io"
git push
```

---

### **STEP 10: Migrate Data (Optional)** (10 mins)

If you have existing data on Render you want to keep:

```bash
# Export from Render PostgreSQL
pg_dump YOUR_RENDER_DB_URL > backup.sql

# Import to Fly PostgreSQL
cat backup.sql | flyctl postgres connect -a cloudcost-db
```

**OR** just let the scripts re-fetch everything (recommended for fresh start).

---

## ✅ **VERIFICATION CHECKLIST**

After migration, verify everything works:

- [ ] **API Health**: `curl https://your-app.fly.dev/health` returns 200
- [ ] **Database**: API returns instance data
- [ ] **Spot Intelligence**: Feature works (may show "collecting data" initially)
- [ ] **CloudCost AI**: Chat feature works
- [ ] **Recommendations**: Returns results
- [ ] **GitHub Actions**: Cron job runs successfully (check Actions tab)
- [ ] **Frontend**: Connects to new API URL

---

## 📊 **MONITORING**

### **View Logs:**
```bash
flyctl logs
```

### **Check Status:**
```bash
flyctl status
```

### **Database Stats:**
```bash
flyctl postgres db list -a cloudcost-db
```

### **Scaling (if needed):**
```bash
# Scale to 2 instances
flyctl scale count 2

# Scale back to 1
flyctl scale count 1

# Scale to zero (stops app, restarts on request)
flyctl scale count 0
```

---

## 💰 **COST BREAKDOWN**

### **Free Tier Limits:**
```
✅ 3 shared VMs (256 MB each)      = FREE
✅ 3GB persistent volume            = FREE
✅ 160GB bandwidth/month            = FREE
✅ PostgreSQL 3GB storage           = FREE
✅ GitHub Actions 2,000 mins        = FREE

Our usage:
• 1 VM (256 MB)                     ✅ Within limit
• 1 GB database                     ✅ Within limit
• ~10 GB bandwidth/month            ✅ Within limit
• 120 mins GitHub Actions/month     ✅ Within limit

TOTAL: $0/month! 🎉
```

### **If You Exceed Free Tier:**
```
Extra VM: ~$2/month
Extra storage: ~$0.15/GB/month
Extra bandwidth: ~$0.02/GB
```

**For your use case**: You'll stay FREE! ✅

---

## 🔄 **ROLLBACK PLAN**

If something goes wrong, you can easily rollback:

### **Option 1: Rollback on Fly.io**
```bash
# List releases
flyctl releases

# Rollback to previous version
flyctl releases rollback
```

### **Option 2: Back to Render**
Your Render deployment is still there! Just:
1. Re-enable auto-deploy on Render
2. Update frontend API URL back to Render
3. Wait for Render to redeploy

---

## 🎯 **ADVANTAGES OVER RENDER**

| Feature | Fly.io | Render |
|---------|--------|--------|
| **Cost** | FREE | $7/mo (database) |
| **Scale to Zero** | ✅ Yes | ⚠️  Limited |
| **Global Edge** | ✅ Yes | ❌ No |
| **Boot Time** | ~1s | ~15s |
| **Free Database** | ✅ 3GB | ❌ Min $7/mo |
| **Free Bandwidth** | 160GB | 100GB |
| **Cron Jobs** | Via GitHub | Native but limited |

---

## 🐛 **TROUBLESHOOTING**

### **Problem**: Deployment fails with "out of memory"
**Solution**: 
```bash
# Check logs
flyctl logs

# If needed, scale up (costs money)
flyctl scale vm shared-cpu-1x --memory 512
```

### **Problem**: Database connection fails
**Solution**:
```bash
# Check database status
flyctl postgres db list -a cloudcost-db

# Test connection
flyctl postgres connect -a cloudcost-db
```

### **Problem**: App not responding
**Solution**:
```bash
# Check status
flyctl status

# Restart app
flyctl apps restart cloudcost-optimizer
```

### **Problem**: GitHub Actions cron not running
**Solution**:
1. Check GitHub Actions tab for errors
2. Verify secrets are set correctly
3. Test with manual trigger first

---

## 📝 **POST-MIGRATION CLEANUP**

After successful migration:

1. **Stop Render services** (to avoid charges):
   ```
   Render Dashboard → Your Service → Settings → Delete Service
   ```

2. **Export any important data** before deleting Render database

3. **Update documentation** with new Fly.io URLs

4. **Remove `render.yaml`** (no longer needed):
   ```bash
   git rm render.yaml
   git commit -m "Remove Render config, migrated to Fly.io"
   ```

---

## 🎉 **SUCCESS!**

You're now running on Fly.io with:
- ✅ **$0/month cost** (within free tier)
- ✅ **Global edge** (fast everywhere)
- ✅ **Scale to zero** (efficient)
- ✅ **Professional setup** (like Vantage.sh)
- ✅ **Real historical data** (via GitHub Actions cron)

**Welcome to the FREE tier! 🚀**

---

## 📚 **HELPFUL RESOURCES**

- **Fly.io Docs**: https://fly.io/docs/
- **Fly CLI Reference**: https://fly.io/docs/flyctl/
- **Fly PostgreSQL**: https://fly.io/docs/postgres/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Support**: Fly.io community forum

---

**Need help?** Check the Fly.io community forum or their excellent documentation!
