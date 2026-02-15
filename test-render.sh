#!/bin/bash
# Quick test script for your deployed Render API

# Replace with your actual Render URL
RENDER_URL="https://jobpulse-api.onrender.com"

echo "🔍 Testing Render Deployment..."
echo "================================"
echo ""

echo "1. Testing Health Endpoint..."
curl -s "$RENDER_URL/health" | python3 -m json.tool
echo ""

echo "2. Testing API Root..."
curl -s "$RENDER_URL/api/health" | python3 -m json.tool
echo ""

echo "3. Checking if service is responsive..."
if curl -s --head "$RENDER_URL/health" | head -n 1 | grep "200" > /dev/null; then
    echo "✅ Service is UP and responding"
else
    echo "❌ Service is DOWN or not responding"
    echo "   → Service may be sleeping (free tier)"
    echo "   → Wait 30-60 seconds and try again"
fi
echo ""

echo "================================"
echo "Next steps:"
echo "1. Check Render logs for errors"
echo "2. Verify environment variables are set"
echo "3. Make sure Gmail account is connected"
echo "================================"
