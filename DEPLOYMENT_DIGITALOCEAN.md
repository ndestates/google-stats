# Google Stats Deployment on DigitalOcean with Docker

**Complete Guide to Deploying Google Stats Analytics Platform on DigitalOcean Droplet**

> **Last Updated**: January 2026
> **Estimated Deployment Time**: 30-45 minutes

---

## 📋 Table of Contents

1. [Prerequisites & Planning](#prerequisites--planning)
2. [Subdomain Configuration](#subdomain-configuration)
3. [DigitalOcean Setup](#digitalocean-setup)
4. [Docker Configuration](#docker-configuration)
5. [SSL Certificate Setup](#ssl-certificate-setup)
6. [Amazon Route 53 DNS Configuration](#amazon-route-53-dns-configuration)
7. [Firewall Setup](#firewall-setup)
8. [Deployment](#deployment)
9. [Post-Deployment](#post-deployment)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites & Planning

### What You'll Need

- **DigitalOcean Account** (https://www.digitalocean.com/) - For the Droplet
- **Amazon Route 53** - For DNS management (existing setup)
- **Domain**: `ndestates.com` (existing)
- **SSH Key Pair** - For secure access to Droplet
- **Git Access** - To clone the google-stats repository
- **Docker Knowledge** - Basic understanding of containers

### System Requirements

**Recommended Droplet Specifications:**
- **Plan**: Basic ($5-$6/month) to Pro ($12/month)
- **OS**: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS
- **CPU**: 1GB RAM minimum (2GB recommended for analytics processing)
- **Storage**: 25GB SSD minimum (50GB+ recommended for report CSV storage)
- **Region**: Choose closest to your users (e.g., US East Coast)

**Costs Estimation:**
```
DigitalOcean Droplet:      $5-12/month
Bandwidth (included):       1TB/month
Backups (optional):        $1-2/month
Total:                     ~$6-15/month
```

---

## Subdomain Configuration

### Recommended Subdomain Options

| Subdomain | Pros | Cons | Recommendation |
|-----------|------|------|-----------------|
| `analytics.ndestates.com` | Professional, descriptive | Standard naming | ⭐ **BEST** |
| `marketing.ndestates.com` | Broader purpose | Less specific | ✅ Good |
| `dashboard.ndestates.com` | Clear function | Generic | ✅ Good |
| `stats.ndestates.com` | Short, simple | Vague | ⚠️ Acceptable |
| `ga.ndestates.com` | Very short | Confusing | ❌ Not recommended |

### **Recommendation: `analytics.ndestates.com`**

**Rationale:**
- Professional and enterprise-grade naming
- SEO-friendly (descriptive subdomain)
- Scalable if you add more analytics tools
- Clear to team members and stakeholders
- Standard industry convention

**Alternative**: If you prefer the shorter version, `marketing.ndestates.com` works well for business-focused analytics.

---

## DigitalOcean Setup

### Step 1: Create a New Droplet

1. **Log in to DigitalOcean**
   - Go to https://cloud.digitalocean.com/

2. **Create a Droplet**
   - Click "Create" → "Droplets"

3. **Configure Droplet**
   ```
   Choose Image:
   - OS: Ubuntu 22.04 LTS (or 24.04 LTS)
   
   Choose Size:
   - Basic: $6/month (1GB RAM, 1 CPU, 25GB SSD)
   - or Standard: $12/month (2GB RAM, 1 CPU, 50GB SSD)
   
   Region:
   - Choose closest to your location
   - Recommended: NYC3 or SFO3 for US
   
   Authentication:
   - Select "SSH Key"
   - Add new SSH key or use existing
   
   Hostname:
   - analytics-do (or any descriptive name)
   
   Backups:
   - Optional: Enable for $1/month (recommended for production)
   ```

4. **Create the Droplet**
   - Click "Create Droplet"
   - Wait 30-60 seconds for the Droplet to boot

5. **Note Your Droplet IP**
   - You'll see the IPv4 address (e.g., `123.45.67.89`)
   - Save this for DNS configuration

### Step 2: Connect to Your Droplet

```bash
# SSH into your Droplet (replace with your actual IP)
ssh root@123.45.67.89

# Or if using non-root user (if configured)
ssh ubuntu@123.45.67.89
```

### Step 3: Initial Server Setup

Run these commands on your Droplet:

```bash
# Update system packages
apt update && apt upgrade -y

# Install essential tools
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools \
    build-essential

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Add Docker repository
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker and Docker Compose
apt update && apt install -y \
    docker.io \
    docker-compose

# Enable Docker service
systemctl enable docker
systemctl start docker

# Verify Docker installation
docker --version
docker-compose --version

# Add current user to docker group (for non-root access)
usermod -aG docker root

# Create directory for application
mkdir -p /opt/google-stats
cd /opt/google-stats
```

---

## Docker Configuration

### Step 1: Clone Repository

```bash
# Navigate to application directory
cd /opt/google-stats

# Clone the repository
git clone https://github.com/ndestates/google-stats.git .

# Or if already cloned
git pull origin master
```

### Step 2: Create Dockerfile for Production

Create `/opt/google-stats/Dockerfile.prod`:

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Create directory for reports
RUN mkdir -p /app/reports /app/logs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

### Step 3: Create docker-compose.yml for Production

Create `/opt/google-stats/docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: google-stats-web
    ports:
      - "5000:5000"
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
      - ./.env:/app/.env:ro
      - ./keys:/app/keys:ro
    environment:
      - FLASK_APP=app.py
      - FLASK_ENV=production
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      - google-stats-network
    labels:
      - "com.example.description=Google Stats Analytics Platform"

  nginx:
    image: nginx:alpine
    container_name: google-stats-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./assets:/app/assets:ro
    depends_on:
      - web
    restart: unless-stopped
    networks:
      - google-stats-network
    labels:
      - "com.example.description=Google Stats Nginx Reverse Proxy"

networks:
  google-stats-network:
    driver: bridge

volumes:
  reports:
  logs:
```

### Step 4: Create Nginx Configuration

Create `/opt/google-stats/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 20M;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name analytics.ndestates.com;
        location /.well-known/acme-challenge/ {
            root /app/ssl/letsencrypt;
        }
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name analytics.ndestates.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/live/analytics.ndestates.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/live/analytics.ndestates.com/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
        ssl_prefer_server_ciphers on;
        ssl_session_timeout 1d;
        ssl_session_cache shared:SSL:50m;
        ssl_session_tickets off;

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

        # Security headers
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        location / {
            limit_req zone=general burst=20 nodelay;
            
            proxy_pass http://web:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $server_name;
            
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        location /api/ {
            limit_req zone=api burst=50 nodelay;
            
            proxy_pass http://web:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /assets/ {
            alias /app/assets/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        location /reports/ {
            proxy_pass http://web:5000;
            proxy_set_header Host $host;
            proxy_buffering off;
            proxy_request_buffering off;
        }

        location /health {
            access_log off;
            proxy_pass http://web:5000/health;
        }
    }
}
```

### Step 5: Install Gunicorn

Update `requirements.txt` to include:

```
gunicorn>=21.0.0
```

Then rebuild: `pip install -r requirements.txt`

---

## SSL Certificate Setup

### Option A: Let's Encrypt with Certbot (Recommended - FREE)

```bash
# SSH into your Droplet
ssh root@YOUR_DROPLET_IP

# Install Certbot
apt install -y certbot python3-certbot-dns-route53

# Create SSL directory
mkdir -p /opt/google-stats/ssl

# Run Certbot for DNS validation
certbot certonly \
  --dns-route53 \
  -d analytics.ndestates.com \
  -d www.analytics.ndestates.com \
  --agree-tos \
  --no-eff-email \
  --email admin@ndestates.com \
  --config-dir /opt/google-stats/ssl/live \
  --work-dir /opt/google-stats/ssl/work \
  --logs-dir /opt/google-stats/ssl/logs

# Verify certificate
ls -la /opt/google-stats/ssl/live/analytics.ndestates.com/
```

**What Certbot Does:**
- Creates `/opt/google-stats/ssl/live/analytics.ndestates.com/fullchain.pem`
- Creates `/opt/google-stats/ssl/live/analytics.ndestates.com/privkey.pem`
- Automatically renews certificates before expiration

### Option B: Self-Signed Certificate (Testing Only)

```bash
# Generate self-signed certificate (valid for 365 days)
mkdir -p /opt/google-stats/ssl/live/analytics.ndestates.com/

openssl req -x509 -newkey rsa:4096 \
  -keyout /opt/google-stats/ssl/live/analytics.ndestates.com/privkey.pem \
  -out /opt/google-stats/ssl/live/analytics.ndestates.com/fullchain.pem \
  -days 365 -nodes \
  -subj "/C=US/ST=State/L=City/O=ndestates/CN=analytics.ndestates.com"

# Fix permissions
chmod 600 /opt/google-stats/ssl/live/analytics.ndestates.com/privkey.pem
chmod 644 /opt/google-stats/ssl/live/analytics.ndestates.com/fullchain.pem
```

### Setup Auto-Renewal

Create `/opt/google-stats/renew-cert.sh`:

```bash
#!/bin/bash

# Renew Let's Encrypt certificate
certbot renew \
  --config-dir /opt/google-stats/ssl/live \
  --work-dir /opt/google-stats/ssl/work \
  --logs-dir /opt/google-stats/ssl/logs \
  --quiet

# Reload Nginx in Docker
docker-compose -f /opt/google-stats/docker-compose.prod.yml exec -T nginx nginx -s reload
```

Make executable and add to crontab:

```bash
chmod +x /opt/google-stats/renew-cert.sh

# Add to crontab (run daily at 2 AM)
crontab -e

# Add this line:
# 0 2 * * * /opt/google-stats/renew-cert.sh >> /var/log/certbot-renew.log 2>&1
```

---

## Amazon Route 53 DNS Configuration

### Step 1: Verify Domain

Ensure your domain `ndestates.com` is registered and its nameservers point to Route 53.

### Step 2: Create A Record for Subdomain

1. **Log in to AWS Console**
   - Go to https://console.aws.amazon.com/
   - Navigate to Route 53

2. **Create A Record**
   ```
   Hosted Zone: ndestates.com
   
   Create Record:
   ├─ Name: analytics
   ├─ Type: A
   ├─ Value: 123.45.67.89 (Your DigitalOcean Droplet IP)
   ├─ TTL: 300 (5 minutes - adjustable for stability)
   └─ Routing Policy: Simple routing
   ```

3. **Create AAAA Record (IPv6 - Optional)**
   ```
   If your Droplet has IPv6:
   ├─ Name: analytics
   ├─ Type: AAAA
   ├─ Value: [your-ipv6-address]
   └─ TTL: 300
   ```

### Step 3: DNS Verification

```bash
# Test DNS resolution
nslookup analytics.ndestates.com
dig analytics.ndestates.com

# Should return your Droplet IP: 123.45.67.89
```

### Step 4: Create Additional Records (Optional)

```
For www subdomain:
├─ Name: www.analytics
├─ Type: CNAME
├─ Value: analytics.ndestates.com
└─ TTL: 300

For API endpoint:
├─ Name: api.analytics
├─ Type: A
├─ Value: 123.45.67.89
└─ TTL: 300
```

---

## Firewall Setup

### DigitalOcean Firewall

1. **Create Firewall in DigitalOcean Console**

   ```
   Firewall Name: google-stats-firewall
   
   Inbound Rules:
   ├─ HTTP (port 80) - from Anywhere
   ├─ HTTPS (port 443) - from Anywhere
   └─ SSH (port 22) - from Your IP Only
   
   Outbound Rules:
   ├─ All TCP - to Anywhere
   └─ All UDP - to Anywhere
   
   Apply to: Your analytics-do Droplet
   ```

2. **CLI Setup (Optional)**

   ```bash
   # Install doctl CLI
   cd ~
   wget https://github.com/digitalocean/doctl/releases/download/v1.106.0/doctl-1.106.0-linux-amd64.tar.gz
   tar xf ~/doctl-1.106.0-linux-amd64.tar.gz
   sudo mv ~/doctl /usr/local/bin
   
   # Authenticate
   doctl auth init
   
   # Create firewall
   doctl compute firewall create \
     --name google-stats-firewall \
     --inbound-rules protocol:tcp,ports:80,sources:addresses:0.0.0.0,sources:addresses::/0 \
     --inbound-rules protocol:tcp,ports:443,sources:addresses:0.0.0.0,sources:addresses::/0 \
     --inbound-rules protocol:tcp,ports:22,sources:addresses:YOUR_IP \
     --outbound-rules protocol:tcp,destinations:addresses:0.0.0.0,destinations:addresses::/0 \
     --outbound-rules protocol:udp,destinations:addresses:0.0.0.0,destinations:addresses::/0
   ```

### AWS Route 53 Security

1. **DNSSEC (Optional but Recommended)**
   ```
   Route 53 Console:
   └─ Hosted Zone: ndestates.com
      └─ DNSSEC Signing
         ├─ Enable signing
         ├─ KSK signing status: Active
         └─ ZSK signing status: Active
   ```

2. **Rate Limiting**
   ```
   Route 53 Configuration:
   └─ Query Logging: Enable
      └─ CloudWatch Logs Group: /aws/route53/ndestates.com
   ```

3. **Access Control**
   ```
   AWS IAM:
   └─ Create policy for Route 53 access
      └─ Limit to specific records (analytics.ndestates.com)
   ```

### Uptime Monitoring

Route 53 Health Checks:

```
Create Health Check:
├─ Type: HTTPS
├─ IP Address: 123.45.67.89
├─ Port: 443
├─ Path: /health
├─ Interval: 30 seconds
└─ Failure threshold: 3
```

---

## Deployment

### Step 1: Prepare Environment File

Create `/opt/google-stats/.env`:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secure-random-key-here

# Google Analytics 4
GA4_PROPERTY_ID=275378361
GA4_KEY_PATH=/app/keys/ga4-key.json

# Google Search Console
GSC_SITE_URL=https://www.ndestates.com/
GSC_KEY_PATH=/app/keys/ga4-key.json

# Google Ads API
GOOGLE_ADS_CUSTOMER_ID=5933984170
GOOGLE_ADS_LOGIN_CUSTOMER_ID=2445831419
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
```

**⚠️ Security Note**: Never commit `.env` to git. Keep sensitive credentials secure.

### Step 2: Deploy with Docker Compose

```bash
# SSH into Droplet
ssh root@123.45.67.89

# Navigate to app directory
cd /opt/google-stats

# Pull latest code
git pull origin master

# Build Docker image
docker-compose -f docker-compose.prod.yml build

# Start containers
docker-compose -f docker-compose.prod.yml up -d

# Verify containers are running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Step 3: Verify Deployment

```bash
# Check if web service is running
docker-compose -f docker-compose.prod.yml logs web | head -20

# Check Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx | head -20

# Test connectivity from Droplet
curl http://localhost:5000/health

# Test through Nginx
curl http://localhost/health
```

### Step 4: Enable HTTPS

Once DNS is configured:

```bash
# Install Certbot with Route 53 plugin
apt install -y certbot python3-certbot-dns-route53

# Request certificate
certbot certonly \
  --dns-route53 \
  -d analytics.ndestates.com \
  --agree-tos \
  --email admin@ndestates.com \
  --config-dir /opt/google-stats/ssl/live \
  --work-dir /opt/google-stats/ssl/work \
  --logs-dir /opt/google-stats/ssl/logs

# Copy certificates
cp /opt/google-stats/ssl/live/analytics.ndestates.com/* \
   /opt/google-stats/ssl/live/analytics.ndestates.com/

# Restart Nginx to enable HTTPS
docker-compose -f docker-compose.prod.yml restart nginx
```

---

## Post-Deployment

### Step 1: Access Your Application

```
https://analytics.ndestates.com

You should see:
✅ Google Stats Web Interface
✅ Dashboard with all analytics tools
✅ SSL certificate valid (green lock icon)
```

### Step 2: Test Core Functionality

```bash
# SSH into Droplet
ssh root@123.45.67.89

# Test reports directory
ls -la /opt/google-stats/reports/

# Run a test report (inside container)
docker-compose -f docker-compose.prod.yml exec web \
  python3 scripts/yesterday_report.py

# Check generated CSV
ls -la /opt/google-stats/reports/
```

### Step 3: Setup Automated Reporting

Create `/opt/google-stats/cron-jobs.sh`:

```bash
#!/bin/bash

# Automated daily reports
# 8 AM daily report
0 8 * * * docker-compose -f /opt/google-stats/docker-compose.prod.yml exec -T web python3 scripts/yesterday_report.py >> /opt/google-stats/logs/cron-yesterday-report.log 2>&1

# 10 AM weekly report (Mondays)
0 10 * * 1 docker-compose -f /opt/google-stats/docker-compose.prod.yml exec -T web python3 scripts/google_ads_performance.py >> /opt/google-stats/logs/cron-ads-report.log 2>&1

# 12 PM monthly campaign report (1st of month)
0 12 1 * * docker-compose -f /opt/google-stats/docker-compose.prod.yml exec -T web python3 scripts/campaign_performance.py >> /opt/google-stats/logs/cron-campaign-report.log 2>&1
```

Add to crontab:
```bash
crontab -e
# Copy content from cron-jobs.sh
```

### Step 4: Setup Monitoring

Create monitoring script `/opt/google-stats/monitoring.sh`:

```bash
#!/bin/bash

# Check containers health
docker-compose -f /opt/google-stats/docker-compose.prod.yml ps

# Check disk space
df -h /opt/google-stats/

# Check memory usage
free -h

# Check application logs for errors
docker-compose -f /opt/google-stats/docker-compose.prod.yml logs --tail=50 web | grep -i error

# Check Nginx status
docker-compose -f /opt/google-stats/docker-compose.prod.yml exec -T nginx nginx -t
```

---

## Monitoring & Maintenance

### Daily Monitoring Checklist

```bash
# SSH to Droplet
ssh root@YOUR_DROPLET_IP

# 1. Container Status
docker-compose -f /opt/google-stats/docker-compose.prod.yml ps

# 2. System Resources
df -h
free -h
top -b -n 1 | head -20

# 3. Application Logs
docker-compose -f /opt/google-stats/docker-compose.prod.yml logs --tail=100 web

# 4. Disk Space for Reports
du -sh /opt/google-stats/reports/

# 5. Certificate Expiration
certbot certificates --config-dir /opt/google-stats/ssl/live
```

### Weekly Tasks

```bash
# Update system packages
apt update && apt upgrade -y

# Prune old Docker images and containers
docker system prune -f

# Backup reports directory
tar -czf /backups/reports-$(date +%Y-%m-%d).tar.gz \
    /opt/google-stats/reports/

# Check certificate renewal
certbot renew --dry-run \
    --config-dir /opt/google-stats/ssl/live
```

### Monthly Tasks

```bash
# Review logs for errors
docker-compose -f /opt/google-stats/docker-compose.prod.yml logs --since 30d web | grep ERROR

# Backup entire application
tar -czf /backups/google-stats-$(date +%Y-%m-%d).tar.gz \
    /opt/google-stats/

# Update application code
cd /opt/google-stats
git pull origin master
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Review and clean old report files (keep 90 days)
find /opt/google-stats/reports/ -mtime +90 -delete
```

### Backup Strategy

Create `/opt/google-stats/backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/mnt/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup reports
tar -czf $BACKUP_DIR/reports_$TIMESTAMP.tar.gz \
    /opt/google-stats/reports/

# Backup application (without node_modules and cache)
tar -czf $BACKUP_DIR/app_$TIMESTAMP.tar.gz \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='htmlcov' \
    --exclude='.pytest_cache' \
    /opt/google-stats/

# Backup database (if applicable)
# mysqldump -u user -p database > $BACKUP_DIR/db_$TIMESTAMP.sql

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/reports_$TIMESTAMP.tar.gz"
echo "Backup completed: $BACKUP_DIR/app_$TIMESTAMP.tar.gz"
```

Add to crontab:
```bash
# Backup daily at 3 AM
0 3 * * * /opt/google-stats/backup.sh >> /var/log/backup.log 2>&1
```

### Performance Tuning

**Nginx Configuration Optimization** (`nginx.conf`):

```nginx
# Increase worker processes
worker_processes auto;

# Increase max connections
events {
    worker_connections 4096;
}

# Enable caching headers
http {
    # Browser caching for static assets
    map $sent_http_content_type $expires {
        default                    off;
        text/html                  epoch;
        text/css                   max;
        application/javascript     max;
        ~image/                    max;
    }

    expires $expires;
}
```

**Flask/Gunicorn Configuration**:

```bash
# In docker-compose.prod.yml, adjust Gunicorn workers:
# 2-4 x CPU cores + 1
# For 1 CPU: use 3 workers
# For 2 CPU: use 5 workers

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--worker-class", "sync", "--timeout", "120", "app:app"]
```

---

## Troubleshooting

### Common Issues & Solutions

#### 1. SSL Certificate Not Found

**Error**: `SSL_ERROR_RX_RECORD_TOO_LONG` or certificate not found

**Solution**:
```bash
# Check certificate path
ls -la /opt/google-stats/ssl/live/analytics.ndestates.com/

# If missing, request new certificate
certbot certonly --dns-route53 -d analytics.ndestates.com

# Verify Nginx config
docker-compose -f docker-compose.prod.yml exec -T nginx nginx -t

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

#### 2. DNS Not Resolving

**Error**: `Failed to resolve analytics.ndestates.com`

**Solution**:
```bash
# Flush local DNS cache
systemctl restart systemd-resolved

# Test DNS from Droplet
nslookup analytics.ndestates.com 8.8.8.8
dig analytics.ndestates.com

# Verify Route 53 record
# AWS Console → Route 53 → Hosted Zones → ndestates.com
# Look for 'A' record pointing to your Droplet IP
```

#### 3. Containers Keep Restarting

**Error**: `docker-compose ps` shows containers restarting

**Solution**:
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Common causes:
# 1. Missing .env file
ls -la /opt/google-stats/.env

# 2. Missing keys directory
ls -la /opt/google-stats/keys/

# 3. Port already in use
netstat -tuln | grep 5000

# 4. Rebuild containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

#### 4. Slow Response Times

**Error**: Application takes 10+ seconds to load

**Solution**:
```bash
# Check resource usage
docker stats

# Monitor Python process
docker-compose -f docker-compose.prod.yml top web

# Check disk I/O
iostat -x 1 5

# Increase Droplet resources or optimize:
# 1. Enable caching headers
# 2. Reduce report data size
# 3. Optimize database queries
# 4. Implement pagination
```

#### 5. Reports Directory Filling Up Disk

**Error**: `Disk full` or out of space warnings

**Solution**:
```bash
# Check disk usage
df -h

# Find large files
du -sh /opt/google-stats/reports/* | sort -rh

# Archive old reports
tar -czf /backups/old-reports.tar.gz /opt/google-stats/reports/*.csv -mtime +90

# Delete old reports (keep 90 days)
find /opt/google-stats/reports/ -name "*.csv" -mtime +90 -delete

# Set up automated cleanup in cron
# 0 2 * * * find /opt/google-stats/reports/ -name "*.csv" -mtime +90 -delete
```

#### 6. API Rate Limits or Google API Quota Errors

**Error**: `Quota exceeded` or `Rate limit exceeded`

**Solution**:
```bash
# Check current quota usage in Google Cloud Console
# Adjust exponential backoff in src/ga4_client.py
# Implement caching for frequent queries
# Stagger automated reports to different times
# Consider upgrading to higher API quota tier
```

#### 7. Certificate Renewal Failed

**Error**: Certificate expires soon or renewal fails

**Solution**:
```bash
# Check renewal status
certbot certificates --config-dir /opt/google-stats/ssl/live

# Manually renew
certbot renew --force-renewal \
    --config-dir /opt/google-stats/ssl/live

# Check renewal logs
cat /opt/google-stats/ssl/logs/letsencrypt.log | tail -20

# Verify Route 53 DNS challenge records exist
# (They're temporary and disappear after renewal)
```

### Getting Help

**Log Files to Check**:
```bash
# Web application logs
docker-compose -f docker-compose.prod.yml logs web

# Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# System logs
tail -f /var/log/syslog

# Docker daemon logs
journalctl -u docker.service -f

# Certificate renewal logs
tail -f /opt/google-stats/ssl/logs/letsencrypt.log

# Cron job logs
grep CRON /var/log/syslog
```

**Debug Mode**:
```bash
# Enable Flask debug mode (development only!)
# Edit .env: FLASK_DEBUG=1
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml logs -f web
```

---

## Cost Analysis & Optimization

### Monthly Costs

| Service | Cost | Notes |
|---------|------|-------|
| **DigitalOcean Droplet** | $5-$12/month | Depends on size (1GB to 2GB RAM) |
| **Data Transfer** | $0 | 1TB included, $0.01/GB after |
| **Backups** | $1-$2/month | Optional, 20% of Droplet cost |
| **DNS (Route 53)** | ~$0.50/month | $0.40 per hosted zone + $0.40 per million queries |
| **SSL Certificate** | $0 | Free with Let's Encrypt |
| **Total** | **$6-$15/month** | Very affordable for analytics platform |

### Cost Optimization Tips

1. **Use Basic Droplet** ($5/month) for low to medium traffic
2. **Enable Droplet Backups** only if data is critical
3. **Use CDN** (DigitalOcean Spaces) for large asset files
4. **Archive Old Reports** to reduce storage needs
5. **Monitor Data Transfer** to stay within 1TB/month limit

---

## Scaling Considerations

### When to Upgrade

- **CPU/Memory**: If `docker stats` shows >80% usage
- **Storage**: If `/opt/google-stats/reports` exceeds 50% of disk
- **Bandwidth**: If monthly data transfer exceeds 800GB
- **Concurrent Users**: If response times exceed 2 seconds

### Scaling Steps

```bash
# Option 1: Upgrade Droplet (Recommended for $5→$12 migration)
# 1. Create backup: tar -czf backup.tar.gz /opt/google-stats/
# 2. Snapshot current Droplet in DigitalOcean console
# 3. Resize Droplet to next size (click "Resize" in console)
# 4. No data loss, minimal downtime (~2 minutes)

# Option 2: Migrate to Load Balanced Setup
# 1. Create second Droplet with same image
# 2. Setup DigitalOcean Load Balancer
# 3. Point both Droplets to load balancer
# 4. Update Route 53 to point to load balancer IP

# Option 3: Use DigitalOcean App Platform (Managed Docker)
# Higher cost but fully managed by DigitalOcean
# No infrastructure maintenance needed
```

---

## Security Checklist

- [ ] SSH key authentication configured (no password login)
- [ ] Firewall restricted to necessary ports (80, 443, 22)
- [ ] .env file secured with restricted permissions (600)
- [ ] API keys stored as environment variables
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled
- [ ] Automated backups configured
- [ ] Monitoring and alerts setup
- [ ] Regular system updates scheduled
- [ ] DNSSEC enabled in Route 53 (optional)
- [ ] Log retention and review process established

---

## Additional Resources

- **DigitalOcean Docs**: https://docs.digitalocean.com/
- **Docker Docs**: https://docs.docker.com/
- **Nginx Docs**: https://nginx.org/en/docs/
- **Let's Encrypt**: https://letsencrypt.org/
- **AWS Route 53**: https://docs.aws.amazon.com/route53/
- **Certbot**: https://certbot.eff.org/

---

## Support & Maintenance

### Monthly Review Checklist

- [ ] Check SSL certificate expiration date
- [ ] Review application error logs
- [ ] Verify backups completed successfully
- [ ] Monitor disk space usage
- [ ] Check for system updates needed
- [ ] Review Route 53 query logs
- [ ] Test disaster recovery procedures
- [ ] Update documentation as needed

### When to Contact Support

**DigitalOcean Support**: Network, Droplet, Firewall issues
**AWS Support**: Route 53, DNS resolution issues
**Certbot Issues**: Visit https://certbot.eff.org/faq/
**Application Issues**: Check logs, review source code

---

**Last Updated**: January 2026  
**Maintainer**: ND Holdings Limited  
**Version**: 1.0.0
