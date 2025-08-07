# GenHook AWS Deployment Guide

## Overview

This guide provides detailed instructions for deploying GenHook on AWS with high availability, security, and scalability. The architecture uses Application Load Balancer, Auto Scaling, and CloudWatch for a production-ready deployment.

## Architecture Diagram

```
Internet
    ↓
Application Load Balancer (ALB)
    ↓
Target Group (Health Checks)
    ↓
Auto Scaling Group
    ↓
EC2 Instances (GenHook)
    ↓
SL1 API (External)
```

## AWS Services Used

- **EC2**: Application hosting
- **Application Load Balancer**: Traffic distribution and SSL termination
- **Auto Scaling Group**: Automatic scaling based on load
- **CloudWatch**: Monitoring and alerting
- **Secrets Manager**: Secure credential storage
- **Certificate Manager**: SSL certificate management
- **Route 53**: DNS management (optional)
- **S3**: Configuration backups (optional)

## Step-by-Step Deployment

### 1. VPC and Security Setup

#### Create Security Groups

```bash
# GenHook Application Security Group
aws ec2 create-security-group \
    --group-name genhook-app-sg \
    --description "Security group for GenHook application" \
    --vpc-id vpc-xxxxxxxxx

# Allow HTTP from ALB
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 8000 \
    --source-group sg-alb-xxxxxxxx

# Allow SSH for management
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 22 \
    --cidr 10.0.0.0/8

# Allow HTTPS outbound to SL1
aws ec2 authorize-security-group-egress \
    --group-id sg-xxxxxxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# ALB Security Group
aws ec2 create-security-group \
    --group-name genhook-alb-sg \
    --description "Security group for GenHook ALB" \
    --vpc-id vpc-xxxxxxxxx

# Allow HTTPS from Internet
aws ec2 authorize-security-group-ingress \
    --group-id sg-alb-xxxxxxxx \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow HTTP (for redirect)
aws ec2 authorize-security-group-ingress \
    --group-id sg-alb-xxxxxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0
```

### 2. SSL Certificate Setup

```bash
# Request certificate via AWS Certificate Manager
aws acm request-certificate \
    --domain-name genhook.yourdomain.com \
    --domain-name "*.yourdomain.com" \
    --validation-method DNS \
    --subject-alternative-names genhook-api.yourdomain.com

# Note the ARN for ALB configuration
```

### 3. Secrets Manager Setup

```bash
# Store SL1 credentials in Secrets Manager
aws secretsmanager create-secret \
    --name genhook/sl1-credentials \
    --description "SL1 API credentials for GenHook" \
    --secret-string '{
        "api_url": "https://your-sl1-instance.com/api/alert",
        "username": "your_sl1_username",
        "password": "your_sl1_password"
    }'
```

### 4. Launch Template Creation

Create a launch template for GenHook instances:

```bash
# Create launch template
aws ec2 create-launch-template \
    --launch-template-name genhook-template \
    --launch-template-data '{
        "ImageId": "ami-0c02fb55956c7d316",
        "InstanceType": "t3.medium",
        "KeyName": "your-key-pair",
        "SecurityGroupIds": ["sg-xxxxxxxxx"],
        "IamInstanceProfile": {
            "Name": "GenHookInstanceProfile"
        },
        "UserData": "'$(base64 -w 0 user-data.sh)'"
    }'
```

#### User Data Script (`user-data.sh`)

```bash
#!/bin/bash
yum update -y
yum install -y python3 python3-pip git amazon-cloudwatch-agent

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Create genhook user
useradd -m -s /bin/bash genhook

# Setup GenHook
mkdir -p /opt/genhook
chown genhook:genhook /opt/genhook
cd /opt/genhook

# Clone repository
sudo -u genhook git clone https://github.com/rudipoppes/GenHook.git .

# Setup Python environment
sudo -u genhook python3 -m venv venv
sudo -u genhook ./venv/bin/pip install -r backend/requirements.txt

# Get secrets from AWS Secrets Manager
SECRET=$(aws secretsmanager get-secret-value \
    --secret-id genhook/sl1-credentials \
    --region us-east-1 \
    --query SecretString --output text)

SL1_API_URL=$(echo $SECRET | jq -r .api_url)
SL1_USERNAME=$(echo $SECRET | jq -r .username)
SL1_PASSWORD=$(echo $SECRET | jq -r .password)

# Create production configuration
cat > backend/config/app-config.ini <<EOF
[server]
host = 0.0.0.0
port = 8000
log_level = INFO

[sl1]
api_url = $SL1_API_URL
username = $SL1_USERNAME
password = $SL1_PASSWORD
timeout = 30
retry_attempts = 3
EOF

cat > backend/config/web-config.ini <<EOF
[ui]
enabled = true
max_analysis_depth = 3
timeout_seconds = 30

[features]
auto_restart_service = true
backup_configs = true

[paths]
config_file_path = config/webhook-config.ini
backup_directory = config/backups
EOF

# Create systemd service
cat > /etc/systemd/system/genhook.service <<EOF
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

[Install]
WantedBy=multi-user.target
EOF

# Setup CloudWatch agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<EOF
{
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/opt/genhook/logs/application.log",
                        "log_group_name": "genhook",
                        "log_stream_name": "application"
                    }
                ]
            }
        }
    },
    "metrics": {
        "namespace": "GenHook/Application",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    }
}
EOF

# Start services
systemctl daemon-reload
systemctl enable genhook
systemctl start genhook
systemctl enable amazon-cloudwatch-agent
systemctl start amazon-cloudwatch-agent
```

### 5. IAM Roles and Policies

#### Create IAM Role for EC2 Instances

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:*:*:secret:genhook/sl1-credentials*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "logs:PutLogEvents",
                "logs:CreateLogGroup",
                "logs:CreateLogStream"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::your-genhook-backups/*"
        }
    ]
}
```

### 6. Application Load Balancer Setup

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name genhook-alb \
    --subnets subnet-xxxxxx subnet-yyyyyy \
    --security-groups sg-alb-xxxxxxxx \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4

# Create Target Group
aws elbv2 create-target-group \
    --name genhook-tg \
    --protocol HTTP \
    --port 8000 \
    --vpc-id vpc-xxxxxxxxx \
    --health-check-path /health \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3

# Create HTTPS Listener
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:region:account:loadbalancer/app/genhook-alb/xxxxxxxxx \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=arn:aws:acm:region:account:certificate/xxxxxxxxx \
    --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:region:account:targetgroup/genhook-tg/xxxxxxxxx

# Create HTTP Listener (redirect to HTTPS)
aws elbv2 create-listener \
    --load-balancer-arn arn:aws:elasticloadbalancing:region:account:loadbalancer/app/genhook-alb/xxxxxxxxx \
    --protocol HTTP \
    --port 80 \
    --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'
```

### 7. Auto Scaling Group

```bash
# Create Auto Scaling Group
aws autoscaling create-auto-scaling-group \
    --auto-scaling-group-name genhook-asg \
    --launch-template LaunchTemplateName=genhook-template,Version=1 \
    --min-size 2 \
    --max-size 6 \
    --desired-capacity 2 \
    --target-group-arns arn:aws:elasticloadbalancing:region:account:targetgroup/genhook-tg/xxxxxxxxx \
    --health-check-type ELB \
    --health-check-grace-period 300 \
    --vpc-zone-identifier "subnet-xxxxxx,subnet-yyyyyy"

# Create scaling policies
aws autoscaling put-scaling-policy \
    --auto-scaling-group-name genhook-asg \
    --policy-name genhook-scale-up \
    --policy-type TargetTrackingScaling \
    --target-tracking-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ASGAverageCPUUtilization"
        },
        "ScaleOutCooldown": 300,
        "ScaleInCooldown": 300
    }'
```

### 8. CloudWatch Monitoring

#### Custom Metrics

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
    --dashboard-name GenHook \
    --dashboard-body '{
        "widgets": [
            {
                "type": "metric",
                "properties": {
                    "metrics": [
                        ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/genhook-alb/xxxxxxxxx"],
                        ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/genhook-alb/xxxxxxxxx"],
                        ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", "app/genhook-alb/xxxxxxxxx"]
                    ],
                    "period": 300,
                    "stat": "Sum",
                    "region": "us-east-1",
                    "title": "ALB Metrics"
                }
            }
        ]
    }'
```

#### Alarms

```bash
# High error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "GenHook-High-Error-Rate" \
    --alarm-description "GenHook 5XX error rate is too high" \
    --metric-name HTTPCode_ELB_5XX_Count \
    --namespace AWS/ApplicationELB \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:account:genhook-alerts

# High response time alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "GenHook-High-Response-Time" \
    --alarm-description "GenHook response time is too high" \
    --metric-name TargetResponseTime \
    --namespace AWS/ApplicationELB \
    --statistic Average \
    --period 300 \
    --threshold 2.0 \
    --comparison-operator GreaterThanThreshold \
    --evaluation-periods 2 \
    --alarm-actions arn:aws:sns:us-east-1:account:genhook-alerts
```

### 9. Route 53 DNS Setup

```bash
# Create hosted zone (if not exists)
aws route53 create-hosted-zone \
    --name yourdomain.com \
    --caller-reference $(date +%s)

# Create A record pointing to ALB
aws route53 change-resource-record-sets \
    --hosted-zone-id Z1234567890ABC \
    --change-batch '{
        "Changes": [{
            "Action": "CREATE",
            "ResourceRecordSet": {
                "Name": "genhook.yourdomain.com",
                "Type": "A",
                "AliasTarget": {
                    "DNSName": "genhook-alb-xxxxxxxxx.us-east-1.elb.amazonaws.com",
                    "EvaluateTargetHealth": true,
                    "HostedZoneId": "Z35SXDOTRQ7X7K"
                }
            }
        }]
    }'
```

### 10. Configuration Backup to S3

Add this to your GenHook application for automatic backups:

```python
import boto3
import json
from datetime import datetime

class S3ConfigBackup:
    def __init__(self, bucket_name):
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
    
    def backup_config(self, config_data):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        key = f"genhook/configs/backup_{timestamp}.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json.dumps(config_data, indent=2),
                ContentType='application/json'
            )
            return key
        except Exception as e:
            logger.error(f"Failed to backup config to S3: {e}")
            return None
```

## Web Interface Access Control

### ALB Listener Rules for Web Interface

```bash
# Create rule to restrict /config access
aws elbv2 create-rule \
    --listener-arn arn:aws:elasticloadbalancing:region:account:listener/app/genhook-alb/xxxxxxxxx/xxxxxxxxx \
    --conditions Field=path-pattern,Values='/config*' \
    --priority 100 \
    --actions Type=fixed-response,FixedResponseConfig='{StatusCode=403,ContentType=text/plain,MessageBody="Access Denied"}'

# Create rule for specific IP ranges
aws elbv2 create-rule \
    --listener-arn arn:aws:elasticloadbalancing:region:account:listener/app/genhook-alb/xxxxxxxxx/xxxxxxxxx \
    --conditions Field=path-pattern,Values='/config*' Field=source-ip,Values='203.0.113.0/24,198.51.100.0/24' \
    --priority 50 \
    --actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:region:account:targetgroup/genhook-tg/xxxxxxxxx
```

## Cost Optimization

### Instance Rightsizing

- **t3.micro**: Development/testing (1 vCPU, 1GB RAM) - ~$8.50/month
- **t3.small**: Light production (2 vCPU, 2GB RAM) - ~$17/month  
- **t3.medium**: Moderate load (2 vCPU, 4GB RAM) - ~$34/month
- **c5.large**: High performance (2 vCPU, 4GB RAM) - ~$62/month

### Reserved Instances

Consider Reserved Instances for 30-60% cost savings on long-term deployments.

## Disaster Recovery

### Multi-AZ Deployment

```bash
# Deploy across multiple AZs
aws autoscaling update-auto-scaling-group \
    --auto-scaling-group-name genhook-asg \
    --vpc-zone-identifier "subnet-xxxxxx,subnet-yyyyyy,subnet-zzzzzz"
```

### Cross-Region Backup

```python
# Cross-region S3 backup
s3_client_dr = boto3.client('s3', region_name='us-west-2')
s3_client_dr.copy_object(
    CopySource={'Bucket': 'genhook-backups', 'Key': config_key},
    Bucket='genhook-backups-dr',
    Key=config_key
)
```

This AWS deployment guide provides a robust, scalable, and secure foundation for running GenHook in production on AWS infrastructure.