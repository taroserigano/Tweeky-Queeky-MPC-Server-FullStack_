# AWS EC2 Deployment - Quick Start

## 🚀 Deploy in 2 Steps

### Step 1: Launch EC2 Instance

**PowerShell (Windows):**
```powershell
cd deploy
.\launch-ec2.ps1
```

**Bash (Mac/Linux):**
```bash
cd deploy
bash launch-ec2.sh
```

**Wait for output:**
```
Instance ID: i-0123456789abcdef
Public IP: 3.145.123.45
⏳ Wait 3 minutes for Docker installation...
```

### Step 2: Deploy Code (After 3 Minutes)

**PowerShell (Windows):**
```powershell
.\deploy-to-ec2.ps1 <YOUR_EC2_IP>
```

**Bash (Mac/Linux):**
```bash
bash deploy-to-ec2.sh <YOUR_EC2_IP>
```

Example:
```powershell
.\deploy-to-ec2.ps1 3.145.123.45
```

### Step 3: Access Your App

```
http://<YOUR_EC2_IP>:3000
```

---

## 📝 Files Overview

- **launch-ec2.ps1** / **launch-ec2.sh** - Launch EC2 instance with Docker
- **deploy-to-ec2.ps1** / **deploy-to-ec2.sh** - Deploy code to running instance
- **ec2-user-data.sh** - Auto-install script (runs on first boot)
- **AWS_EC2_DEPLOYMENT.md** - Complete deployment guide

---

## 💰 Cost

- **t4g.nano (ARM)**: $3.07/month
- **t3.nano (x86)**: $3.80/month

---

## ⚙️ Update API Keys (IMPORTANT!)

After deployment, update your environment variables:

```bash
# SSH into server (Windows)
wsl ssh -i tweeky-ec2-key.pem ubuntu@<YOUR_EC2_IP>

# SSH into server (Mac/Linux)
ssh -i tweeky-ec2-key.pem ubuntu@<YOUR_EC2_IP>

# Edit .env
cd /opt/tweeky-app
sudo nano .env

# Update these:
OPENAI_API_KEY=sk-your-real-key
ANTHROPIC_API_KEY=sk-ant-your-real-key
JWT_SECRET=your-secret-key

# Restart backend
sudo docker compose restart fastapi-backend
```

---

## 🔧 Management

### Check Status
```bash
ssh -i tweeky-ec2-key.pem ubuntu@<YOUR_EC2_IP>
cd /opt/tweeky-app
sudo docker compose ps
```

### View Logs
```bash
sudo docker compose logs -f
```

### Restart Services
```bash
sudo docker compose restart
```

---

## 📚 Full Documentation

See [AWS_EC2_DEPLOYMENT.md](./AWS_EC2_DEPLOYMENT.md) for:
- Complete setup guide
- Security configuration
- Custom domain setup
- HTTPS with Caddy
- Troubleshooting
- Monitoring
- Backup strategies

---

## 🗑️ Cleanup

To delete everything and stop charges:

```bash
# Get instance ID
aws ec2 describe-instances --filters "Name=tag:Name,Values=TweekySqueeky-App" --query "Reservations[0].Instances[0].InstanceId" --output text

# Terminate instance
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>

# Delete security group (wait for instance to terminate first)
aws ec2 delete-security-group --group-name tweeky-sg

# Delete key pair
aws ec2 delete-key-pair --key-name tweeky-ec2-key
rm tweeky-ec2-key.pem
```

---

## ✅ Prerequisites

- AWS CLI installed and configured (`aws configure`)
- WSL (for Windows users) or Bash (for Mac/Linux)
- Your project code

---

## 🆘 Need Help?

Check the [Full Documentation](./AWS_EC2_DEPLOYMENT.md) or run:
```bash
sudo docker compose logs -f
```
