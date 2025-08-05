# GenHook AWS Deployment Guide
**Production-Ready Webhook Processing System**

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Server Installation](#server-installation)
5. [Service Configuration](#service-configuration)
6. [Production Settings](#production-settings)
7. [Testing & Validation](#testing--validation)
8. [External Webhook Configuration](#external-webhook-configuration)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [Security & Backup](#security--backup)
11. [Cost Analysis](#cost-analysis)
12. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for deploying GenHook, a configuration-driven webhook receiver, to AWS EC2. GenHook processes webhooks from multiple services (GitHub, Stripe, Slack, AWS) and forwards formatted alerts to SL1 monitoring systems.

### Architecture
```
Internet → AWS ALB/CloudFront → EC2 Instance → Nginx → GenHook App → SL1 API
```

### Key Features
- **Multi-Service Support**: GitHub, Stripe, Slack, AWS webhooks
- **Configuration-Driven**: No code changes for new webhook types
- **Template-Based Messaging**: Flexible alert generation
- **SL1 Integration**: Direct API integration with retry logic
- **Production-Ready**: Nginx proxy, process management, logging

---

## Prerequisites

### AWS Account Requirements
- Active AWS account with billing enabled
- IAM user with EC2, Security Groups, and optionally Route 53 permissions
- AWS CLI installed and configured locally

### Local Development Environment
- SSH client (Terminal on macOS/Linux, PuTTY on Windows)
- Git repository with GenHook code
- Text editor for configuration files

### Required Knowledge
- Basic Linux command line operations
- SSH key management
- DNS configuration (if using custom domain)

---

## AWS Infrastructure Setup

### Step 1: Create EC2 Security Group

1. Navigate to **EC2 Console → Security Groups → Create Security Group**
2. Configure:
   - **Name**: `genhook-security-group`
   - **Description**: Security group for GenHook webhook server
   - **VPC**: Default VPC (or your preferred VPC)

3. **Inbound Rules**:
   ```
   Type     Protocol  Port  Source      Description
   SSH      TCP       22    Your-IP     SSH access from your IP
   HTTP     TCP       80    0.0.0.0/0   Webhook traffic
   HTTPS    TCP       443   0.0.0.0/0   Webhook traffic (future SSL)
   ```

4. **Outbound Rules**: Leave default (allow all outbound)

### Step 2: Launch EC2 Instance

1. **Navigate to EC2 → Launch Instance**
2. **Configure Instance**:
   - **Name**: `genhook-production`
   - **AMI**: Ubuntu Server 22.04 LTS (Free Tier Eligible)
   - **Instance Type**: `t3.small` (2 vCPU, 2GB RAM)
   - **Key Pair**: Create new or select existing SSH key pair
   - **Security Group**: Select `genhook-security-group` created above
   - **Storage**: 20GB gp3 (default settings)

3. **Advanced Details**:
   - **User Data** (optional - for automated setup):
   ```bash
   #!/bin/bash
   apt update
   apt install -y git curl
   ```

4. **Launch Instance**

### Step 3: Elastic IP (Recommended)

1. **Navigate to EC2 → Elastic IPs → Allocate Elastic IP**
2. **Associate** the Elastic IP with your GenHook instance
3. **Note the Elastic IP** - this will be your webhook endpoint

---

## Server Installation

### Step 1: Connect to Instance

```bash
# Replace with your key file and Elastic IP
ssh -i /path/to/your-key.pem ubuntu@YOUR-ELASTIC-IP
```

### Step 2: Run Installation Script

```bash
# Download installation script
curl -o install_server.sh https://raw.githubusercontent.com/YOUR-USERNAME/GenHook/main/backend/deploy/install_server.sh

# Make executable and run
chmod +x install_server.sh
sudo ./install_server.sh
```

### Installation Script Contents
The script performs the following:
- Updates system packages
- Installs Python 3.11, pip, git, nginx, supervisor
- Creates `genhook` user for security isolation
- Sets up application directory at `/opt/genhook`
- Clones GenHook repository
- Creates Python virtual environment
- Installs Python dependencies

### Step 3: Verify Installation

```bash
# Check application directory
ls -la /opt/genhook/

# Verify Python installation
/opt/genhook/venv/bin/python --version

# Check installed packages
/opt/genhook/venv/bin/pip list
```

---

## Service Configuration

### Step 1: Configure Nginx

Create nginx configuration file:

```bash
sudo nano /etc/nginx/sites-available/genhook
```

Configuration content:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=webhook_limit:10m rate=100r/m;
    limit_req zone=webhook_limit burst=20 nodelay;
    
    # Webhook endpoints
    location /webhook/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
        client_max_body_size 1M;
        
        access_log /var/log/nginx/genhook_webhook.log;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 5s;
        proxy_connect_timeout 2s;
    }
    
    # Block all other paths
    location / {
        return 404;
    }
    
    access_log /var/log/nginx/genhook_access.log;
    error_log /var/log/nginx/genhook_error.log;
}
```

### Step 2: Configure Supervisor

Create supervisor configuration:

```bash
sudo nano /etc/supervisor/conf.d/genhook.conf
```

Configuration content:
```ini
[program:genhook]
command=/opt/genhook/venv/bin/python main.py
directory=/opt/genhook/backend
user=genhook
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/var/log/genhook/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PYTHONPATH="/opt/genhook/backend"

[program:genhook-monitor]
command=/opt/genhook/backend/deploy/monitor.sh
directory=/opt/genhook
user=genhook
autostart=true
autorestart=true
startretries=3
redirect_stderr=true
stdout_logfile=/var/log/genhook/monitor.log
```

### Step 3: Setup Services

```bash
# Create log directories
sudo mkdir -p /var/log/genhook
sudo chown genhook:genhook /var/log/genhook

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/genhook /etc/nginx/sites-enabled/genhook
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Reload services
sudo systemctl reload nginx
sudo supervisorctl reread
sudo supervisorctl update

# Start GenHook services
sudo supervisorctl start genhook
sudo supervisorctl start genhook-monitor
```

---

## Production Settings

### Step 1: Configure Application Settings

```bash
# Switch to genhook user
sudo -u genhook bash
cd /opt/genhook/backend

# Copy and edit production configuration
cp config/app-config.ini config/app-config.prod.ini
nano config/app-config.prod.ini
```

Production configuration template:
```ini
[server]
host = 127.0.0.1  # Nginx will proxy to this
port = 8000
reload = false    # Disable in production

[sl1]
# Your SL1 instance details
api_url = https://your-sl1-server.com/api/alert
username = your_sl1_username
password = your_sl1_password
timeout = 30
retry_attempts = 3

[logging]
level = INFO
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s
file = /var/log/genhook/app.log

[threading]
max_workers = 10     # Conservative for MVP
queue_size = 1000    # Small queue for MVP
processing_timeout = 30
```

### Step 2: Restart Services

The application automatically detects and uses production configuration when `app-config.prod.ini` exists:

```bash
# Restart GenHook service to use production configuration
sudo supervisorctl restart genhook

# Verify it's using production config (check logs)
sudo supervisorctl tail genhook stdout
# Should show: "✅ Using production config: /opt/genhook/backend/config/app-config.prod.ini"
```

### Step 3: Restart Services

```bash
# Restart application with new configuration
sudo supervisorctl restart genhook

# Check status
sudo supervisorctl status
```

---

## Testing & Validation

### Test 1: Health Check

```bash
# Test health endpoint
curl http://YOUR-ELASTIC-IP/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "webhook_types": 4,
  "timestamp": "2024-08-05T15:38:00Z"
}
```

### Test 2: Webhook Processing

```bash
# Test GitHub webhook
curl -X POST http://YOUR-ELASTIC-IP/webhook/github \
  -H 'Content-Type: application/json' \
  -d '{
    "action": "opened",
    "pull_request": {
      "title": "Deployment Test",
      "user": {"login": "deployer"}
    },
    "repository": {"name": "GenHook-AWS"}
  }'

# Expected response:
{
  "status": "success",
  "message": "Webhook processed and alert sent to SL1",
  "generated_message": "MAJOR: GitHub opened on GenHook-AWS: \"Deployment Test\" by deployer",
  "processing_time_ms": 45.2
}
```

### Test 3: Log Verification

```bash
# Check application logs
tail -f /var/log/genhook/app.log

# Check nginx access logs
sudo tail -f /var/log/nginx/genhook_access.log

# Check service status
sudo supervisorctl status
```

---

## External Webhook Configuration

### GitHub Webhook Setup

1. **Navigate to Repository Settings**:
   - Go to your GitHub repository
   - Click **Settings → Webhooks → Add webhook**

2. **Configure Webhook**:
   - **Payload URL**: `http://YOUR-ELASTIC-IP/webhook/github`
   - **Content type**: `application/json`
   - **Secret**: Leave empty (Phase 3 will add signature verification)
   - **Events**: Select events you want to monitor:
     - Pull requests
     - Issues
     - Push events
     - Releases

3. **Test Webhook**:
   - GitHub will send a test payload
   - Check your GenHook logs for successful processing

### Stripe Webhook Setup

1. **Navigate to Stripe Dashboard**:
   - Go to **Developers → Webhooks → Add endpoint**

2. **Configure Endpoint**:
   - **Endpoint URL**: `http://YOUR-ELASTIC-IP/webhook/stripe`
   - **Events**: Select relevant events:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `customer.subscription.created`

3. **Test Endpoint**:
   - Use Stripe's webhook testing tool
   - Verify events appear in GenHook logs

### Slack Webhook Setup

1. **Create Slack App**:
   - Go to https://api.slack.com/apps
   - Create new app or use existing

2. **Configure Event Subscriptions**:
   - **Request URL**: `http://YOUR-ELASTIC-IP/webhook/slack`
   - **Subscribe to events**:
     - `message.channels`
     - `app_mention`

3. **Verify URL**:
   - Slack will send verification challenge
   - GenHook needs to respond with the challenge value

---

## Monitoring & Maintenance

### System Monitoring Script

Create a comprehensive status check script:

```bash
# Create monitoring script
sudo nano /opt/genhook/check_status.sh
```

Script content:
```bash
#!/bin/bash
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
```

### Log Rotation

Configure log rotation to prevent disk space issues:

```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/genhook
```

Configuration:
```
/var/log/genhook/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        supervisorctl restart genhook
    endscript
}
```

### Automated Monitoring

Set up cron job for regular health checks:

```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * curl -f -s http://localhost/health > /dev/null || echo "GenHook health check failed at $(date)" | mail -s "GenHook Alert" admin@yourcompany.com
```

---

## Security & Backup

### Basic Security Hardening

```bash
# Configure UFW firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS (future SSL)
sudo ufw enable

# Update packages regularly
sudo apt update && sudo apt upgrade -y

# Configure automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### SSH Security (Optional)

```bash
# Edit SSH configuration
sudo nano /etc/ssh/sshd_config

# Recommended changes:
# Port 2222  # Change default port
# PasswordAuthentication no  # Disable password auth
# PermitRootLogin no  # Disable root login
# AllowUsers ubuntu genhook  # Limit users

# Restart SSH service
sudo systemctl restart sshd
```

### Backup Strategy

Create automated backup script:

```bash
# Create backup script
nano /opt/genhook/backup.sh
```

Backup script:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/genhook_backups"
mkdir -p $BACKUP_DIR

# Create comprehensive backup
tar -czf $BACKUP_DIR/genhook_backup_$DATE.tar.gz \
  /opt/genhook/backend/config/ \
  /var/log/genhook/ \
  /etc/nginx/sites-available/genhook \
  /etc/supervisor/conf.d/genhook.conf

# Upload to S3 (optional)
# aws s3 cp $BACKUP_DIR/genhook_backup_$DATE.tar.gz s3://your-backup-bucket/

echo "Backup created: $BACKUP_DIR/genhook_backup_$DATE.tar.gz"

# Cleanup old backups (keep last 7 days)
find $BACKUP_DIR -name "genhook_backup_*.tar.gz" -mtime +7 -delete
```

Schedule daily backups:
```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /opt/genhook/backup.sh
```

---

## Cost Analysis

### AWS Monthly Costs (US East Region)

**Compute:**
- **t3.small EC2 Instance**: $15.33/month
- **20GB EBS Storage**: $2.00/month
- **Elastic IP**: $0.00 (free when attached)

**Data Transfer:**
- **First 100GB outbound**: Free
- **Additional outbound**: $0.09/GB
- **Inbound**: Free

**Estimated Monthly Total**: $17-25/month
- Base: $17.33
- With moderate webhook traffic (50GB): $22.33
- With high webhook traffic (200GB): $26.33

### Cost Optimization Tips

1. **Right-size instance**: Start with t3.small, monitor usage
2. **Reserved Instances**: Save up to 75% with 1-year commitment
3. **CloudWatch monitoring**: Use free tier for basic metrics
4. **EBS optimization**: Use gp3 for better price/performance

---

## Troubleshooting

### Common Issues

**Issue 1: GenHook service won't start**
```bash
# Check supervisor logs
sudo supervisorctl tail genhook stderr

# Check Python path and dependencies
sudo -u genhook bash
cd /opt/genhook/backend
source ../venv/bin/activate
python main.py
```

**Issue 2: Nginx 502 Bad Gateway**
```bash
# Check if GenHook is running on port 8000
sudo netstat -tlnp | grep 8000

# Check nginx error logs
sudo tail -f /var/log/nginx/genhook_error.log

# Restart services in order
sudo supervisorctl restart genhook
sudo systemctl restart nginx
```

**Issue 3: Webhooks not reaching SL1**
```bash
# Check SL1 connectivity
curl -k -u "username:password" https://your-sl1-server.com/api/alert

# Check application logs for SL1 errors
grep "SL1" /var/log/genhook/app.log

# Test with verbose logging
# Edit config to set logging level to DEBUG
```

**Issue 4: High memory usage**
```bash
# Monitor memory usage
free -h
htop

# Check for memory leaks in logs
grep -i "memory\|oom" /var/log/syslog

# Consider upgrading to t3.medium
```

### Performance Monitoring

```bash
# Monitor CPU and memory
htop

# Monitor disk I/O
iotop

# Monitor network connections
netstat -an | grep :80

# Check webhook processing times
grep "processing_time_ms" /var/log/genhook/app.log | tail -20
```

### Log Analysis

```bash
# Count webhook types processed
grep "Received.*webhook" /var/log/genhook/app.log | awk '{print $4}' | sort | uniq -c

# Check error rates
grep -c "ERROR" /var/log/genhook/app.log

# Monitor SL1 success rates
grep -c "Successfully sent alert to SL1" /var/log/genhook/app.log
```

---

## Next Steps

### Immediate Post-Deployment
1. **Monitor logs** for first 24-48 hours
2. **Test all webhook sources** (GitHub, Stripe, etc.)
3. **Verify SL1 alerts** are being received
4. **Set up basic monitoring** alerts

### Phase 2 Enhancements (Future)
1. **Multi-threading**: Handle concurrent webhooks
2. **Queue system**: Redis/RabbitMQ for reliability
3. **Load balancing**: Multiple EC2 instances
4. **Auto-scaling**: Scale based on webhook volume

### Phase 3 Production Features (Future)
1. **Webhook signature verification**: Security hardening
2. **Rate limiting**: Protect against abuse
3. **Comprehensive monitoring**: Detailed metrics and alerting
4. **SSL certificate**: Let's Encrypt or AWS Certificate Manager

### Infrastructure Improvements
1. **Application Load Balancer**: For high availability
2. **RDS database**: Store webhook history and metrics
3. **CloudWatch**: Advanced monitoring and alerting
4. **Auto Scaling Groups**: Automatic capacity management

---

## Support Information

### Documentation
- **GenHook Repository**: https://github.com/YOUR-USERNAME/GenHook
- **AWS EC2 Documentation**: https://docs.aws.amazon.com/ec2/
- **FastAPI Documentation**: https://fastapi.tiangolo.com/

### Getting Help
- **Application Logs**: `/var/log/genhook/app.log`
- **System Logs**: `/var/log/syslog`
- **Nginx Logs**: `/var/log/nginx/genhook_*.log`

### Emergency Procedures
1. **Service restart**: `sudo supervisorctl restart genhook`
2. **Full system restart**: `sudo reboot`
3. **Rollback**: Restore from backup and restart services
4. **Scale up**: Change instance type in AWS console

---

**Document Version**: 1.0  
**Last Updated**: August 5, 2024  
**Contact**: admin@yourcompany.com

---

*This guide provides a complete deployment strategy for GenHook MVP. For production environments processing high volumes of webhooks, consider implementing Phase 2 and Phase 3 enhancements.*