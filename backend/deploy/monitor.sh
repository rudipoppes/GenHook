#!/bin/bash
# Simple health monitoring script for GenHook
set -e

LOG_FILE="/var/log/genhook/monitor.log"
HEALTH_URL="http://localhost:8000/health"
CHECK_INTERVAL=60  # seconds

# Ensure log file exists and is writable
touch "$LOG_FILE" 2>/dev/null || {
    echo "Warning: Cannot write to $LOG_FILE, using /tmp/genhook-monitor.log"
    LOG_FILE="/tmp/genhook-monitor.log"
    touch "$LOG_FILE"
}

echo "🔍 GenHook Monitor started at $(date)" >> "$LOG_FILE"

while true; do
    if curl -f -s "$HEALTH_URL" > /dev/null 2>&1; then
        echo "$(date): ✅ Health check passed" >> "$LOG_FILE"
    else
        echo "$(date): ❌ Health check failed - logging failure" >> "$LOG_FILE"
        
        # Instead of restarting, just log the failure
        # Supervisor will handle automatic restarts based on its configuration
        echo "$(date): 🚨 Service health check failed - supervisor will handle restart" >> "$LOG_FILE"
        
        # Wait a bit before next check
        sleep 30
    fi
    
    sleep $CHECK_INTERVAL
done