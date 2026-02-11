# Deploy TweekySqueeky E-Commerce to AWS EC2 (PowerShell)
# Uses t4g.nano (ARM, $3.07/month) for cheapest option

$ErrorActionPreference = "Stop"

# Configuration
$INSTANCE_TYPE = "t4g.nano"  # ARM-based, cheapest option
$AMI_ID = "ami-0ea3c35c5c3284d82"  # Ubuntu 24.04 LTS ARM64 (us-east-2)
$KEY_NAME = "tweeky-ec2-key"
$SECURITY_GROUP_NAME = "tweeky-sg"
$REGION = "us-east-2"

Write-Host "`n=== Deploying TweekySqueeky to AWS EC2 ===" -ForegroundColor Cyan
Write-Host "Instance Type: $INSTANCE_TYPE"
Write-Host "Region: $REGION`n"

# Check if key pair exists
$keyExists = $false
try {
    aws ec2 describe-key-pairs --key-names $KEY_NAME --region $REGION 2>$null | Out-Null
    $keyExists = $true
    Write-Host "✅ Key pair already exists: $KEY_NAME" -ForegroundColor Green
} catch {
    Write-Host "Creating new key pair..." -ForegroundColor Yellow
    aws ec2 create-key-pair `
        --key-name $KEY_NAME `
        --region $REGION `
        --query 'KeyMaterial' `
        --output text | Out-File -FilePath "${KEY_NAME}.pem" -Encoding ASCII
    Write-Host "✅ Key pair created: ${KEY_NAME}.pem (SAVE THIS FILE!)" -ForegroundColor Green
}

# Create security group
Write-Host "`nSetting up security group..." -ForegroundColor Yellow
$SG_ID = aws ec2 describe-security-groups `
    --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" `
    --region $REGION `
    --query 'SecurityGroups[0].GroupId' `
    --output text 2>$null

if ([string]::IsNullOrEmpty($SG_ID) -or $SG_ID -eq "None") {
    Write-Host "Creating security group..." -ForegroundColor Yellow
    $SG_ID = aws ec2 create-security-group `
        --group-name $SECURITY_GROUP_NAME `
        --description "Security group for TweekySqueeky E-Commerce" `
        --region $REGION `
        --query 'GroupId' `
        --output text
    
    # Allow SSH
    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 22 `
        --cidr 0.0.0.0/0 `
        --region $REGION
    
    # Allow HTTP
    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 80 `
        --cidr 0.0.0.0/0 `
        --region $REGION
    
    # Allow HTTPS
    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 443 `
        --cidr 0.0.0.0/0 `
        --region $REGION
    
    # Allow frontend port 3000
    aws ec2 authorize-security-group-ingress `
        --group-id $SG_ID `
        --protocol tcp `
        --port 3000 `
        --cidr 0.0.0.0/0 `
        --region $REGION
    
    Write-Host "✅ Security group created: $SG_ID" -ForegroundColor Green
} else {
    Write-Host "✅ Using existing security group: $SG_ID" -ForegroundColor Green
}

# Launch EC2 instance
Write-Host "`nLaunching EC2 instance..." -ForegroundColor Yellow

# Read user-data file
$USER_DATA = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content -Path "ec2-user-data.sh" -Raw)))

$INSTANCE_ID = aws ec2 run-instances `
    --image-id $AMI_ID `
    --instance-type $INSTANCE_TYPE `
    --key-name $KEY_NAME `
    --security-group-ids $SG_ID `
    --region $REGION `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=TweekySqueeky-App}]" `
    --user-data $USER_DATA `
    --block-device-mappings "[{`"DeviceName`":`"/dev/sda1`",`"Ebs`":{`"VolumeSize`":10,`"VolumeType`":`"gp3`",`"DeleteOnTermination`":true}}]" `
    --query 'Instances[0].InstanceId' `
    --output text

Write-Host "✅ Instance launched: $INSTANCE_ID" -ForegroundColor Green
Write-Host "`nWaiting for instance to start..." -ForegroundColor Yellow
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION

# Get public IP
$PUBLIC_IP = aws ec2 describe-instances `
    --instance-ids $INSTANCE_ID `
    --region $REGION `
    --query 'Reservations[0].Instances[0].PublicIpAddress' `
    --output text

Write-Host "`n=========================================="  -ForegroundColor Green
Write-Host "🎉 EC2 Instance is RUNNING!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "`nInstance ID: $INSTANCE_ID"
Write-Host "Public IP: $PUBLIC_IP"
Write-Host "`n⏳ The instance is installing Docker (takes 2-3 minutes)" -ForegroundColor Yellow
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Wait 3 minutes for Docker installation"
Write-Host "2. Deploy your app:"
Write-Host "   .\deploy\deploy-to-ec2.ps1 $PUBLIC_IP" -ForegroundColor Yellow
Write-Host "`n3. Access your app:"
Write-Host "   http://${PUBLIC_IP}:3000" -ForegroundColor Green
Write-Host "`nMonthly cost: ~`$3.07" -ForegroundColor Green
Write-Host "==========================================`n"

# Save instance info
@"
INSTANCE_ID=$INSTANCE_ID
PUBLIC_IP=$PUBLIC_IP
KEY_NAME=$KEY_NAME
REGION=$REGION
"@ | Out-File -FilePath "deploy\ec2-instance.txt" -Encoding ASCII

Write-Host "✅ Instance info saved to deploy\ec2-instance.txt" -ForegroundColor Green
