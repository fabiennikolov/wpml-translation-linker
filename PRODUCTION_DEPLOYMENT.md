# 🚀 Production Deployment Guide - Translation Service

## 📋 Prerequisites

### VPS Requirements:
- **Ubuntu 20.04+** (или друг Linux distro)
- **2GB+ RAM** (рекомендува се 4GB)
- **1 CPU core+** (рекомендува се 2+ cores)
- **20GB+ storage**
- **Root access** или sudo privileges

### Domain Setup:
- **Domain name** насочен към VPS IP
- **SSL certificate** (Let's Encrypt)
- **Firewall configured** (port 22, 80, 443, 8001)

## 🔧 Step 1: VPS Initial Setup

### Connect to VPS:
```bash
ssh root@your-vps-ip
# или
ssh username@your-vps-ip
```

### Update system:
```bash
apt update && apt upgrade -y
```

### Install required packages:
```bash
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw
```

## 🔧 Step 2: Deploy Translation Service

### Create application directory:
```bash
mkdir -p /opt/translation-service
cd /opt/translation-service
```

### Clone your repository:
```bash
git clone https://github.com/your-username/translation_service_clubs1.git .
# или upload files via SCP/SFTP
```

### Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Create production environment file:
```bash
nano .env
```

**Production .env content:**
```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# LangSmith Configuration  
LANGSMITH_API_KEY=your-langsmith-api-key-here
LANGSMITH_PROJECT=clubs1-translation-production

# Service Configuration
SERVICE_PORT=8001
SERVICE_HOST=0.0.0.0
ENVIRONMENT=production

# Security
SECRET_KEY=your-super-secret-key-here

# Logging
LOG_LEVEL=INFO
```

### Test the service:
```bash
python api.py
# Press Ctrl+C to stop
```

## 🔧 Step 3: Systemd Service Setup

### Create systemd service file:
```bash
nano /etc/systemd/system/translation-service.service
```

**Service file content:**
```ini
[Unit]
Description=Translation Service API
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/translation-service
Environment=PATH=/opt/translation-service/venv/bin
ExecStart=/opt/translation-service/venv/bin/python api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and start service:
```bash
systemctl daemon-reload
systemctl enable translation-service
systemctl start translation-service
systemctl status translation-service
```

## 🔧 Step 4: Nginx Reverse Proxy

### Create Nginx configuration:
```bash
nano /etc/nginx/sites-available/translation-service
```

**Nginx config content:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings for long translations
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

### Enable site:
```bash
ln -s /etc/nginx/sites-available/translation-service /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

## 🔧 Step 5: SSL Certificate

### Get SSL certificate:
```bash
certbot --nginx -d your-domain.com
```

### Auto-renewal setup:
```bash
crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔧 Step 6: Firewall Configuration

### Configure UFW:
```bash
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable
```

## 🔧 Step 7: Monitoring & Logs

### View service logs:
```bash
journalctl -u translation-service -f
```

### View Nginx logs:
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Create log rotation:
```bash
nano /etc/logrotate.d/translation-service
```

**Logrotate config:**
```
/opt/translation-service/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload translation-service
    endscript
}
```

## 🔧 Step 8: Health Check Script

### Create health check:
```bash
nano /opt/translation-service/health-check.sh
```

**Health check script:**
```bash
#!/bin/bash
HEALTH_URL="https://your-domain.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $RESPONSE)"
    systemctl restart translation-service
    exit 1
fi
```

### Make executable and add to cron:
```bash
chmod +x /opt/translation-service/health-check.sh
crontab -e
# Add this line (check every 5 minutes):
*/5 * * * * /opt/translation-service/health-check.sh
```

## 🔧 Step 9: Backup Script

### Create backup script:
```bash
nano /opt/translation-service/backup.sh
```

**Backup script:**
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/translation-service"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup application files
tar -czf $BACKUP_DIR/translation-service-$DATE.tar.gz /opt/translation-service

# Keep only last 7 days of backups
find $BACKUP_DIR -name "translation-service-*.tar.gz" -mtime +7 -delete

echo "Backup completed: translation-service-$DATE.tar.gz"
```

### Make executable and schedule:
```bash
chmod +x /opt/translation-service/backup.sh
crontab -e
# Add this line (daily backup at 2 AM):
0 2 * * * /opt/translation-service/backup.sh
```

## 🧪 Step 10: Testing

### Test the service:
```bash
curl https://your-domain.com/health
```

### Expected response:
```json
{
  "status": "healthy",
  "openai_configured": true,
  "langsmith_configured": true,
  "timestamp": "2024-01-XX..."
}
```

### Test translation endpoint:
```bash
curl -X POST https://your-domain.com/translate/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Тест за превод",
    "target_language": "en",
    "source_language": "bg"
  }'
```

## 🔧 Step 11: WordPress Plugin Configuration

### Update WordPress plugin settings:
```
WordPress Admin → Settings → Translation Service
- Translation Service URL: https://your-domain.com
- Test Connection → Should show ✅ Success
```

## 📊 Monitoring Commands

### Service status:
```bash
systemctl status translation-service
```

### Service logs:
```bash
journalctl -u translation-service --since "1 hour ago"
```

### Resource usage:
```bash
htop
# или
top
```

### Disk usage:
```bash
df -h
du -sh /opt/translation-service
```

## 🚨 Troubleshooting

### Service won't start:
```bash
journalctl -u translation-service -n 50
```

### Nginx errors:
```bash
nginx -t
tail -f /var/log/nginx/error.log
```

### Permission issues:
```bash
chown -R www-data:www-data /opt/translation-service
chmod -R 755 /opt/translation-service
```

### Port conflicts:
```bash
netstat -tlnp | grep :8001
lsof -i :8001
```

## 🔄 Updates & Maintenance

### Update service:
```bash
cd /opt/translation-service
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart translation-service
```

### Update system:
```bash
apt update && apt upgrade -y
```

## 📈 Scaling Considerations

### For high traffic:
- **Load balancer** (nginx upstream)
- **Multiple service instances**
- **Redis for caching**
- **Database for user management**
- **CDN for static assets**

### Monitoring tools:
- **Prometheus + Grafana**
- **Uptime monitoring** (UptimeRobot)
- **Error tracking** (Sentry)

## ✅ Production Checklist

- [ ] VPS configured with required specs
- [ ] Domain DNS pointing to VPS
- [ ] Translation service deployed and running
- [ ] Systemd service enabled and started
- [ ] Nginx reverse proxy configured
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Health checks working
- [ ] Backup system in place
- [ ] WordPress plugin configured
- [ ] Test translation successful
- [ ] Monitoring setup
- [ ] Documentation updated

## 🎯 Final URL

Your production translation service will be available at:
**https://your-domain.com**

Update your WordPress plugin settings to use this URL!
