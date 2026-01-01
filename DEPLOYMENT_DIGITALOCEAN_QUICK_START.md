# DigitalOcean Deployment - Quick Start Guide

**Estimated Time**: 30-45 minutes  
**Difficulty**: Intermediate  
**Cost**: ~$6-15/month

---

## 🎯 Quick Summary

This guide deploys Google Stats on a DigitalOcean Droplet with:
- ✅ Docker containerization
- ✅ Nginx reverse proxy
- ✅ Let's Encrypt SSL (free)
- ✅ Subdomain: `analytics.ndestates.com`
- ✅ Route 53 DNS integration
- ✅ Automated backups & monitoring

---

## 📋 Prerequisites Checklist

- [ ] DigitalOcean account created
- [ ] Google API credentials ready (.env values)
- [ ] AWS Route 53 access for DNS
- [ ] SSH key pair configured
- [ ] Droplet IP address noted
- [ ] Domain: `ndestates.com` verified

---

## 🚀 Quick Start (5 Steps)

### Step 1: Create DigitalOcean Droplet (2 minutes)

```bash
# Visit: https://cloud.digitalocean.com/

# Settings:
OS: Ubuntu 22.04 LTS
Size: $6/month (1GB RAM, 1 CPU, 25GB SSD) - Basic plan
Region: NYC3 (or closest to you)
Auth: SSH Key
Hostname: analytics-do

# After creation, note your Droplet IP:
# 123.45.67.89
```

### Step 2: Initial Server Setup (5 minutes)

```bash
# SSH into Droplet
ssh root@123.45.67.89

# Run automated setup script
# (Complete script is in deploy-digitalocean.sh)
bash deploy-digitalocean.sh
```

### Step 3: Configure Credentials (5 minutes)

```bash
# On your local machine, copy .env template
scp root@123.45.67.89:/opt/google-stats/.env.template ./google-stats.env

# Edit with your Google credentials
# Get values from: README_Google_Ads_Credentials.md
nano google-stats.env

# Copy back to Droplet
scp ./google-stats.env root@123.45.67.89:/opt/google-stats/.env

# Copy your Google API key files
scp ./keys/*.json root@123.45.67.89:/opt/google-stats/keys/
```

### Step 4: Setup DNS & SSL (10 minutes)

```bash
# SSH into Droplet
ssh root@123.45.67.89

# 1. Configure DNS in AWS Route 53:
#    - Go to AWS Console → Route 53
#    - Hosted Zone: ndestates.com
#    - Create A Record:
#      Name: analytics
#      Type: A
#      Value: 123.45.67.89 (Your Droplet IP)
#      TTL: 300

# 2. Wait 5-10 minutes for DNS propagation
# 3. Test DNS:
nslookup analytics.ndestates.com

# 4. Request SSL certificate
certbot certonly --dns-route53 \
  -d analytics.ndestates.com \
  --config-dir /opt/google-stats/ssl/live \
  --work-dir /opt/google-stats/ssl/work \
  --logs-dir /opt/google-stats/ssl/logs \
  --agree-tos \
  --email admin@ndestates.com
```

### Step 5: Start Application (3 minutes)

```bash
# SSH into Droplet
ssh root@123.45.67.89

# Navigate to app directory
cd /opt/google-stats

# Start the application
docker-compose -f docker-compose.prod.yml up -d

# Verify it's running
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web

# Access application
# https://analytics.ndestates.com
```

---

## ✅ Verification Checklist

After deployment, verify everything works:

```bash
# 1. Check containers
docker-compose -f docker-compose.prod.yml ps
# Status: Up (both web and nginx)

# 2. Test web interface
curl http://localhost:5000/health
# Response: 200 OK

# 3. Test Nginx
curl http://localhost/health
# Response: 200 OK

# 4. Check DNS
nslookup analytics.ndestates.com
# Should return your Droplet IP

# 5. Test HTTPS
curl -I https://analytics.ndestates.com
# Response: 200 OK with valid SSL
```

---

## 📊 Application Access

| URL | Purpose |
|-----|---------|
| `https://analytics.ndestates.com` | Main dashboard |
| `https://analytics.ndestates.com/health` | Health check |
| `https://analytics.ndestates.com/documentation.php` | API documentation |

---

## 🛠️ Common Commands

### Manage Application

```bash
# Start
docker-compose -f docker-compose.prod.yml up -d

# Stop
docker-compose -f docker-compose.prod.yml down

# Restart
docker-compose -f docker-compose.prod.yml restart

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# View container status
docker-compose -f docker-compose.prod.yml ps
```

### Monitor System

```bash
# View resource usage
docker stats

# Check disk space
df -h /opt/google-stats/

# View running processes
docker-compose -f docker-compose.prod.yml top web

# Monitor in real-time
watch -n 5 'docker stats --no-stream'
```

### Run Reports

```bash
# Inside container
docker-compose -f docker-compose.prod.yml exec web \
  python3 scripts/yesterday_report.py

# Check generated reports
ls -la /opt/google-stats/reports/
```

### Update Application

```bash
# Pull latest code
git pull origin master

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Restart with new images
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔒 Firewall Configuration

### DigitalOcean Firewall Rules

Create firewall in DigitalOcean Console:

| Direction | Port | Protocol | Source | Purpose |
|-----------|------|----------|--------|---------|
| Inbound | 80 | TCP | Anywhere | HTTP redirect |
| Inbound | 443 | TCP | Anywhere | HTTPS |
| Inbound | 22 | TCP | Your IP | SSH access |
| Outbound | All | All | Anywhere | API calls |

### Route 53 Security

1. Enable DNSSEC signing (optional)
2. Setup query logging for monitoring
3. Create IAM policy limiting DNS changes

---

## 🆘 Quick Troubleshooting

### DNS Not Resolving

```bash
# Test DNS
nslookup analytics.ndestates.com 8.8.8.8

# If fails, check Route 53:
# 1. AWS Console → Route 53 → Hosted Zones
# 2. Verify A record exists for 'analytics'
# 3. Check IP matches your Droplet
# 4. Wait 5-10 minutes for propagation
```

### SSL Certificate Issues

```bash
# Check certificate status
certbot certificates --config-dir /opt/google-stats/ssl/live

# If missing, request new:
certbot certonly --dns-route53 -d analytics.ndestates.com \
  --config-dir /opt/google-stats/ssl/live

# Verify Nginx config
docker-compose -f docker-compose.prod.yml exec -T nginx nginx -t

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Containers Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Ensure .env file exists
ls -la /opt/google-stats/.env

# Rebuild containers
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

---

## 📈 Maintenance Tasks

### Daily
- Check container status: `docker-compose ps`
- Monitor logs for errors: `docker-compose logs web`

### Weekly
- Update system: `apt update && apt upgrade -y`
- Prune unused images: `docker system prune -f`
- Backup reports: `./backup.sh`

### Monthly
- Review disk usage: `du -sh /opt/google-stats/`
- Verify SSL certificate: `certbot certificates`
- Archive old reports (90+ days): `find /opt/google-stats/reports -mtime +90 -delete`
- Update application: `git pull && docker-compose build && docker-compose up -d`

---

## 💰 Cost Control

### Optimize Costs

1. **Use Basic Droplet** ($5/month) - Sufficient for medium traffic
2. **Monitor Bandwidth** - 1TB/month included free
3. **Archive Reports** - Keep only recent reports on disk
4. **Free SSL** - Use Let's Encrypt (no cost)
5. **Free DNS** - Use Route 53 (minimal cost: $0.50/month)

### Cost Breakdown

```
DigitalOcean Droplet:    $5-12/month
  └─ Basic: $5 (1GB RAM, 1CPU, 25GB)
  └─ Standard: $12 (2GB RAM, 1CPU, 50GB)

AWS Route 53:            ~$0.50/month
  └─ $0.40 hosted zone
  └─ $0.40 per million queries

SSL Certificate:         FREE (Let's Encrypt)

Total:                   $5.50-12.50/month
```

---

## 📚 Full Documentation

For complete documentation including:
- Detailed troubleshooting
- Advanced configuration
- Performance tuning
- Scaling considerations
- Security hardening

See: `DEPLOYMENT_DIGITALOCEAN.md`

---

## 🤝 Support

### Getting Help

**Issue**: Deployment fails
**Solution**: Check `DEPLOYMENT_DIGITALOCEAN.md` → Troubleshooting section

**Issue**: DNS not resolving
**Solution**: Wait 10 minutes, check Route 53 A record, test with `nslookup`

**Issue**: SSL certificate errors
**Solution**: Run `certbot certonly` again, check certificate paths in nginx.conf

**Issue**: High memory usage
**Solution**: Check `docker stats`, reduce report processing, upgrade Droplet

---

## ✨ Next Steps

After successful deployment:

1. ✅ Access https://analytics.ndestates.com
2. ✅ Run test reports
3. ✅ Setup automated daily reports
4. ✅ Configure monitoring alerts
5. ✅ Document your configuration

---

**Happy deploying! 🚀**

For issues or questions, refer to the comprehensive guide in `DEPLOYMENT_DIGITALOCEAN.md`
