# 🕐 Setting Up Spot Price Collection Cron Job in Render

## Current Status
❌ **Cron Job NOT Running** - Needs to be created manually in Render dashboard

## What You Need to Do

### Option 1: Use Render Blueprint (Easiest)

1. **Go to Render Dashboard:**
   - https://dashboard.render.com/

2. **Create New → Blueprint:**
   - Click "New +" → "Blueprint"
   - Connect your GitHub repo: `KadaliAswinkumar/cloudcost-optimizer`
   - Select branch: `main`
   - Render will detect `render.yaml` automatically

3. **Review Services:**
   - You should see:
     - ✅ `cloudcost-api` (Web Service) - Already exists
     - ✅ `spot-price-collector` (Cron Job) - **NEW, needs creation**
     - ✅ `cloudcost-db` (PostgreSQL) - Already exists

4. **Apply Blueprint:**
   - Click "Apply"
   - Render will create the missing cron job

---

### Option 2: Create Cron Job Manually

1. **Go to Render Dashboard:**
   - https://dashboard.render.com/

2. **Click "New +" → "Cron Job"**

3. **Configure:**
   ```
   Name: spot-price-collector
   Environment: Python
   Runtime: Python 3.11.0
   
   Build Command:
   pip install -r requirements.txt
   
   Command:
   export PYTHONPATH=/opt/render/project/src:$PYTHONPATH && python scripts/collect_spot_prices_hourly.py
   
   Schedule: 0 0 * * 0
   (Every Sunday at midnight UTC)
   
   Branch: main
   Root Directory: (leave empty)
   ```

4. **Environment Variables:**
   Add these from your existing `cloudcost-api` service:
   - `PYTHON_VERSION` = `3.11.0`
   - `DATABASE_URL` = (Link to cloudcost-db)
   - `AWS_ACCESS_KEY_ID` = (Your AWS key)
   - `AWS_SECRET_ACCESS_KEY` = (Your AWS secret)

5. **Create Service**

---

## What the Cron Job Does

### Script: `scripts/collect_spot_prices_hourly.py`

**Collects real spot prices from:**
- ✅ **AWS**: Uses `boto3.describe_spot_price_history` API
- ✅ **Azure**: Uses Azure Retail Prices API  
- ✅ **GCP**: Calculates from on-demand prices (70% discount)

**Stores in:** `spot_price_history` table

**Example data:**
```sql
provider | instance_type | region      | zone          | spot_price | timestamp
---------|---------------|-------------|---------------|------------|--------------------
aws      | t3.medium     | us-east-1   | us-east-1a    | 0.0416     | 2026-02-03 00:00:00
aws      | t3.medium     | us-east-1   | us-east-1b    | 0.0418     | 2026-02-03 00:00:00
azure    | Standard_D2s  | eastus      | NULL          | 0.096      | 2026-02-03 00:00:00
```

---

## Timeline for Historical Data

### Week 1 (Now):
- ❌ No historical data yet
- ⚠️  Spot Intelligence shows "Limited data" message

### Week 2 (After 1st run):
- ✅ 1 data point per instance
- ⚠️  Still not enough for trends

### Week 4 (After 4 runs):
- ✅ 4 weeks of data
- ✅ Can show basic price trends
- ✅ Volatility calculations more accurate

### Week 12+ (After 12 runs):
- ✅ 12+ weeks of data
- ✅ Full historical price charts
- ✅ Accurate interruption predictions
- ✅ Industry-leading Spot Intelligence! 🎉

---

## How to Verify It's Working

### 1. Check Cron Job Status
In Render dashboard → Cron Jobs → `spot-price-collector`:
- Last run status
- Next scheduled run
- Logs from previous runs

### 2. Check Database
After first run (next Sunday), you should have:
```sql
SELECT COUNT(*) FROM spot_price_history;
-- Should return 30,000+ records
```

### 3. Test API
After first run:
```bash
curl -X POST https://cloudcost-api.onrender.com/api/v1/spot-intelligence/analyze \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", "instance_type": "t3.medium", "region": "us-east-1"}'
```

Should return:
```json
{
  "success": true,
  "historical_prices": [...],  // Real data!
  "interruption_frequency": "...",
  "best_launch_times": [...]
}
```

---

## Render Cron Job Costs

**Free Tier:**
- 400 minutes/month for cron jobs
- Our job runs ~5-10 minutes per week
- **Total usage:** ~40 minutes/month
- ✅ **Well within free tier!**

---

## Manual Testing (Before Cron Job Runs)

You can manually trigger the script:

```bash
# SSH into your Render instance (if possible)
cd /opt/render/project/src
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH
python scripts/collect_spot_prices_hourly.py
```

Or run locally:
```bash
cd /Users/aswinkumar/Downloads/Aswin/Startups/cloudcost-optimizer
export DATABASE_URL="your_render_postgres_url"
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
python scripts/collect_spot_prices_hourly.py
```

---

## Next Steps

1. ✅ Create cron job in Render (Option 1 or 2 above)
2. ⏰ Wait for next Sunday (first run)
3. 🔍 Check logs to verify success
4. 📊 After 4 weeks, you'll have industry-leading Spot Intelligence data!

---

## Support

If the cron job fails, check Render logs for:
- Database connection errors
- AWS credential issues
- Module import errors (should be fixed with latest PYTHONPATH fix)
