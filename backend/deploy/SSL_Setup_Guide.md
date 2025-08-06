# GenHook HTTPS/SSL Setup Guide

This guide shows how to add HTTPS support to your GenHook deployment for services like Meraki that require secure webhook endpoints.

## Prerequisites

1. **Domain Name**: You need a domain pointing to your server's IP address
2. **DNS Configuration**: Domain must resolve to your EC2 instance's public IP
3. **AWS Security Group**: Port 443 must be open for HTTPS traffic

## Quick Setup

### Step 1: Get a Domain Name

If you don't have a domain, you can use free services:

- **Duck DNS** (duckdns.org): Free subdomain like `yourname.duckdns.org`
- **No-IP** (noip.com): Free dynamic DNS
- **Freenom** (freenom.com): Free domain names

Point your domain to your EC2 instance's **Elastic IP address**.

### Step 2: Run SSL Setup Script

```bash
# Connect to your EC2 instance
ssh -i /path/to/your-key.pem ubuntu@YOUR-ELASTIC-IP

# Switch to GenHook directory
cd /opt/genhook/backend/deploy

# Make scripts executable
sudo chmod +x setup_ssl.sh update_security_group.sh test_https.sh

# Run SSL setup (replace with your domain)
sudo ./setup_ssl.sh your-domain.com
```

**Example:**
```bash
sudo ./setup_ssl.sh webhooks.mydomain.com
```

### Step 3: Update AWS Security Group

```bash
# Update security group to allow HTTPS traffic
./update_security_group.sh
```

### Step 4: Test HTTPS Setup

```bash
# Test all HTTPS functionality
./test_https.sh your-domain.com
```

## What the SSL Setup Does

1. **Installs Certbot** for Let's Encrypt certificates
2. **Generates SSL certificate** for your domain
3. **Updates nginx configuration** with HTTPS and security headers
4. **Sets up automatic renewal** (certificates renew every 90 days)
5. **Configures HTTP to HTTPS redirect**

## Expected Output

After successful setup, you'll see:

```
✅ SSL setup successful!

🎉 HTTPS is now configured for your GenHook server!
📍 Your webhook endpoints:
   - Health check: https://your-domain.com/health
   - GitHub: https://your-domain.com/webhook/github
   - Meraki: https://your-domain.com/webhook/meraki
   - Stripe: https://your-domain.com/webhook/stripe
   - Slack: https://your-domain.com/webhook/slack
```

## Configure Meraki Webhooks

1. **Log into Meraki Dashboard**
2. **Go to Organization > Alerts**
3. **Click Webhooks > Add webhook**
4. **Configure:**
   - **Name**: GenHook Alerts
   - **URL**: `https://your-domain.com/webhook/meraki`
   - **Shared Secret**: Leave empty for now
   - **Alert Types**: Select desired alert types

## Testing Meraki Integration

Test with curl:

```bash
curl -X POST https://your-domain.com/webhook/meraki \
  -H "Content-Type: application/json" \
  -d '{
    "alertType": "Device down",
    "deviceName": "Test-Switch-01", 
    "deviceSerial": "Q2XX-XXXX-XXXX",
    "networkName": "Test Network"
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Webhook processed and alert sent to SL1",
  "generated_message": "MAJOR: Meraki Device down on device Test-Switch-01 (Serial: Q2XX-XXXX-XXXX) in network Test Network"
}
```

## Security Features

The SSL setup includes:

- **TLS 1.2/1.3** encryption
- **HSTS headers** for browser security
- **Security headers** (X-Frame-Options, X-XSS-Protection, etc.)
- **Rate limiting** (100 requests/minute)
- **Automatic certificate renewal**

## Troubleshooting

### SSL Certificate Issues

```bash
# Check certificate status
sudo certbot certificates

# Manual renewal test
sudo certbot renew --dry-run

# Check nginx configuration
sudo nginx -t
```

### Domain Not Resolving

```bash
# Test DNS resolution
nslookup your-domain.com
dig your-domain.com

# Check if domain points to correct IP
```

### Port 443 Blocked

```bash
# Test if port 443 is accessible
telnet your-domain.com 443

# Check AWS Security Group rules
aws ec2 describe-security-groups --group-names genhook-security-group
```

### Certificate Renewal Issues

Let's Encrypt certificates expire every 90 days. Automatic renewal is configured, but if it fails:

```bash
# Manual certificate renewal
sudo certbot renew --nginx

# Check renewal log
sudo tail /var/log/letsencrypt/letsencrypt.log
```

## File Locations

- **SSL Certificates**: `/etc/letsencrypt/live/your-domain.com/`
- **Nginx Config**: `/etc/nginx/sites-available/genhook`
- **SSL Logs**: `/var/log/nginx/genhook_ssl_*.log`
- **Let's Encrypt Logs**: `/var/log/letsencrypt/`

## Next Steps

After HTTPS is working:

1. **Update all webhook sources** to use HTTPS URLs
2. **Test with real webhook traffic**
3. **Monitor SSL certificate expiration** (auto-renewal should handle this)
4. **Consider adding webhook signature verification** for additional security

## Cost Impact

- **Let's Encrypt certificates**: Free
- **No additional AWS costs** for HTTPS traffic
- **Same EC2 and bandwidth costs** as HTTP setup

---

**Need Help?** Check the main deployment guide or GenHook repository for additional troubleshooting steps.