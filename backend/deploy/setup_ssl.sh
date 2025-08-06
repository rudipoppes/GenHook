#!/bin/bash

# GenHook SSL Setup Script
# Configures HTTPS using Let's Encrypt for Meraki webhook requirements

set -e

echo "🔒 Setting up SSL for GenHook..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Get domain name
if [ -z "$1" ]; then
    echo "❌ Usage: sudo ./setup_ssl.sh your-domain.com"
    echo "   Example: sudo ./setup_ssl.sh webhooks.mycompany.com"
    echo ""
    echo "💡 You need a domain name pointing to this server's IP address"
    echo "   You can use a subdomain or get a free domain from providers like:"
    echo "   - Duck DNS (duckdns.org)"
    echo "   - No-IP (noip.com)"
    echo "   - Freenom (freenom.com)"
    exit 1
fi

DOMAIN="$1"

echo "🌐 Setting up SSL for domain: $DOMAIN"

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "📦 Installing Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
else
    echo "✅ Certbot already installed"
fi

# Stop nginx temporarily for certificate generation
echo "⏸️  Stopping nginx temporarily..."
systemctl stop nginx

# Generate SSL certificate
echo "🔐 Generating SSL certificate for $DOMAIN..."
certbot certonly --standalone \
    --agree-tos \
    --non-interactive \
    --email admin@$DOMAIN \
    --domains $DOMAIN

if [ $? -ne 0 ]; then
    echo "❌ SSL certificate generation failed!"
    echo "   Make sure:"
    echo "   1. Domain $DOMAIN points to this server's public IP"
    echo "   2. Port 80 is accessible from the internet"
    echo "   3. No firewall is blocking the connection"
    systemctl start nginx
    exit 1
fi

# Create SSL-enabled nginx configuration
echo "🔧 Creating SSL nginx configuration..."

cat > /etc/nginx/sites-available/genhook << 'EOF'
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;
    
    # Allow Let's Encrypt renewal
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/DOMAIN_PLACEHOLDER/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Rate limiting (applied here in HTTPS server block)
    limit_req zone=webhook_limit burst=50 nodelay;

    # Proxy to GenHook application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Logging
    access_log /var/log/nginx/genhook_ssl_access.log;
    error_log /var/log/nginx/genhook_ssl_error.log;
}
EOF

# Replace domain placeholder
sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/genhook

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration test failed!"
    exit 1
fi

# Start nginx
echo "🚀 Starting nginx with SSL configuration..."
systemctl start nginx

# Set up automatic certificate renewal
echo "🔄 Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet --nginx") | crontab -

# Test SSL setup
echo "🧪 Testing SSL setup..."
sleep 2

if curl -k -s "https://$DOMAIN/health" > /dev/null; then
    echo "✅ SSL setup successful!"
    echo ""
    echo "🎉 HTTPS is now configured for your GenHook server!"
    echo "📍 Your webhook endpoints:"
    echo "   - Health check: https://$DOMAIN/health"
    echo "   - GitHub: https://$DOMAIN/webhook/github"
    echo "   - Meraki: https://$DOMAIN/webhook/meraki"
    echo "   - Stripe: https://$DOMAIN/webhook/stripe"
    echo "   - Slack: https://$DOMAIN/webhook/slack"
    echo ""
    echo "🔒 SSL Certificate Details:"
    echo "   - Domain: $DOMAIN"
    echo "   - Issuer: Let's Encrypt"
    echo "   - Auto-renewal: Enabled (daily check at 12:00)"
    echo ""
    echo "🌐 You can now configure Meraki webhooks to use:"
    echo "   https://$DOMAIN/webhook/meraki"
else
    echo "⚠️  SSL setup completed but health check failed"
    echo "   Check nginx logs: sudo tail -f /var/log/nginx/genhook_ssl_error.log"
fi

echo ""
echo "📋 Next steps:"
echo "1. Update your AWS Security Group to allow HTTPS (port 443)"
echo "2. Configure Meraki webhooks to use https://$DOMAIN/webhook/meraki"
echo "3. Test with: curl https://$DOMAIN/health"