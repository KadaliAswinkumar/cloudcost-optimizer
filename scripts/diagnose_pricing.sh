#!/bin/bash
# Comprehensive database check

echo "========================================"
echo "DATABASE DIAGNOSTIC"
echo "========================================"
echo ""

echo "1. Checking cloud_pricing table for spot prices..."
curl -s -X POST "https://cloudcost-api.onrender.com/api/v1/spot-intelligence/analyze" \
  -H "Content-Type: application/json" \
  -d '{"provider": "aws", "instance_type": "t2.nano", "region": "us-east-1"}' 2>&1
echo ""
echo ""

echo "2. Checking if instance has pricing attached..."
curl -s "https://cloudcost-api.onrender.com/api/v1/multicloud/instances?provider=aws&instance_type=t2.nano" 2>&1 | python3 -c "import json,sys; d=json.load(sys.stdin); print('Instance count:', d.get('total', 0)); inst = d.get('instances', [{}])[0]; print('Has hourly_price:', 'hourly_price' in inst); print('Price:', inst.get('hourly_price', 'N/A'))"
echo ""
echo ""

echo "3. Testing historical price endpoint (cron job data)..."
curl -s "https://cloudcost-api.onrender.com/api/v1/spot-intelligence/history?provider=aws&instance_type=c5ad.8xlarge&region=us-east-1&days=7" 2>&1 | python3 -m json.tool 2>&1 | head -20
echo ""

echo "========================================"
echo "CONCLUSION:"
echo "- If #1 shows 'No spot pricing': cloud_pricing table is empty"
echo "- If #2 shows price: Pricing attached to instances but not in cloud_pricing"  
echo "- If #3 works: Historical data (cron job) is working"
echo "========================================"
