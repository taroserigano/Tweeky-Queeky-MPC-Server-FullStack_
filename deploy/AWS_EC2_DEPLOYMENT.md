# AWS EC2 Deployment Guide
## TweekySqueeky E-Commerce App

Deploy your full-stack e-commerce app to AWS EC2 for **$3.07/month** using Docker Compose.

---

## 🚀 Quick Deploy (5 Minutes)

### Prerequisites
- AWS CLI installed and configured (`aws configure`)
- This project directory

### Step 1: Launch EC2 Instance

```bash
cd deploy
bash launch-ec2.sh
```

This will:
- Create a t4g.nano ARM instance ($3.07/month)
- Set up security groups (ports 22, 80, 443, 3000)
- Create SSH key pair (saved as `tweeky-ec2-key.pem`)
- Install Docker automatically
- Return your EC2 public IP

**Output:**
```
Instance ID: i-0123456789abcdef
Public IP: 3.145.123.45

Wait 3 minutes for Docker installation...
```

### Step 2: Deploy Your Code (After 3 Minutes)

```bash
bash deploy-to-ec2.sh <YOUR_EC2_PUBLIC_IP>
```

Example:
```bash
bash deploy-to-ec2.sh 3.145.123.45
```

This will:
- Package your code (excluding node_modules)
- Upload to EC2
- Build Docker images
- Start all containers
- Seed database with products

### Step 3: Access Your App

```
http://<YOUR_EC2_IP>:3000
```

That's it! Your app is live! 🎉

---

## ⚙️ Configuration

### Update API Keys (IMPORTANT!)

SSH into your server:
```bash
ssh -i tweeky-ec2-key.pem ubuntu@<YOUR_EC2_IP>
```

Edit environment variables:
```bash
cd /opt/tweeky-app
sudo nano .env
```

Update these keys:
```bash
OPENAI_API_KEY=sk-your-real-key-here
ANTHROPIC_API_KEY=sk-ant-your-real-key-here
JWT_SECRET=your-super-secret-jwt-key
```

Save and restart:
```bash
sudo docker compose restart fastapi-backend
```

---

## 🔧 Management Commands

### SSH into Server
```bash
ssh -i tweeky-ec2-key.pem ubuntu@<YOUR_EC2_IP>
```

### Check Container Status
```bash
cd /opt/tweeky-app
sudo docker compose ps
```

### View Logs
```bash
# All services
sudo docker compose logs -f

# Backend only
sudo docker compose logs -f fastapi-backend

# Frontend only
sudo docker compose logs -f frontend
```

### Restart Services
```bash
# All services
sudo docker compose restart

# Specific service
sudo docker compose restart fastapi-backend
```

### Stop/Start App
```bash
# Stop
sudo docker compose down

# Start
sudo docker compose up -d
```

### Re-deploy Updated Code
From your local machine:
```bash
bash deploy/deploy-to-ec2.sh <YOUR_EC2_IP>
```

---

## 💰 Cost Breakdown

### t4g.nano (Recommended - ARM)
- **Monthly**: $3.07
- **Specs**: 512MB RAM, 2 vCPUs (burstable)
- **Storage**: 10GB SSD included
- **Data Transfer**: 100GB/month free

### t3.nano (Alternative - x86)
- **Monthly**: $3.80
- **Same specs**: 512MB RAM, 2 vCPUs

**Total Monthly Cost: ~$3-4**

---

## 🔒 Security Best Practices

### 1. Change Security Group (After Setup)
Restrict SSH access to your IP only:
```bash
# Get your security group ID
aws ec2 describe-instances --filters "Name=tag:Name,Values=TweekySqueeky-App"

# Restrict SSH to your IP
aws ec2 revoke-security-group-ingress \
    --group-id <SG_ID> \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id <SG_ID> \
    --protocol tcp \
    --port 22 \
    --cidr $(curl -s ifconfig.me)/32
```

### 2. Set Up HTTPS (Optional)
Using Caddy (automatic HTTPS):
```bash
ssh -i tweeky-ec2-key.pem ubuntu@<YOUR_EC2_IP>

# Install Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Configure Caddy
sudo nano /etc/caddy/Caddyfile
```

Add:
```
yourdomain.com {
    reverse_proxy localhost:3000
}
```

Reload:
```bash
sudo systemctl reload caddy
```

### 3. Automatic Backups
MongoDB data persists in `/var/lib/docker/volumes/tweeky-app_mongodb_data`

Backup script:
```bash
#!/bin/bash
cd /opt/tweeky-app
sudo docker compose exec -T mongodb mongodump --archive --gzip > backup-$(date +%Y%m%d).gz
```

---

## 📊 Monitoring

### System Resources
```bash
# CPU/Memory usage
htop

# Disk usage
df -h

# Docker stats
sudo docker stats
```

### Application Health
```bash
# Check if app is responding
curl http://localhost:3000/api/gateway/health

# Check MongoDB connection
sudo docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 🛠️ Troubleshooting

### App Not Accessible
```bash
# Check if containers are running
sudo docker compose ps

# Check logs for errors
sudo docker compose logs --tail=50

# Verify ports are open
sudo netstat -tulpn | grep -E '3000|5000|27017'
```

### Out of Memory
t4g.nano has only 512MB RAM. If OOM errors occur:

**Option 1**: Upgrade instance
```bash
aws ec2 stop-instances --instance-ids <INSTANCE_ID>
aws ec2 modify-instance-attribute --instance-id <INSTANCE_ID> --instance-type t4g.micro
aws ec2 start-instances --instance-ids <INSTANCE_ID>
```
Cost: $6.91/month (1GB RAM)

**Option 2**: Add swap space
```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Database Issues
```bash
# Reset database
cd /opt/tweeky-app
sudo docker compose exec fastapi-backend python scripts/seeder.py
```

---

## 🌐 Custom Domain Setup

1. **Point domain to EC2 IP** (using your DNS provider)
   - A record: `yourdomain.com` → `<EC2_PUBLIC_IP>`
   - A record: `www.yourdomain.com` → `<EC2_PUBLIC_IP>`

2. **Update nginx config** on EC2:
   ```bash
   cd /opt/tweeky-app
   sudo docker compose exec frontend sh
   vi /etc/nginx/conf.d/default.conf
   ```
   
   Change `server_name localhost;` to `server_name yourdomain.com;`

3. **Restart frontend**:
   ```bash
   sudo docker compose restart frontend
   ```

---

## 🗑️ Cleanup / Terminate Instance

When you're done testing:

```bash
# Get instance ID
aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=TweekySqueeky-App" \
    --query "Reservations[0].Instances[0].InstanceId" \
    --output text

# Terminate instance
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>

# Delete security group (after instance terminates)
aws ec2 delete-security-group --group-name tweeky-sg

# Delete key pair
aws ec2 delete-key-pair --key-name tweeky-ec2-key
rm tweeky-ec2-key.pem
```

---

## 📝 Architecture

```
┌─────────────────────────────────────┐
│      EC2 Instance (t4g.nano)        │
│         Ubuntu 24.04 ARM            │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Docker Compose             │   │
│  ├─────────────────────────────┤   │
│  │                             │   │
│  │  ┌────────────────────┐     │   │
│  │  │ Frontend (Nginx)   │     │   │
│  │  │ Port 3000→80       │     │   │
│  │  └────────┬───────────┘     │   │
│  │           │                 │   │
│  │  ┌────────▼───────────┐     │   │
│  │  │ Backend (FastAPI)  │     │   │
│  │  │ Port 5000          │     │   │
│  │  └────────┬───────────┘     │   │
│  │           │                 │   │
│  │  ┌────────▼───────────┐     │   │
│  │  │ MongoDB 7.0        │     │   │
│  │  │ Port 27017         │     │   │
│  │  └────────────────────┘     │   │
│  │                             │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
         │
         │ Internet
         ▼
     http://<EC2_IP>:3000
```

---

## 🎯 Next Steps

After deployment:

1. ✅ Access your app at `http://<EC2_IP>:3000`
2. ⚙️ Update API keys in `.env`
3. 🧪 Test all features (products, cart, chatbot)
4. 🔒 Restrict SSH to your IP only
5. 🌐 (Optional) Set up custom domain + HTTPS
6. 📊 Set up monitoring/alerts
7. 💾 Set up automatic backups

---

## 📚 Additional Resources

- [AWS EC2 Pricing](https://aws.amazon.com/ec2/pricing/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [MongoDB Backup Guide](https://www.mongodb.com/docs/manual/tutorial/backup-and-restore-tools/)

---

## 💬 Support

If you encounter issues:
1. Check logs: `sudo docker compose logs -f`
2. Verify containers: `sudo docker compose ps`
3. Test health: `curl http://localhost:3000/api/gateway/health`

For more help, check the troubleshooting section above.
