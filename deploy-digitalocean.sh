#!/bin/bash
# Quick deployment script for Google Stats on DigitalOcean
# This script automates initial setup on a fresh Ubuntu 22.04 LTS Droplet

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="${1:-}"
DOMAIN="analytics.ndestates.com"
APP_DIR="/opt/google-stats"
REPO_URL="https://github.com/ndestates/google-stats.git"

# Functions
print_header() {
    echo -e "${BLUE}=================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}=================================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root"
    exit 1
fi

print_header "Google Stats - DigitalOcean Deployment Script"

# Step 1: Update system
print_header "Step 1: Updating System Packages"
apt update
apt upgrade -y
print_success "System updated"

# Step 2: Install Docker
print_header "Step 2: Installing Docker and Docker Compose"

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
print_success "Docker GPG key added"

# Add Docker repository
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update
print_success "Docker repository added"

# Install Docker
apt install -y docker.io docker-compose
systemctl enable docker
systemctl start docker
print_success "Docker installed and enabled"

# Verify Docker installation
docker --version
docker-compose --version

# Step 3: Install essential tools
print_header "Step 3: Installing Essential Tools"
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    build-essential \
    certbot \
    python3-certbot-dns-route53

print_success "Essential tools installed"

# Step 4: Create application directory
print_header "Step 4: Creating Application Directory"
mkdir -p "$APP_DIR"
cd "$APP_DIR"
print_success "Application directory created: $APP_DIR"

# Step 5: Clone repository
print_header "Step 5: Cloning Google Stats Repository"
if [ ! -d "$APP_DIR/.git" ]; then
    git clone "$REPO_URL" .
    print_success "Repository cloned"
else
    git pull origin master
    print_success "Repository updated"
fi

# Step 6: Create SSL directory structure
print_header "Step 6: Creating SSL Directory Structure"
mkdir -p "$APP_DIR/ssl/live/$DOMAIN"
mkdir -p "$APP_DIR/ssl/letsencrypt"
mkdir -p "$APP_DIR/ssl/work"
mkdir -p "$APP_DIR/ssl/logs"
print_success "SSL directories created"

# Step 7: Create keys directory
print_header "Step 7: Creating Keys Directory"
mkdir -p "$APP_DIR/keys"
chmod 700 "$APP_DIR/keys"
print_success "Keys directory created and secured"

# Step 8: Create logs and reports directories
print_header "Step 8: Creating Logs and Reports Directories"
mkdir -p "$APP_DIR/logs"
mkdir -p "$APP_DIR/reports"
chmod 777 "$APP_DIR/logs"
chmod 777 "$APP_DIR/reports"
print_success "Logs and reports directories created"

# Step 9: Create .env template
print_header "Step 9: Creating Environment File Template"
cat > "$APP_DIR/.env.template" << 'EOF'
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=change-this-to-a-secure-random-string-here

# Google Analytics 4
GA4_PROPERTY_ID=your-property-id
GA4_KEY_PATH=/app/keys/ga4-key.json

# Google Search Console
GSC_SITE_URL=https://www.ndestates.com/
GSC_KEY_PATH=/app/keys/ga4-key.json

# Google Ads API
GOOGLE_ADS_CUSTOMER_ID=your-customer-id
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your-manager-account-id
GOOGLE_ADS_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=your-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_JSON_KEY_PATH=/app/keys/google-ads-key.json

# Logging
LOG_LEVEL=INFO
WEB_LOG_LEVEL=INFO

# Application
REPORTS_DIR=/app/reports
SCRIPTS_DIR=/app/scripts
LOGS_DIR=/app/logs

# Domain
DOMAIN=analytics.ndestates.com
EOF

chmod 600 "$APP_DIR/.env.template"
print_success ".env template created at $APP_DIR/.env.template"
print_warning "IMPORTANT: Copy .env.template to .env and fill in your credentials"

# Step 10: Build Docker images
print_header "Step 10: Building Docker Images"
cd "$APP_DIR"
docker-compose -f docker-compose.prod.yml build
print_success "Docker images built successfully"

# Step 11: Create systemd service
print_header "Step 11: Creating Systemd Service"
cat > /etc/systemd/system/google-stats.service << 'EOF'
[Unit]
Description=Google Stats Analytics Platform
Requires=docker.service
After=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/google-stats
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable google-stats.service
print_success "Systemd service created and enabled"

# Step 12: Create helpful scripts
print_header "Step 12: Creating Helper Scripts"

# Deploy script
cat > "$APP_DIR/deploy.sh" << 'EOF'
#!/bin/bash
# Deploy latest version of Google Stats

cd /opt/google-stats

echo "Pulling latest code..."
git pull origin master

echo "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

echo "Restarting containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "Checking status..."
docker-compose -f docker-compose.prod.yml ps

echo "Deployment complete!"
EOF

chmod +x "$APP_DIR/deploy.sh"
print_success "Deploy script created"

# Backup script
cat > "$APP_DIR/backup.sh" << 'EOF'
#!/bin/bash
# Backup Google Stats data

BACKUP_DIR="/mnt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

echo "Backing up reports..."
tar -czf $BACKUP_DIR/reports_$TIMESTAMP.tar.gz /opt/google-stats/reports/

echo "Backing up application..."
tar -czf $BACKUP_DIR/app_$TIMESTAMP.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='htmlcov' \
    /opt/google-stats/

# Keep only last 30 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backups completed successfully!"
ls -lh $BACKUP_DIR/
EOF

chmod +x "$APP_DIR/backup.sh"
print_success "Backup script created"

# Monitor script
cat > "$APP_DIR/monitor.sh" << 'EOF'
#!/bin/bash
# Monitor Google Stats containers

echo "Container Status:"
docker-compose -f /opt/google-stats/docker-compose.prod.yml ps

echo ""
echo "Docker Stats:"
docker stats --no-stream

echo ""
echo "Disk Usage:"
df -h /opt/google-stats/

echo ""
echo "Recent Logs:"
docker-compose -f /opt/google-stats/docker-compose.prod.yml logs --tail=20 web
EOF

chmod +x "$APP_DIR/monitor.sh"
print_success "Monitor script created"

# Step 13: Summary
print_header "Deployment Preparation Complete!"

echo -e "\n${YELLOW}NEXT STEPS:${NC}\n"

echo "1. Configure environment variables:"
echo "   cp $APP_DIR/.env.template $APP_DIR/.env"
echo "   # Edit with your Google API credentials:"
echo "   vim $APP_DIR/.env"

echo ""
echo "2. Add your Google API key files to:"
echo "   mkdir -p $APP_DIR/keys"
echo "   # Copy your JSON key files here"

echo ""
echo "3. Setup DNS in AWS Route 53:"
echo "   - Create A record: analytics.ndestates.com"
echo "   - Point to your Droplet IP"
echo "   - Wait for DNS propagation (5-10 minutes)"

echo ""
echo "4. Request SSL certificate:"
echo "   certbot certonly --dns-route53 \\"
echo "     -d $DOMAIN \\"
echo "     --config-dir $APP_DIR/ssl/live \\"
echo "     --work-dir $APP_DIR/ssl/work \\"
echo "     --logs-dir $APP_DIR/ssl/logs \\"
echo "     --agree-tos \\"
echo "     --email admin@ndestates.com"

echo ""
echo "5. Start the application:"
echo "   cd $APP_DIR"
echo "   docker-compose -f docker-compose.prod.yml up -d"

echo ""
echo "6. Verify deployment:"
echo "   docker-compose -f docker-compose.prod.yml ps"
echo "   docker-compose -f docker-compose.prod.yml logs -f web"

echo ""
echo -e "${GREEN}Documentation: $APP_DIR/DEPLOYMENT_DIGITALOCEAN.md${NC}\n"

print_success "Setup complete! Follow the next steps above."
