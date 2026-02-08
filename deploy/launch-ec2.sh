#!/bin/bash
# Deploy TweekySqueeky E-Commerce to AWS EC2
# Uses t4g.nano (ARM, $3.07/month) for cheapest option

set -e

# Configuration
INSTANCE_TYPE="t4g.nano"  # ARM-based, cheapest option
AMI_ID="ami-0ea3c35c5c3284d82"  # Ubuntu 24.04 LTS ARM64 (us-east-2)
KEY_NAME="tweeky-ec2-key"
SECURITY_GROUP_NAME="tweeky-sg"
REGION="us-east-2"

echo "=== Deploying TweekySqueeky to AWS EC2 ==="
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $REGION"
echo ""

# Check if key pair exists
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION &>/dev/null; then
    echo "Creating new key pair..."
    aws ec2 create-key-pair \
        --key-name $KEY_NAME \
        --region $REGION \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    echo "✅ Key pair created: ${KEY_NAME}.pem (SAVE THIS FILE!)"
else
    echo "✅ Key pair already exists: ${KEY_NAME}"
fi

# Create security group
echo ""
echo "Setting up security group..."
SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=${SECURITY_GROUP_NAME}" \
    --region $REGION \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null)

if [ "$SG_ID" == "None" ] || [ -z "$SG_ID" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP_NAME \
        --description "Security group for TweekySqueeky E-Commerce" \
        --region $REGION \
        --query 'GroupId' \
        --output text)
    
    # Allow SSH
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    # Allow HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    # Allow HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    # Allow frontend port 3000
    aws ec2 authorize-security-group-ingress \
        --group-id $SG_ID \
        --protocol tcp \
        --port 3000 \
        --cidr 0.0.0.0/0 \
        --region $REGION
    
    echo "✅ Security group created: $SG_ID"
else
    echo "✅ Using existing security group: $SG_ID"
fi

# Launch EC2 instance
echo ""
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --region $REGION \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=TweekySqueeky-App}]" \
    --user-data file://deploy/ec2-user-data.sh \
    --block-device-mappings "[{\"DeviceName\":\"/dev/sda1\",\"Ebs\":{\"VolumeSize\":10,\"VolumeType\":\"gp3\",\"DeleteOnTermination\":true}}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo ""
echo "Waiting for instance to start..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "=========================================="
echo "🎉 EC2 Instance is RUNNING!"
echo "=========================================="
echo ""
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo ""
echo "⏳ The instance is installing Docker (takes 2-3 minutes)"
echo ""
echo "Next steps:"
echo "1. Wait 3 minutes for Docker installation"
echo "2. SSH into the server:"
echo "   ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "3. Deploy your app:"
echo "   cd /opt/tweeky-app"
echo "   # Upload your code or clone from git"
echo "   docker compose up -d"
echo ""
echo "4. Access your app:"
echo "   http://${PUBLIC_IP}:3000"
echo ""
echo "To SSH now (wait 2-3 min first):"
echo "ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "Monthly cost: ~$3.07"
echo "=========================================="
