#!/bin/bash

# Update AWS Security Group for HTTPS
# Adds port 443 (HTTPS) to the existing genhook-security-group

echo "🔒 Adding HTTPS (port 443) to AWS Security Group..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first:"
    echo "   curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'"
    echo "   unzip awscliv2.zip"
    echo "   sudo ./aws/install"
    exit 1
fi

# Check if AWS is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS not configured. Please run: aws configure"
    exit 1
fi

# Find the security group
SECURITY_GROUP_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=genhook-security-group" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

if [ "$SECURITY_GROUP_ID" = "None" ] || [ -z "$SECURITY_GROUP_ID" ]; then
    echo "❌ Security group 'genhook-security-group' not found"
    echo "   Available security groups:"
    aws ec2 describe-security-groups --query 'SecurityGroups[*].[GroupName,GroupId]' --output table
    exit 1
fi

echo "✅ Found security group: $SECURITY_GROUP_ID"

# Check if HTTPS rule already exists
EXISTING_RULE=$(aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --query 'SecurityGroups[0].IpPermissions[?FromPort==`443`]' \
    --output text)

if [ -n "$EXISTING_RULE" ]; then
    echo "✅ HTTPS rule already exists in security group"
else
    echo "➕ Adding HTTPS rule to security group..."
    
    aws ec2 authorize-security-group-ingress \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --tag-specifications 'ResourceType=security-group-rule,Tags=[{Key=Name,Value=GenHook-HTTPS},{Key=Description,Value=HTTPS access for Meraki webhooks}]'
    
    if [ $? -eq 0 ]; then
        echo "✅ HTTPS rule added successfully"
    else
        echo "❌ Failed to add HTTPS rule"
        exit 1
    fi
fi

echo ""
echo "🎉 Security group updated for HTTPS traffic"
echo "📋 Current rules for $SECURITY_GROUP_ID:"
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --query 'SecurityGroups[0].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' \
    --output table