#!/bin/bash
# Simple health monitoring script for GenHook
set -e

LOG_FILE="/var/log/genhook/monitor.log"
HEALTH_URL="http://localhost:8000/health"
CHECK_INTERVAL=60  # seconds

mkdir -p /var/log/genhook

echo "🔍 GenHook Monitor started at $(date)" >> $LOG_FILE

while true; do
    if curl -f -s $HEALTH_URL > /dev/null; then
        echo "$(date): ✅ Health check passed" >> $LOG_FILE
    else
        echo "$(date): ❌ Health check failed - restarting service" >> $LOG_FILE
        sudo supervisorctl restart genhook
        
        # Wait for restart
        sleep 10
        
        # Check if restart worked
        if curl -f -s $HEALTH_URL > /dev/null; then
            echo "$(date): ✅ Service restarted successfully" >> $LOG_FILE
        else
            echo "$(date): 🚨 CRITICAL: Service failed to restart!" >> $LOG_FILE
            # TODO: Send alert to ops team
        fi
    fi
    
    sleep $CHECK_INTERVAL
done