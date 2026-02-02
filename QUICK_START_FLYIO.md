# ⚡ QUICK START - FLY.IO MIGRATION

**Time**: 30 minutes  
**Cost**: **$0/month** (FREE!)  
**Difficulty**: Easy 🟢

---

## 🎯 **WHAT YOU'LL GET**

```
┌─────────────────────────────────────┐
│ FREE HOSTING STACK                  │
├─────────────────────────────────────┤
│ Frontend:  GitHub Pages      (FREE) │
│ API:       Fly.io             (FREE) │
│ Database:  Fly PostgreSQL     (FREE) │
│ Cron:      GitHub Actions     (FREE) │
│                                     │
│ TOTAL: $0/month! 🎉                 │
└─────────────────────────────────────┘
```

---

## 🚀 **SUPER QUICK START** (30 mins)

### **1. Install Fly CLI** (2 mins)

```bash
# Mac
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

---

### **2. Login** (1 min)

```bash
flyctl auth login
```

---

### **3. Create Database** (3 mins)

```bash
flyctl postgres create \
  --name cloudcost-db \
  --region iad \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 3
```

**⚠️ SAVE THE CONNECTION STRING!**

---

### **4. Initialize App** (2 mins)

```bash
flyctl launch --no-deploy
```

Answer:
- App name: `cloudcost-optimizer` (or your choice)
- Region: `iad` (or closest to you)
- PostgreSQL: **No** (already created)
- Redis: **No**

---

### **5. Deploy** (5 mins)

```bash
# Easy way - use the script:
./deploy-to-flyio.sh

# Or manual way:
flyctl secrets set DATABASE_URL="your_connection_string"
flyctl secrets set GROQ_API_KEY="your_groq_key"
flyctl deploy
```

---

### **6. Set Up GitHub Actions** (10 mins)

#### **A. Add Secrets to GitHub:**

Go to: Settings → Secrets → Actions → New secret

Add:
- `DATABASE_URL` (from step 3)
- `AWS_ACCESS_KEY_ID` (optional)
- `AWS_SECRET_ACCESS_KEY` (optional)

#### **B. Enable Workflow:**

Go to: Actions → "Collect Spot Prices" → Enable

#### **C. Test:**

Run workflow → "Run workflow" button → Check logs

---

### **7. Update Frontend** (5 mins)

```bash
# frontend/.env.production
VITE_API_URL=https://cloudcost-optimizer.fly.dev

# Rebuild
cd frontend
npm run build

# Deploy
git add dist
git commit -m "Update API URL to Fly.io"
git push
```

---

## ✅ **DONE!**

Test your app:
```bash
curl https://cloudcost-optimizer.fly.dev/health
```

Expected:
```json
{"status":"healthy","service":"CloudCost Optimizer"}
```

---

## 🎉 **YOU'RE LIVE!**

- ✅ API running on Fly.io (FREE)
- ✅ Database on Fly PostgreSQL (FREE)
- ✅ Cron job on GitHub Actions (FREE)
- ✅ **Total cost: $0/month!**

---

## 📚 **DETAILED GUIDE**

For full instructions, troubleshooting, and advanced setup:
→ Read **`FLY_IO_MIGRATION.md`**

---

## 🐛 **TROUBLESHOOTING**

### **App not working?**
```bash
flyctl logs  # Check what went wrong
```

### **Database issues?**
```bash
flyctl postgres db list -a cloudcost-db
```

### **Need to restart?**
```bash
flyctl apps restart cloudcost-optimizer
```

---

## 💡 **PRO TIPS**

1. **Monitor your app**:
   ```bash
   flyctl dashboard  # Opens web dashboard
   ```

2. **Check free tier usage**:
   ```bash
   flyctl platform regions  # See your regions
   flyctl status           # See resource usage
   ```

3. **Scale if needed** (costs money):
   ```bash
   flyctl scale count 2      # 2 instances
   flyctl scale vm shared-cpu-1x --memory 512  # More RAM
   ```

---

## 🎯 **NEXT STEPS**

After migration:

1. ✅ Test all features work
2. ✅ Check GitHub Actions runs
3. ✅ Wait 24 hours for first historical data
4. ✅ Delete Render services (avoid charges)
5. ✅ Celebrate! 🎉

---

**Welcome to Fly.io!** 🚀
