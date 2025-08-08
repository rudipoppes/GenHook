# GenHook Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying GenHook to production with the web configuration interface. GenHook is designed to be production-ready with proper security, monitoring, and scalability considerations.

## Architecture Overview

```
Internet → Load Balancer (443) → Reverse Proxy → GenHook (8000) → SL1 API
                                       ↓
                               Web Interface (/config)
```

## Pre-Production Checklist

### ✅ Code Readiness
- [ ] All debug statements removed
- [ ] Error handling implemented
- [ ] Configuration externalized
- [ ] Logging configured
- [ ] Health checks working

### ✅ Security
- [ ] HTTPS/SSL certificates configured
- [ ] Webhook signature verification enabled
- [ ] Rate limiting implemented
- [ ] Access controls for web interface
- [ ] SL1 credentials secured

### ✅ Configuration
- [ ] Production webhook configurations tested
- [ ] SL1 API connectivity verified
- [ ] Web interface configurations validated
- [ ] Backup strategy implemented

## Port Configuration Strategy

**GenHook uses a configuration-driven approach - no code changes required!**

### Configuration Files
- **Development**: `backend/config/app-config.ini` (default port 8000)
- **Production**: `backend/config/app-config.prod.ini` (automatically detected if exists)

### Port Configuration Options

#### Option 1: Direct HTTPS (Port 443)
Create production config for direct HTTPS:
```ini
# backend/config/app-config.prod.ini
[server]
host = 0.0.0.0
port = 443
reload = false
```

**Benefits**: Direct HTTPS, no reverse proxy needed
**Requirements**: SSL certificates, root privileges for port 443

#### Option 2: Reverse Proxy (Recommended)
Keep default port 8000, use nginx/Apache for HTTPS:
```ini
# backend/config/app-config.ini (unchanged)
[server]
host = 0.0.0.0
port = 8000
reload = false
```

**Benefits**: Better security, easier SSL management, load balancing
**Setup**: Configure nginx/Apache to proxy 443 → 8000

#### Option 3: Custom Port
Use any available port:
```ini
# backend/config/app-config.prod.ini
[server]
host = 0.0.0.0
port = 9000  # or any port
reload = false
```

### Configuration Priority
1. If `app-config.prod.ini` exists → production config used
2. Otherwise → `app-config.ini` (development) used
3. **No code modification ever required**

## Deployment Options

### Option 1: AWS EC2 with Application Load Balancer (Recommended)

#### Infrastructure Setup

1. **EC2 Instance Configuration**
   ```bash
   # Instance Type: t3.medium (2 vCPU, 4GB RAM) for moderate load
   # Instance Type: c5.large (2 vCPU, 4GB RAM) for high load
   # OS: Amazon Linux 2 or Ubuntu 20.04 LTS
   ```

2. **Security Group Configuration**
   ```
   Inbound Rules:
   - Port 22 (SSH): Your IP only
   - Port 8000: ALB Security Group only
   - Port 443: ALB Security Group only (if using direct SSL)
   
   Outbound Rules:
   - Port 443 (HTTPS): SL1 API endpoints
   - Port 80/443: Package updates
   ```

3. **Application Load Balancer Setup**
   ```
   Target Group: GenHook instances on port 8000
   Health Check: /health
   SSL Certificate: AWS Certificate Manager
   ```

#### Installation Script

```bash
#!/bin/bash
# GenHook Production Installation Script

# Update system
sudo yum update -y  # Amazon Linux
# sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.9+
sudo yum install python3 python3-pip git -y  # Amazon Linux
# sudo apt install python3 python3-pip git -y  # Ubuntu

# Create genhook user
sudo useradd -m -s /bin/bash genhook
sudo mkdir -p /opt/genhook
sudo chown genhook:genhook /opt/genhook

# Clone repository
sudo -u genhook git clone https://github.com/rudipoppes/GenHook.git /opt/genhook
cd /opt/genhook

# Create virtual environment
sudo -u genhook python3 -m venv venv
sudo -u genhook ./venv/bin/pip install -r backend/requirements.txt

# Create production configuration
sudo -u genhook cp backend/config/app-config.ini.example backend/config/app-config.ini
sudo -u genhook cp backend/config/web-config.ini.example backend/config/web-config.ini

# Configure port for production (IMPORTANT: Configuration-driven approach)
# Option 1: Direct HTTPS on port 443 (requires SSL certs)
sudo -u genhook cp backend/config/app-config.prod.ini.example backend/config/app-config.prod.ini
sudo -u genhook sed -i 's/port = 8000/port = 443/' backend/config/app-config.prod.ini

# Option 2: Keep port 8000 for reverse proxy (recommended)
# No changes needed - use default port 8000 with nginx/ALB handling HTTPS

# Create systemd service
sudo tee /etc/systemd/system/genhook.service > /dev/null <<EOF
[Unit]
Description=GenHook Webhook Receiver
After=network.target

[Service]
Type=simple
User=genhook
Group=genhook
WorkingDirectory=/opt/genhook/backend
Environment=PYTHONPATH=/opt/genhook/backend
ExecStart=/opt/genhook/venv/bin/python main.py
Restart=always
RestartSec=3

# Environment variables
Environment="SL1_API_URL=https://your-sl1-instance.com/api/alert"
Environment="SL1_USERNAME=your_sl1_user"
Environment="SL1_PASSWORD=your_sl1_password"
Environment="WEB_INTERFACE_ENABLED=true"

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl enable genhook
sudo systemctl start genhook
```

#### Nginx Reverse Proxy Configuration

```bash
# Install Nginx
sudo yum install nginx -y  # Amazon Linux
# sudo apt install nginx -y  # Ubuntu

# Create configuration
sudo tee /etc/nginx/sites-available/genhook > /dev/null <<EOF
server {
    listen 80;
    server_name your-genhook-domain.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-genhook-domain.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/genhook.crt;
    ssl_certificate_key /etc/ssl/private/genhook.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Webhook endpoints (public)
    location /webhook/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Rate limiting
        limit_req zone=webhook_limit burst=10 nodelay;
    }

    # Health check (public)
    location /health {
        proxy_pass http://localhost:8000;
        access_log off;
    }

    # Web interface (restrict access)
    location /config {
        # Restrict to specific IPs
        allow 10.0.0.0/8;    # Private networks
        allow 192.168.0.0/16;
        deny all;

        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files for web interface
    location /static/ {
        # Same IP restrictions as /config
        allow 10.0.0.0/8;
        allow 192.168.0.0/16;
        deny all;

        proxy_pass http://localhost:8000;
    }

    # Block other access
    location / {
        return 404;
    }
}

# Rate limiting zone
http {
    limit_req_zone \$binary_remote_addr zone=webhook_limit:10m rate=10r/s;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/genhook /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Option 2: Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash genhook

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Set ownership
RUN chown -R genhook:genhook /app
USER genhook

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["python", "main.py"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  genhook:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SL1_API_URL=https://your-sl1-instance.com/api/alert
      - SL1_USERNAME=your_sl1_user
      - SL1_PASSWORD=your_sl1_password
      - WEB_INTERFACE_ENABLED=true
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - genhook
    restart: unless-stopped
```

## Configuration Management

### Production Configuration Files

1. **Backend Configuration (`backend/config/app-config.ini`)**
   ```ini
   [server]
   host = 0.0.0.0
   port = 8000
   log_level = INFO

   [sl1]
   api_url = ${SL1_API_URL}
   username = ${SL1_USERNAME}
   password = ${SL1_PASSWORD}
   timeout = 30
   retry_attempts = 3
   ```

2. **Web Interface Configuration (`backend/config/web-config.ini`)**
   ```ini
   [ui]
   enabled = true
   max_analysis_depth = 3
   timeout_seconds = 30

   [features]
   backup_configs = true
   # Dynamic configuration loading enabled - no restart needed

   [paths]
   config_file_path = config/webhook-config.ini
   backup_directory = config/backups
   ```

3. **Webhook Configuration (`backend/config/webhook-config.ini`)**
   ```ini
   [webhooks]
   # Your production webhook configurations
   github = action,pull_request{title,user{login}},repository{name}::GitHub $action$ on $repository.name$: "$pull_request.title$" by $pull_request.user.login$
   ```

## Monitoring and Logging

### CloudWatch Integration (AWS)

```python
# Add to main.py for AWS CloudWatch logging
import boto3
import logging
from datetime import datetime

# Configure CloudWatch logging
cloudwatch_logs = boto3.client('logs')

class CloudWatchHandler(logging.Handler):
    def __init__(self, log_group, log_stream):
        super().__init__()
        self.log_group = log_group
        self.log_stream = log_stream
        
    def emit(self, record):
        log_entry = {
            'timestamp': int(record.created * 1000),
            'message': self.format(record)
        }
        
        try:
            cloudwatch_logs.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[log_entry]
            )
        except Exception as e:
            print(f"Failed to send log to CloudWatch: {e}")

# Usage
if os.getenv('AWS_CLOUDWATCH_ENABLED'):
    cloudwatch_handler = CloudWatchHandler('genhook', 'application')
    logger.addHandler(cloudwatch_handler)
```

### Metrics and Alerts

```bash
# CloudWatch Custom Metrics
aws cloudwatch put-metric-data \
    --namespace "GenHook" \
    --metric-data MetricName=WebhooksProcessed,Value=1,Unit=Count

# CloudWatch Alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "GenHook-High-Error-Rate" \
    --alarm-description "GenHook error rate is too high" \
    --metric-name ErrorRate \
    --namespace GenHook \
    --statistic Average \
    --period 300 \
    --threshold 5.0 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2
```

## Security Configuration

### SSL/TLS Setup

```bash
# Generate SSL certificate (Let's Encrypt)
sudo certbot --nginx -d your-genhook-domain.com

# Or use self-signed for testing
openssl req -x509 -newkey rsa:4096 -keyout genhook.key -out genhook.crt -days 365 -nodes
```

### Access Control

```nginx
# IP-based access control in nginx
location /config {
    allow 203.0.113.0/24;  # Your office IP range
    allow 198.51.100.0/24; # Your VPN IP range
    deny all;
}
```

### Webhook Signature Verification

```python
# Add to webhook endpoints for signature verification
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Backup and Recovery

### Automated Backups

```bash
#!/bin/bash
# Backup script for GenHook configurations

BACKUP_DIR="/opt/genhook-backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONFIG_DIR="/opt/genhook/backend/config"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup configurations
tar -czf $BACKUP_DIR/genhook-config-$DATE.tar.gz -C $CONFIG_DIR .

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/genhook-config-$DATE.tar.gz s3://your-backup-bucket/genhook/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "genhook-config-*.tar.gz" -mtime +30 -delete
```

### Recovery Procedure

```bash
# Stop service
sudo systemctl stop genhook

# Restore configuration
cd /opt/genhook/backend/config
sudo -u genhook tar -xzf /path/to/backup.tar.gz

# Start service
sudo systemctl start genhook
```

## Performance Tuning

### Application Settings

```ini
# In app-config.ini
[performance]
worker_processes = 4
max_connections = 1000
keepalive_timeout = 65
client_max_body_size = 10M
```

### System Tuning

```bash
# Increase file descriptor limits
echo "genhook soft nofile 65536" >> /etc/security/limits.conf
echo "genhook hard nofile 65536" >> /etc/security/limits.conf

# Tune network settings
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
echo "net.ipv4.tcp_max_syn_backlog = 65536" >> /etc/sysctl.conf
sysctl -p
```

## Troubleshooting

### Common Issues

1. **Port 8000 Already in Use**
   ```bash
   sudo netstat -tulpn | grep :8000
   sudo systemctl stop genhook
   ```

2. **SL1 API Connection Issues**
   ```bash
   curl -X POST https://your-sl1-instance.com/api/alert \
        -H "Content-Type: application/json" \
        -u username:password \
        -d '{"message": "Test"}'
   ```

3. **Web Interface Not Loading**
   ```bash
   curl http://localhost:8000/config
   sudo journalctl -u genhook -f
   ```

### Log Analysis

```bash
# Check application logs
sudo journalctl -u genhook -f

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Check GenHook application logs
tail -f /opt/genhook/logs/application.log
```

## Maintenance

### Updates

```bash
# Update GenHook
cd /opt/genhook
sudo -u genhook git pull origin main
sudo -u genhook ./venv/bin/pip install -r backend/requirements.txt --upgrade
sudo systemctl restart genhook
```

### Health Monitoring

```bash
# Health check script
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "GenHook health check failed: $RESPONSE"
    sudo systemctl restart genhook
    # Send alert notification
fi
```

This guide provides a comprehensive foundation for deploying GenHook in production with proper security, monitoring, and maintenance procedures.