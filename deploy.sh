#!/bin/bash

# 🚀 Translation Service Production Deployment Script
# Usage: ./deploy.sh your-domain.com

set -e

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "❌ Error: Please provide domain name"
    echo "Usage: ./deploy.sh your-domain.com"
    exit 1
fi

echo "🚀 Starting deployment for domain: $DOMAIN"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root or with sudo"
    exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y

print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx ufw curl

print_status "Creating application directory..."
mkdir -p /opt/translation-service
cd /opt/translation-service

print_status "Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

print_status "Installing Python dependencies..."
pip install -r requirements.txt

print_status "Creating systemd service..."
cat > /etc/systemd/system/translation-service.service << EOF
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
EOF

print_status "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/translation-service << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeout settings for long translations
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

print_status "Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/translation-service /etc/nginx/sites-enabled/
nginx -t

print_status "Configuring firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

print_status "Setting up log rotation..."
cat > /etc/logrotate.d/translation-service << EOF
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
EOF

print_status "Creating health check script..."
cat > /opt/translation-service/health-check.sh << EOF
#!/bin/bash
HEALTH_URL="https://$DOMAIN/health"
RESPONSE=\$(curl -s -o /dev/null -w "%{http_code}" \$HEALTH_URL)

if [ \$RESPONSE -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP \$RESPONSE)"
    systemctl restart translation-service
    exit 1
fi
EOF

chmod +x /opt/translation-service/health-check.sh

print_status "Creating backup script..."
cat > /opt/translation-service/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="/opt/backups/translation-service"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup application files
tar -czf \$BACKUP_DIR/translation-service-\$DATE.tar.gz /opt/translation-service

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "translation-service-*.tar.gz" -mtime +7 -delete

echo "Backup completed: translation-service-\$DATE.tar.gz"
EOF

chmod +x /opt/translation-service/backup.sh

print_status "Setting up cron jobs..."
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/translation-service/health-check.sh") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/translation-service/backup.sh") | crontab -

print_status "Setting proper permissions..."
chown -R www-data:www-data /opt/translation-service
chmod -R 755 /opt/translation-service

print_status "Enabling and starting services..."
systemctl daemon-reload
systemctl enable translation-service
systemctl start translation-service
systemctl reload nginx

print_warning "IMPORTANT: You need to configure your .env file!"
print_warning "Edit /opt/translation-service/.env with your API keys:"
print_warning "- OPENAI_API_KEY=your-key-here"
print_warning "- LANGSMITH_API_KEY=your-key-here"
print_warning "- SECRET_KEY=your-secret-key-here"

print_warning "After configuring .env, restart the service:"
print_warning "systemctl restart translation-service"

print_warning "Then get SSL certificate:"
print_warning "certbot --nginx -d $DOMAIN"

print_status "Deployment completed!"
print_status "Service will be available at: http://$DOMAIN"
print_status "After SSL: https://$DOMAIN"

echo ""
echo "🔧 Next steps:"
echo "1. Configure .env file with your API keys"
echo "2. Restart service: systemctl restart translation-service"
echo "3. Get SSL certificate: certbot --nginx -d $DOMAIN"
echo "4. Test: curl https://$DOMAIN/health"
echo "5. Update WordPress plugin with: https://$DOMAIN"
echo ""
echo "📊 Useful commands:"
echo "- Check service status: systemctl status translation-service"
echo "- View logs: journalctl -u translation-service -f"
echo "- Test health: curl https://$DOMAIN/health"
