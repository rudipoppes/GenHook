#!/bin/bash

# Fix monitor log file permissions
echo "🔧 Fixing monitor log file permissions..."

# Create the log file with proper permissions
sudo touch /var/log/genhook/monitor.log
sudo chown genhook:genhook /var/log/genhook/monitor.log  
sudo chmod 644 /var/log/genhook/monitor.log

# Restart the monitor service
sudo supervisorctl restart genhook-monitor

echo "✅ Monitor log permissions fixed"
echo "📊 Check monitor status:"
echo "   sudo supervisorctl status genhook-monitor"
echo "   tail -f /var/log/genhook/monitor.log"