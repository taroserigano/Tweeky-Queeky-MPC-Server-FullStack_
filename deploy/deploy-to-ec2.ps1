# Deploy code to running EC2 instance (PowerShell)

param(
    [Parameter(Mandatory=$true)]
    [string]$EC2_IP
)

$ErrorActionPreference = "Stop"

$KEY_FILE = "tweeky-ec2-key.pem"

if (-not (Test-Path $KEY_FILE)) {
    Write-Host "❌ Key file not found: $KEY_FILE" -ForegroundColor Red
    Write-Host "Make sure you're in the project root directory"
    exit 1
}

Write-Host "`n=== Deploying TweekySqueeky to EC2: $EC2_IP ===" -ForegroundColor Cyan

# Create deployment tarball (excluding large files)
Write-Host "`n📦 Creating deployment package..." -ForegroundColor Yellow

# Use WSL tar if available, otherwise use 7-Zip or built-in PowerShell
if (Get-Command wsl -ErrorAction SilentlyContinue) {
    wsl tar --exclude='node_modules' `
        --exclude='frontend/node_modules' `
        --exclude='frontend/build' `
        --exclude='__pycache__' `
        --exclude='*.pyc' `
        --exclude='.git' `
        --exclude='uploads' `
        --exclude='deploy/*.pem' `
        -czf /tmp/tweeky-deploy.tar.gz .
    
    Write-Host "✅ Package created" -ForegroundColor Green
    
    # Copy to EC2
    Write-Host "`n📤 Uploading to EC2..." -ForegroundColor Yellow
    
    # Use SCP via WSL
    wsl scp -i $KEY_FILE `
        -o StrictHostKeyChecking=no `
        /tmp/tweeky-deploy.tar.gz `
        ubuntu@${EC2_IP}:/tmp/
    
    Write-Host "✅ Upload complete" -ForegroundColor Green
} else {
    Write-Host "⚠️  WSL not found. Using alternative method..." -ForegroundColor Yellow
    Write-Host "Please install Git Bash or WSL for automated deployment." -ForegroundColor Yellow
    Write-Host "`nManual deployment steps:" -ForegroundColor Cyan
    Write-Host "1. Install Git Bash or WSL"
    Write-Host "2. Run: bash deploy/deploy-to-ec2.sh $EC2_IP"
    Write-Host "`nOr use an SFTP client like WinSCP to upload files manually."
    exit 1
}

# Deploy on EC2
Write-Host "`n🚀 Deploying on EC2..." -ForegroundColor Yellow

$deployScript = @'
# Extract code
cd /opt/tweeky-app
sudo tar -xzf /tmp/tweeky-deploy.tar.gz
rm /tmp/tweeky-deploy.tar.gz

echo ""
echo "⚙️  IMPORTANT: Update /opt/tweeky-app/.env with your real API keys!"
echo "Edit with: sudo nano /opt/tweeky-app/.env"
echo ""

# Build and start containers
echo "🐳 Building and starting Docker containers..."
sudo docker compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Seed database
echo "🌱 Seeding database..."
sudo docker compose exec -T fastapi-backend python scripts/seeder.py

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check status:"
echo "  sudo docker compose ps"
echo ""
echo "View logs:"
echo "  sudo docker compose logs -f"
echo ""
'@

wsl ssh -i $KEY_FILE -o StrictHostKeyChecking=no ubuntu@${EC2_IP} $deployScript

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "🎉 Deployment Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "`nYour app is running at:"
Write-Host "  http://${EC2_IP}:3000" -ForegroundColor Cyan
Write-Host "`n⚠️  IMPORTANT: Update API keys in .env!" -ForegroundColor Yellow
Write-Host "`nTo SSH into server:" -ForegroundColor Cyan
Write-Host "  wsl ssh -i ${KEY_FILE} ubuntu@${EC2_IP}"
Write-Host "`nThen edit .env:"
Write-Host "  cd /opt/tweeky-app"
Write-Host "  sudo nano .env"
Write-Host "  sudo docker compose restart fastapi-backend"
Write-Host "`n==========================================`n"
