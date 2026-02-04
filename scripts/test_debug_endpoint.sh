#!/bin/bash
# Test the new debug endpoint to see what's in the database

echo "🔍 CHECKING DATABASE STATUS..."
echo ""

echo "======================================"
echo "DATABASE STATUS"
echo "======================================"
curl -s "https://cloudcost-api.onrender.com/api/v1/debug/database-status" | python3 -m json.tool
echo ""
echo ""

echo "======================================"
echo "PRICING FOR t2.nano"
echo "======================================"
curl -s "https://cloudcost-api.onrender.com/api/v1/debug/pricing-for-instance/aws/t2.nano" | python3 -m json.tool
echo ""
echo ""

echo "======================================"
echo "SUMMARY"
echo "======================================"
echo "If 'on_demand' pricing count = 0 → That's the problem!"
echo "If 'on_demand' pricing count > 0 → Issue is elsewhere"
echo ""
