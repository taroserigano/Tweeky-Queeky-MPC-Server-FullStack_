#!/bin/bash
# Deploy code to running EC2 instance

if [ -z "$1" ]; then
    echo "Usage: ./deploy/deploy-to-ec2.sh <EC2_PUBLIC_IP>"
    echo "Example: ./deploy/deploy-to-ec2.sh 3.145.123.45"
    exit 1
fi

EC2_IP=$1
KEY_FILE="tweeky-ec2-key.pem"

if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found: $KEY_FILE"
    echo "Make sure you're in the project root directory"
    exit 1
fi

echo "=== Deploying TweekySqueeky to EC2: $EC2_IP ==="
echo ""

# Create deployment tarball (excluding large files)
echo "📦 Creating deployment package..."
tar --exclude='node_modules' \
    --exclude='frontend/node_modules' \
    --exclude='frontend/build' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='uploads' \
    --exclude='deploy/*.pem' \
    -czf /tmp/tweeky-deploy.tar.gz \
    .

echo "✅ Package created"
echo ""

# Copy to EC2
echo "📤 Uploading to EC2..."
scp -i $KEY_FILE \
    -o StrictHostKeyChecking=no \
    /tmp/tweeky-deploy.tar.gz \
    ubuntu@${EC2_IP}:/tmp/

echo "✅ Upload complete"
echo ""

# Deploy on EC2
echo "🚀 Deploying on EC2..."
ssh -i $KEY_FILE \
    -o StrictHostKeyChecking=no \
    ubuntu@${EC2_IP} << 'ENDSSH'

# Extract code
cd /opt/tweeky-app
sudo tar -xzf /tmp/tweeky-deploy.tar.gz
rm /tmp/tweeky-deploy.tar.gz

# Update .env with your actual credentials
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

ENDSSH

# Get the public IP for display
echo ""
echo "=========================================="
echo "🎉 Deployment Complete!"
echo "=========================================="
echo ""
echo "Your app is running at:"
echo "  http://${EC2_IP}:3000"
echo ""
echo "To check status:"
echo "  ssh -i ${KEY_FILE} ubuntu@${EC2_IP}"
echo "  cd /opt/tweeky-app"
echo "  sudo docker compose ps"
echo ""
echo "⚠️  IMPORTANT: Update API keys in .env!"
echo "  ssh -i ${KEY_FILE} ubuntu@${EC2_IP}"
echo "  sudo nano /opt/tweeky-app/.env"
echo "  sudo docker compose restart fastapi-backend"
echo ""
echo "=========================================="

# Cleanup
rm /tmp/tweeky-deploy.tar.gz
