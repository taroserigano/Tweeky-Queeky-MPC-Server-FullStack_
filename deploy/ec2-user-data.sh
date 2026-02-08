#!/bin/bash
# EC2 User Data Script - Auto-setup Docker + Deploy App
# This runs on first boot only

set -e

echo "=== Starting TweekySqueeky E-Commerce Setup ==="

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
systemctl enable docker
systemctl start docker

# Create app directory
mkdir -p /opt/tweeky-app
cd /opt/tweeky-app

# Create .env file (REPLACE WITH YOUR VALUES)
cat > .env << 'EOF'
MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/tweeky?authSource=admin
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
ANTHROPIC_CHAT_MODEL=claude-3-5-sonnet-latest
PINECONE_API_KEY=
PINECONE_ENVIRONMENT=
PINECONE_INDEX=
PAYPAL_CLIENT_ID=
PAYPAL_APP_SECRET=
PAYPAL_API_URL=https://api-m.sandbox.paypal.com
PAGINATION_LIMIT=12
EOF

echo "=== User data script complete. Deploy manually with deploy-ec2.sh ==="
