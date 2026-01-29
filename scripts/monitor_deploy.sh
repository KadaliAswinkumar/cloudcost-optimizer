#!/bin/bash

API_URL="https://cloudcost-api.onrender.com"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 MONITORING RENDER DEPLOYMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Pushed to GitHub at: $(date)"
echo "Render typically takes 8-10 minutes to:"
echo "  1. Pull latest code from GitHub"
echo "  2. Build Docker image"
echo "  3. Run migrations (alembic upgrade head)"
echo "  4. Run data fetch (python fetch_real_data.py)"
echo "  5. Start the server"
echo ""
echo "Checking every 30 seconds..."
echo ""

for i in {1..25}; do
  echo "━━━━ Attempt $i/25 ($(($i * 30))s elapsed) ━━━━"
  
  # Test health
  HEALTH=$(curl -sk "$API_URL/health" 2>&1)
  
  if echo "$HEALTH" | grep -q "healthy"; then
    echo "✅ API is healthy!"
    
    # Check AWS pricing status
    AWS_STATS=$(curl -sk "$API_URL/api/v1/multicloud/stats?provider=aws" 2>&1)
    AWS_REGIONS=$(echo "$AWS_STATS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_regions', 0))" 2>/dev/null || echo "0")
    AWS_PRICING=$(echo "$AWS_STATS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total_pricing_records', 0))" 2>/dev/null || echo "0")
    
    echo "   AWS Regions: $AWS_REGIONS"
    echo "   AWS Pricing: $AWS_PRICING"
    
    if [ "$AWS_PRICING" -gt "0" ]; then
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "🎉 SUCCESS! AWS PRICING IS NOW AVAILABLE!"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "Full stats:"
      curl -sk "$API_URL/api/v1/multicloud/stats" | python3 -m json.tool
      echo ""
      echo "✅ ALL FIXES DEPLOYED SUCCESSFULLY!"
      break
    else
      echo "   ⏳ Still waiting for AWS pricing data..."
    fi
  else
    echo "⏳ Deploying... (server not responding yet)"
  fi
  
  if [ $i -lt 25 ]; then
    sleep 30
  fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Once deployed, test these pages:"
echo "  1. Instance Finder - prices should show"
echo "  2. Dashboard - AWS regions should show correct count"
echo "  3. Compare Clouds - AWS should appear in graph"
echo "  4. Recommendations - AWS price should show"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
