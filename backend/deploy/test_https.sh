#!/bin/bash

# Test HTTPS setup for GenHook

if [ -z "$1" ]; then
    echo "❌ Usage: ./test_https.sh your-domain.com"
    exit 1
fi

DOMAIN="$1"

echo "🧪 Testing HTTPS setup for GenHook..."
echo "🌐 Domain: $DOMAIN"
echo ""

# Test 1: SSL Certificate
echo "1️⃣ Testing SSL Certificate..."
if openssl s_client -connect $DOMAIN:443 -servername $DOMAIN < /dev/null 2>/dev/null | grep -q "Verify return code: 0"; then
    echo "✅ SSL certificate is valid"
else
    echo "❌ SSL certificate issues detected"
fi

# Test 2: Health endpoint
echo ""
echo "2️⃣ Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -k "https://$DOMAIN/health")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health endpoint responding: $HEALTH_RESPONSE"
else
    echo "❌ Health endpoint not responding properly"
    echo "   Response: $HEALTH_RESPONSE"
fi

# Test 3: Meraki webhook endpoint
echo ""
echo "3️⃣ Testing Meraki Webhook Endpoint..."
TEST_PAYLOAD='{
    "alertType": "Device down",
    "deviceName": "Test-Switch-01",
    "deviceSerial": "Q2XX-XXXX-XXXX",
    "networkName": "Test Network",
    "networkUrl": "https://dashboard.meraki.com/o/12345/manage/organization/overview"
}'

WEBHOOK_RESPONSE=$(curl -s -k -X POST "https://$DOMAIN/webhook/meraki" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD")

if echo "$WEBHOOK_RESPONSE" | grep -q "success"; then
    echo "✅ Meraki webhook endpoint working"
    echo "   Generated message: $(echo "$WEBHOOK_RESPONSE" | grep -o '"generated_message":"[^"]*"' | cut -d'"' -f4)"
else
    echo "❌ Meraki webhook endpoint issues"
    echo "   Response: $WEBHOOK_RESPONSE"
fi

# Test 4: HTTP to HTTPS redirect
echo ""
echo "4️⃣ Testing HTTP to HTTPS Redirect..."
REDIRECT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/health")
if [ "$REDIRECT_RESPONSE" = "301" ]; then
    echo "✅ HTTP to HTTPS redirect working (301)"
else
    echo "⚠️  HTTP redirect response: $REDIRECT_RESPONSE"
fi

echo ""
echo "🎉 HTTPS testing complete!"
echo ""
echo "📋 Your Meraki webhook URL:"
echo "   https://$DOMAIN/webhook/meraki"
echo ""
echo "🔧 Configure this URL in your Meraki Dashboard:"
echo "   Organization > Alerts > Webhooks > Add webhook"