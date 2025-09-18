# 🚀 Translation Service Deployment Guide

This guide will help you deploy the translation service to your server so WordPress can use it.

## 📋 Prerequisites

- Server with Python 3.8+ installed
- Domain or IP address
- SSH access to your server

## 🔧 Step 1: Prepare Your Server

### Install Python and pip (if not installed)
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

## 📁 Step 2: Upload Files to Server

Upload the entire `translation_service_clubs1` folder to your server:

```bash
# Example using scp
scp -r translation_service_clubs1 user@your-server.com:/home/user/

# Or use FTP/SFTP to upload the folder
```

## 🔧 Step 3: Install Dependencies

SSH into your server and install the required packages:

```bash
cd /home/user/translation_service_clubs1

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Step 4: Configure Environment

Create a `.env` file with your settings:

```bash
nano .env
```

Add this content (replace with your values):

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_key_here
LANGSMITH_PROJECT=clubs1-translation

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001

# Default Languages
DEFAULT_SOURCE_LANGUAGE=bg
DEFAULT_TARGET_LANGUAGE=en
```

## 🚀 Step 5: Run the Service

### Option A: Simple Run (for testing)
```bash
source venv/bin/activate
python api.py
```

### Option B: Production Run with PM2 (recommended)

Install PM2:
```bash
npm install -g pm2
```

Create PM2 configuration:
```bash
nano ecosystem.config.js
```

Add this content:
```javascript
module.exports = {
  apps: [{
    name: 'translation-service',
    script: 'api.py',
    interpreter: '/home/user/translation_service_clubs1/venv/bin/python',
    cwd: '/home/user/translation_service_clubs1',
    env: {
      NODE_ENV: 'production'
    },
    instances: 1,
    exec_mode: 'fork',
    watch: false,
    max_memory_restart: '1G'
  }]
}
```

Start with PM2:
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

## 🌐 Step 6: Configure Firewall/Reverse Proxy

### Option A: Direct Port Access
Open port 8001 in your firewall:
```bash
# UFW (Ubuntu)
sudo ufw allow 8001

# iptables
sudo iptables -A INPUT -p tcp --dport 8001 -j ACCEPT
```

### Option B: Nginx Reverse Proxy (recommended)

Create Nginx configuration:
```bash
sudo nano /etc/nginx/sites-available/translation-service
```

Add this content:
```nginx
server {
    listen 80;
    server_name translation.your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/translation-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## ✅ Step 7: Test the Service

Test if the service is running:
```bash
curl http://your-server.com:8001/
# or
curl http://translation.your-domain.com/
```

You should see:
```json
{
  "service": "Clubs1 Translation Service",
  "status": "running",
  "version": "1.0.0"
}
```

## 🔧 Step 8: Configure WordPress

1. Go to **WordPress Admin → Settings → Translation Service**
2. Set the **Translation Service URL** to:
   - `http://your-server.com:8001` (direct port access)
   - `http://translation.your-domain.com` (with reverse proxy)
3. Configure your WordPress credentials
4. Click **Test Connection** to verify

## 📝 Step 9: Use the Translation Feature

1. Edit any post in WordPress
2. Look for the **"Translate Post"** box in the sidebar
3. Click buttons like **"Translate to English"**, **"Translate to Spanish"**, etc.
4. The translated post will be created automatically and linked via WPML

## 🔍 Troubleshooting

### Service won't start
```bash
# Check logs
tail -f /var/log/syslog

# Check if port is in use
sudo netstat -tulpn | grep :8001
```

### Connection refused from WordPress
```bash
# Check firewall
sudo ufw status

# Check service status
pm2 status
pm2 logs translation-service
```

### Translation fails
```bash
# Check OpenAI API key
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.openai.com/v1/models

# Check service logs
pm2 logs translation-service
```

## 🔄 Updates

To update the service:
```bash
cd /home/user/translation_service_clubs1
git pull  # if using git
pm2 restart translation-service
```

## 🛡️ Security Tips

1. **Use HTTPS** with SSL certificates (Let's Encrypt)
2. **Restrict access** to specific IP addresses if needed
3. **Monitor logs** regularly
4. **Keep dependencies updated**
5. **Use strong API keys**

## 📞 Support

If you need help with deployment:
1. Check the logs: `pm2 logs translation-service`
2. Test the service: `curl http://your-server:8001/health`
3. Verify WordPress can reach the service

Your translation service is now ready for production use! 🎉
