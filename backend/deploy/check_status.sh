#!/bin/bash
# Simple status check script for GenHook

echo "🔍 GenHook System Status Report"
echo "================================"
echo "Date: $(date)"
echo ""

# Service status
echo "📊 Service Status:"
sudo supervisorctl status
echo ""

# Health check
echo "🏥 Health Check:"
if curl -f -s http://localhost/health > /dev/null; then
    echo "✅ Health check passed"
    curl -s http://localhost/health | python3 -m json.tool
else
    echo "❌ Health check failed"
fi
echo ""

# Recent logs
echo "📝 Recent Application Logs:"
tail -10 /var/log/genhook/app.log
echo ""

# Disk usage
echo "💾 Disk Usage:"
df -h /
echo ""

# Memory usage
echo "🧠 Memory Usage:"
free -h
echo ""

# Recent webhook activity
echo "🔗 Recent Webhook Activity:"
sudo tail -5 /var/log/nginx/genhook_access.log
echo ""

echo "✅ Status check complete"