#!/bin/bash
# Configure Nginx and Supervisor for GenHook
set -e

echo "🔧 Configuring services..."

# Create log directories
sudo mkdir -p /var/log/genhook
sudo chown genhook:genhook /var/log/genhook

# Configure Nginx
sudo cp /opt/genhook/backend/deploy/nginx.conf /etc/nginx/sites-available/genhook
sudo ln -sf /etc/nginx/sites-available/genhook /etc/nginx/sites-enabled/genhook
sudo rm -f /etc/nginx/sites-enabled/default

# Add rate limiting to main nginx.conf (if not already present)
if ! grep -q "limit_req_zone.*webhook_limit" /etc/nginx/nginx.conf; then
    echo "Adding rate limiting configuration to nginx.conf..."
    sudo sed -i '/http {/a\    # GenHook rate limiting\n    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=100r/m;' /etc/nginx/nginx.conf
fi

# Test nginx configuration
sudo nginx -t

# Configure Supervisor
sudo cp /opt/genhook/backend/deploy/supervisor.conf /etc/supervisor/conf.d/genhook.conf

# Make scripts executable
chmod +x /opt/genhook/backend/deploy/monitor.sh
chmod +x /opt/genhook/backend/deploy/check_status.sh
chmod +x /opt/genhook/backend/deploy/setup_services.sh

# Reload services
sudo systemctl reload nginx
sudo supervisorctl reread
sudo supervisorctl update

# Start GenHook
sudo supervisorctl start genhook
sudo supervisorctl start genhook-monitor

echo "✅ Services configured and started!"
echo ""
echo "🔍 Service Status:"
sudo supervisorctl status
echo ""
echo "📊 Check logs:"
echo "  Application: tail -f /var/log/genhook/app.log"
echo "  Monitor: tail -f /var/log/genhook/monitor.log"
echo "  Nginx: tail -f /var/log/nginx/genhook_access.log"