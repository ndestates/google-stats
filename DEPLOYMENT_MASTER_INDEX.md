# DigitalOcean Deployment - Master Index & Quick Reference

**Complete Guide Index for Google Stats Deployment**

---

## 📚 Documentation Files

| File | Purpose | Time | Audience |
|------|---------|------|----------|
| **DEPLOYMENT_DIGITALOCEAN_QUICK_START.md** | 5-step quick deployment guide | 30-45 min | Everyone - Start here! |
| **DEPLOYMENT_DIGITALOCEAN.md** | Comprehensive deployment guide with all details | 2-3 hours | Detailed reference |
| **ROUTE53_DNS_SETUP.md** | AWS Route 53 DNS configuration | 30 min | DNS administrators |
| **FIREWALL_SECURITY_SETUP.md** | Firewall & security configuration | 45 min | System administrators |
| **deploy-digitalocean.sh** | Automated setup script | 5 min | Automation |

---

## 🎯 Recommended Reading Order

### For First-Time Deployment

```
1. DEPLOYMENT_DIGITALOCEAN_QUICK_START.md (15 min)
   ├─ Understand the process
   └─ Gather prerequisites
   
2. Create DigitalOcean Droplet (5 min)
   └─ Record IP address
   
3. Run deploy-digitalocean.sh (5 min)
   └─ Automated server setup
   
4. ROUTE53_DNS_SETUP.md (20 min)
   ├─ Create DNS records
   └─ Verify resolution
   
5. FIREWALL_SECURITY_SETUP.md (20 min)
   ├─ Create firewall rules
   └─ Secure SSH access
   
6. DEPLOYMENT_DIGITALOCEAN.md (reference)
   └─ Detailed info when needed

Total Time: ~45 minutes for basic setup
```

### For Advanced Configuration

```
1. DEPLOYMENT_DIGITALOCEAN.md
   ├─ SSL/TLS setup details
   ├─ Performance tuning
   ├─ Scaling strategies
   └─ Troubleshooting
   
2. FIREWALL_SECURITY_SETUP.md
   ├─ DDoS protection
   ├─ Rate limiting
   └─ Monitoring setup
   
3. ROUTE53_DNS_SETUP.md
   ├─ Advanced routing
   ├─ Health checks
   └─ Failover configuration
```

---

## 🚀 Quick Commands Reference

### Initial Setup

```bash
# SSH to your Droplet (replace IP)
ssh root@123.45.67.89

# Run automated setup
bash /opt/google-stats/deploy-digitalocean.sh
```

### Deployment

```bash
# Configure credentials
scp google-stats.env root@123.45.67.89:/opt/google-stats/.env

# Copy API keys
scp keys/*.json root@123.45.67.89:/opt/google-stats/keys/

# Start application
ssh root@123.45.67.89
cd /opt/google-stats
docker-compose -f docker-compose.prod.yml up -d
```

### Monitoring

```bash
# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Monitor resources
docker stats

# System health
df -h
free -h
```

### Maintenance

```bash
# Deploy updates
./deploy.sh

# Backup data
./backup.sh

# Monitor system
./monitor.sh

# Renew certificate
certbot renew
```

---

## 📋 Deployment Checklist

### Pre-Deployment (Before Creating Droplet)

- [ ] DigitalOcean account created
- [ ] Google API credentials prepared (see README_Google_Ads_Credentials.md)
- [ ] AWS Route 53 access verified
- [ ] SSH key pair generated
- [ ] Subdomain decision made (recommended: `analytics.ndestates.com`)
- [ ] Read DEPLOYMENT_DIGITALOCEAN_QUICK_START.md

### Droplet Creation

- [ ] Create Ubuntu 22.04 LTS Droplet
- [ ] Size: Basic ($6/month) or Standard ($12/month)
- [ ] Record Droplet IP address: `__________`
- [ ] Enable backups (optional, $1/month)
- [ ] Note hostname: `__________`

### Server Setup

- [ ] Run deploy-digitalocean.sh
- [ ] Verify Docker installation: `docker --version`
- [ ] Verify Docker Compose installation: `docker-compose --version`
- [ ] Application directory created: `/opt/google-stats`

### Configuration

- [ ] Copy .env.template → .env
- [ ] Fill in Google API credentials
- [ ] Verify all required values in .env
- [ ] Copy Google API key files to /opt/google-stats/keys/
- [ ] Set correct file permissions: `chmod 600 .env`

### DNS Setup (Route 53)

- [ ] Log in to AWS Route 53 console
- [ ] Create A record: `analytics` → Your Droplet IP
- [ ] Verify DNS resolution: `nslookup analytics.ndestates.com`
- [ ] Wait for propagation (5-10 minutes)
- [ ] Test DNS from Droplet: `nslookup analytics.ndestates.com`

### SSL Certificate

- [ ] Request certificate: `certbot certonly --dns-route53 -d analytics.ndestates.com`
- [ ] Verify certificate created: `ls -la /opt/google-stats/ssl/live/`
- [ ] Update nginx.conf with correct certificate path
- [ ] Build Docker image: `docker-compose build`

### Firewall (DigitalOcean)

- [ ] Create firewall: `google-stats-firewall`
- [ ] Add inbound rule: TCP 80 (HTTP)
- [ ] Add inbound rule: TCP 443 (HTTPS)
- [ ] Add inbound rule: TCP 22 (SSH from your IP)
- [ ] Configure outbound rules (allow all)
- [ ] Apply firewall to Droplet
- [ ] Verify firewall status: Active

### Firewall (Server-Level)

- [ ] SSH to Droplet
- [ ] Enable UFW: `ufw enable`
- [ ] Allow SSH: `ufw allow 22/tcp`
- [ ] Allow HTTP: `ufw allow 80/tcp`
- [ ] Allow HTTPS: `ufw allow 443/tcp`
- [ ] Verify rules: `ufw status verbose`

### Security Configuration

- [ ] Enable Route 53 DNSSEC signing
- [ ] Configure Route 53 query logging
- [ ] Create CloudWatch alarms
- [ ] Review security headers in nginx.conf
- [ ] Test rate limiting

### Application Deployment

- [ ] Start Docker containers: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Verify containers running: `docker-compose ps`
- [ ] Check application logs: `docker-compose logs web`
- [ ] Test health endpoint: `curl https://analytics.ndestates.com/health`

### Post-Deployment

- [ ] Access https://analytics.ndestates.com
- [ ] Verify SSL certificate (green lock)
- [ ] Run test report: `docker-compose exec web python3 scripts/yesterday_report.py`
- [ ] Check generated reports: `ls -la /opt/google-stats/reports/`
- [ ] Verify file permissions: `ls -la /opt/google-stats/`

### Final Verification

- [ ] Application accessible: https://analytics.ndestates.com ✓
- [ ] HTTPS working with valid certificate ✓
- [ ] DNS resolving correctly ✓
- [ ] Reports generating successfully ✓
- [ ] Firewall blocking unauthorized access ✓
- [ ] Rate limiting active ✓
- [ ] Backups configured ✓
- [ ] Monitoring alerts set up ✓

---

## 🆘 Quick Troubleshooting

### Problem: DNS Not Resolving

```bash
# Check DNS from local machine
nslookup analytics.ndestates.com 8.8.8.8

# If fails:
# 1. Wait 10 minutes (propagation time)
# 2. Check Route 53 A record: analytics → Your IP
# 3. Verify nameservers: dig NS ndestates.com
# 4. Flush cache: sudo dscacheutil -flushcache (Mac)

# See detailed help: ROUTE53_DNS_SETUP.md → Troubleshooting
```

### Problem: HTTPS Not Working

```bash
# Check certificate file
ls -la /opt/google-stats/ssl/live/analytics.ndestates.com/

# If missing:
certbot certonly --dns-route53 -d analytics.ndestates.com \
  --config-dir /opt/google-stats/ssl/live

# Verify Nginx config
docker-compose -f docker-compose.prod.yml exec -T nginx nginx -t

# Restart Nginx
docker-compose -f docker-compose.prod.yml restart nginx

# See detailed help: DEPLOYMENT_DIGITALOCEAN.md → Troubleshooting
```

### Problem: Containers Not Starting

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Check .env file exists
ls -la /opt/google-stats/.env

# Rebuild containers
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# See detailed help: DEPLOYMENT_DIGITALOCEAN.md → Troubleshooting
```

### Problem: Can't SSH to Droplet

```bash
# Check firewall rules
ufw status verbose

# Allow SSH
ufw allow 22/tcp

# Or if you changed SSH port:
ufw allow 2222/tcp

# Restart SSH service
systemctl restart sshd

# For DigitalOcean Console access:
# 1. Log in to DigitalOcean console
# 2. Click Droplet
# 3. Click "Console" button to access via web
```

---

## 📊 System Requirements Verification

### Minimum Requirements

```bash
# Check CPU
cat /proc/cpuinfo | grep processor | wc -l
# Should be: 1+

# Check RAM
free -h
# Should be: 1GB+

# Check Disk Space
df -h /opt/google-stats/
# Should be: 25GB+ available
```

### Recommended Specifications

```
CPU:        1-2 cores
RAM:        2GB (more for heavy analytics)
Disk:       50GB+ (for reports history)
Bandwidth:  1TB/month (plenty for typical use)
Region:     Closest to your location
```

---

## 💰 Cost Summary

### Monthly Costs

```
DigitalOcean Droplet:
  ├─ Basic ($5/month):    1GB RAM, 1CPU, 25GB SSD
  ├─ Standard ($12/month): 2GB RAM, 1CPU, 50GB SSD
  └─ Premium ($24/month):  4GB RAM, 2CPU, 100GB SSD

Optional Add-ons:
  ├─ Backups: $1-2/month (20% of droplet cost)
  ├─ Data Transfer: Free (1TB/month included)
  └─ Monitoring: Free with DigitalOcean

AWS Route 53:
  ├─ Hosted Zone: $0.40/month
  ├─ Queries: ~$0.40/month (1M queries/month typical)
  ├─ Health Checks: $0.50/month each (optional)
  └─ Query Logging: $0.50/month (optional)

SSL Certificate: FREE (Let's Encrypt)

TOTAL: $5.50-13/month
```

### Cost Optimization

- Use Basic Droplet for typical traffic
- Archive old reports to reduce storage
- Keep TTL at 300 (cache efficiency)
- Monitor bandwidth usage monthly
- Use free monitoring (no premium add-ons needed)

---

## 🔄 Maintenance Schedule

### Daily
- Monitor container status
- Check for errors in logs

### Weekly
- Update system packages: `apt update && apt upgrade`
- Prune old Docker images: `docker system prune -f`
- Review firewall logs

### Monthly
- Full backup: `./backup.sh`
- Verify SSL certificate: `certbot certificates`
- Archive reports 90+ days old
- Update application: `git pull && docker-compose build`
- Review cost analysis

### Quarterly
- Disaster recovery test
- Security audit
- Capacity planning review

### Annually
- Security certification renewal
- Compliance audit
- Major version updates

---

## 📞 Getting Support

### Resources

| Issue | Resource |
|-------|----------|
| DigitalOcean | https://www.digitalocean.com/help |
| AWS Route 53 | https://docs.aws.amazon.com/route53/ |
| Docker | https://docs.docker.com/ |
| Nginx | https://nginx.org/en/docs/ |
| Let's Encrypt | https://letsencrypt.org/support/ |

### Documentation Files

All issues should be solvable by referring to:
- **DNS Issues**: ROUTE53_DNS_SETUP.md → Troubleshooting
- **Firewall Issues**: FIREWALL_SECURITY_SETUP.md → Troubleshooting
- **Deployment Issues**: DEPLOYMENT_DIGITALOCEAN.md → Troubleshooting
- **General Issues**: DEPLOYMENT_DIGITALOCEAN_QUICK_START.md → Troubleshooting

---

## ✅ Deployment Success Criteria

Your deployment is successful when:

1. ✅ Application accessible at https://analytics.ndestates.com
2. ✅ Valid SSL certificate (green lock in browser)
3. ✅ DNS resolving correctly
4. ✅ All reports generating without errors
5. ✅ Firewall protecting the server
6. ✅ Rate limiting preventing abuse
7. ✅ Automated backups running
8. ✅ Monitoring alerts configured
9. ✅ All containers healthy

---

## 🎉 Congratulations!

You now have a production-ready Google Stats deployment on DigitalOcean with:

- ✨ Professional analytics platform
- 🔒 Enterprise-grade security
- 🚀 Fast CDN-like performance
- 💰 Cost-effective infrastructure ($6-15/month)
- 📊 Real-time analytics and reporting
- 🔄 Automated backups and monitoring
- 📈 Scalable architecture for future growth

### Next Steps

1. Share access with your team
2. Configure automated reports
3. Setup alerts for important metrics
4. Monitor performance metrics
5. Plan quarterly reviews

---

**Documentation Version**: 1.0.0  
**Last Updated**: January 2026  
**Status**: Production Ready ✅

For updates or corrections, refer to the individual guide files.
