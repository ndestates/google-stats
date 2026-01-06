# Firewall & Security Configuration for Google Stats

**Complete Guide to Firewall Setup for DigitalOcean + AWS Route 53**

---

## 📋 Architecture Overview

```
Internet Users
    ↓
AWS Route 53 (DNS)
    ↓
[DigitalOcean Firewall] ← Filters traffic
    ↓
DigitalOcean Droplet
    ├─ Nginx (Port 443/80)
    ├─ Flask App (Port 5000 - internal only)
    └─ Docker Containers
```

---

## Part 1: DigitalOcean Firewall Setup

### Step 1: Create Firewall via DigitalOcean Console

1. **Log in to DigitalOcean Console**
   - https://cloud.digitalocean.com/

2. **Navigate to Networking → Firewalls**
   - Click "Firewalls" in left sidebar
   - Click "Create Firewall"

3. **Configure Basic Settings**
   ```
   Name:               google-stats-firewall
   Description:        Firewall for Google Stats analytics platform
   ```

### Step 2: Configure Inbound Rules

1. **Add HTTP Rule** (for Let's Encrypt validation and redirect)
   ```
   Protocol:           TCP
   Port:               80
   Sources:
     Type:             Anywhere
     Value:            0.0.0.0/0 (all IPv4)
   
   Add second source for IPv6:
     Type:             Anywhere
     Value:            ::/0 (all IPv6)
   ```

2. **Add HTTPS Rule** (main traffic)
   ```
   Protocol:           TCP
   Port:               443
   Sources:
     Type:             Anywhere
     Value:            0.0.0.0/0 (all IPv4)
   
   Add second source for IPv6:
     Type:             Anywhere
     Value:            ::/0 (all IPv6)
   ```

3. **Add SSH Rule** (YOUR IP ONLY - CRITICAL FOR SECURITY)
   ```
   Protocol:           TCP
   Port:               22
   Sources:
     Type:             IP Address
     Value:            YOUR_HOME_IP (e.g., 192.0.2.50)
   
   Replace YOUR_HOME_IP with:
   - Your home internet IP
   - Your office/VPN IP
   - Only IPs you'll use to SSH
   
   Get your IP:
     - Linux/Mac: curl -s https://api.ipify.org
     - Windows: Open PowerShell, run: (Invoke-WebRequest -Uri "https://api.ipify.org").Content
   ```

4. **Review Inbound Rules**

   | Protocol | Port | Source | Purpose |
   |----------|------|--------|---------|
   | TCP | 80 | 0.0.0.0/0, ::/0 | HTTP redirect to HTTPS |
   | TCP | 443 | 0.0.0.0/0, ::/0 | HTTPS traffic (main) |
   | TCP | 22 | YOUR_IP only | SSH admin access |

### Step 3: Configure Outbound Rules

By default, DigitalOcean allows all outbound traffic. Keep this for API calls:

```
Protocol:           TCP
Destination:        Anywhere (0.0.0.0/0, ::/0)
Purpose:            API calls to Google, AWS, etc.

Protocol:           UDP
Destination:        Anywhere (0.0.0.0/0, ::/0)
Purpose:            DNS queries, NTP time sync
```

**⚠️ If you want to restrict outbound (advanced):**

```
Allow Outbound To:
├─ TCP 53 (DNS to 8.8.8.8, 1.1.1.1)
├─ UDP 53 (DNS to 8.8.8.8, 1.1.1.1)
├─ TCP 443 (HTTPS to Google APIs, AWS, etc.)
├─ TCP 123 (NTP time sync)
└─ UDP 123 (NTP time sync)
```

### Step 4: Apply Firewall to Droplet

1. **In Firewall Creation Form**
   - Scroll to "Droplets" section
   - Search for your Droplet (e.g., "analytics-do")
   - Select your Droplet

2. **Create Firewall**
   - Click "Create Firewall"
   - Wait for status to show "Active"

3. **Verify Application**
   - Go to your Droplet page
   - You should see firewall listed under "Firewalls"

---

## Part 2: Server-Level Firewall (UFW)

For additional protection, configure UFW (Ubuntu Firewall) on the Droplet:

### Step 1: SSH to Your Droplet

```bash
ssh -i /path/to/ssh/key root@123.45.67.89
```

### Step 2: Configure UFW Rules

```bash
# Enable UFW
ufw enable

# Default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (CRITICAL - do this first!)
ufw allow 22/tcp

# Allow HTTP
ufw allow 80/tcp

# Allow HTTPS
ufw allow 443/tcp

# View rules
ufw status verbose

# Output should show:
# Status: active
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere
# 80/tcp                     ALLOW       Anywhere
# 443/tcp                    ALLOW       Anywhere
# 22/tcp (v6)                ALLOW       Anywhere (v6)
# 80/tcp (v6)                ALLOW       Anywhere (v6)
# 443/tcp (v6)               ALLOW       Anywhere (v6)
```

### Step 3: Optional - Restrict SSH to Your IP

For extra security, limit SSH to your IP only:

```bash
# Remove general SSH rule
ufw delete allow 22/tcp

# Add SSH from your IP only
ufw allow from 192.0.2.50 to any port 22

# Verify
ufw status verbose

# When you need to SSH from different IP:
# 1. Use VPN to consistent IP
# 2. Or temporarily: ufw allow from NEW_IP to any port 22
# 3. Or use AWS Systems Manager Session Manager (no SSH needed)
```

### Step 4: Rate Limiting

Prevent brute force attacks:

```bash
# Limit SSH attempts
ufw limit 22/tcp

# Limit HTTP/HTTPS (after rate limiting in Nginx)
ufw limit 80/tcp
ufw limit 443/tcp

# View updated rules
ufw status verbose
```

---

## Part 3: AWS Route 53 Security

### Security Best Practices for Route 53

#### 1. Enable DNSSEC

Prevent DNS spoofing/poisoning:

```bash
# AWS Console → Route 53 → Hosted Zones → ndestates.com

# Enable DNSSEC Signing:
1. Click "DNSSEC signing" button
2. Click "Enable signing"
3. Create KSK (Key Signing Key)
   - Click "Create KSK"
   - Select algorithm: ECDSAP256SHA256 (recommended)
   - Click "Create"
4. Create ZSK (Zone Signing Key)
   - Click "Create ZSK"
   - Select algorithm: ECDSAP256SHA256
   - Click "Create"
5. Wait for both to show "Active" status (1-2 minutes)
```

**Verification:**
```bash
# Check DNSSEC is active
dig +dnssec analytics.ndestates.com

# Output includes:
# ;; flags: qr rd ra ad;
# "ad" flag indicates DNSSEC validated
```

#### 2. Setup IAM Policies

Restrict who can modify DNS records:

```bash
# AWS Console → IAM → Policies → Create Policy

# JSON Policy (least privilege):
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "route53:ListHostedZones",
        "route53:GetHostedZone"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "route53:ListResourceRecordSets",
        "route53:GetChange"
      ],
      "Resource": [
        "arn:aws:route53:::hostedzone/Z123456789ABC",
        "arn:aws:route53:::change/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "route53:ChangeResourceRecordSets"
      ],
      "Resource": "arn:aws:route53:::hostedzone/Z123456789ABC",
      "Condition": {
        "StringEquals": {
          "route53:ChangeResourceRecordSetsNormalizedRecordNames": [
            "analytics.ndestates.com"
          ]
        }
      }
    }
  ]
}
```

**Note**: Get hosted zone ID from:
- Route 53 console → Hosted Zones → ndestates.com
- Copy ID (looks like: Z123456789ABC)

#### 3. Enable Query Logging

Monitor DNS activity for security events:

```bash
# AWS Console → Route 53 → Hosted Zones → ndestates.com

# Create Query Log Config:
1. Click "Query logging" button
2. Click "Create query logging config"
3. CloudWatch Settings:
   - Log group name: /aws/route53/ndestates.com
   - Region: select your region
4. Click "Create query logging config"

# View logs:
# AWS Console → CloudWatch → Log Groups
# → /aws/route53/ndestates.com
# → Select log stream to view queries
```

**Analyze Suspicious Activity:**
```bash
# Using AWS CLI
aws logs filter-log-events \
  --log-group-name "/aws/route53/ndestates.com" \
  --query "events[?contains(message, 'SERVFAIL')]"

# Query response codes:
# NOERROR   - Success
# NXDOMAIN  - Domain doesn't exist (potential probe)
# SERVFAIL  - Server error
# REFUSED   - Query refused (blocked)
```

#### 4. Setup Alarms

Alert on suspicious DNS activity:

```bash
# AWS Console → CloudWatch → Alarms → Create alarm

# Alert for failed queries:
Metric:               DNSQueries
Statistic:            Sum
Period:               5 minutes
Threshold:            Anomaly detection
Comparison:           Greater than
Alarm actions:        SNS topic → Email notification

# Alert for excessive queries:
Metric:               DNSQueries
Statistic:            Sum
Period:               1 minute
Threshold:            > 1000 queries
Action:               Email admin
```

---

## Part 4: Application-Level Security (Nginx)

### Rate Limiting Configuration

Already included in `nginx.conf`:

```nginx
# Rate limiting zones (from nginx.conf)
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

# Applied to endpoints:
location / {
    limit_req zone=general burst=20 nodelay;
    proxy_pass http://web:5000;
}

location /api/ {
    limit_req zone=api burst=50 nodelay;
    proxy_pass http://web:5000;
}
```

**What This Does:**
- General: 10 requests/second, burst to 20
- API: 30 requests/second, burst to 50
- Excess requests: 429 Too Many Requests response
- Per-IP limiting: Each IP has separate limit

### Security Headers (Already Configured)

```nginx
# Prevent MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# XSS protection
add_header X-XSS-Protection "1; mode=block" always;

# HSTS - Force HTTPS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions Policy
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

### SSL/TLS Configuration

```nginx
# TLS versions (strong security)
ssl_protocols TLSv1.2 TLSv1.3;

# Strong ciphers only
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';

# Prefer server ciphers
ssl_prefer_server_ciphers on;

# Session configuration
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# OCSP stapling (certificate status verification)
ssl_stapling on;
ssl_stapling_verify on;
```

---

## Part 5: DDoS Protection

### DigitalOcean DDoS Protection

DigitalOcean provides basic DDoS protection for all customers.

For enhanced protection:

```bash
# Option 1: Use Cloudflare (recommended, free tier available)
# 1. Create Cloudflare account: https://www.cloudflare.com/
# 2. Add domain: ndestates.com
# 3. Change nameservers at registrar to Cloudflare's
# 4. Setup analytics.ndestates.com CNAME to Droplet IP
# 5. Benefits:
#    - DDoS protection
#    - WAF (Web Application Firewall)
#    - Rate limiting
#    - Caching
#    - Free SSL upgrade

# Option 2: Use AWS Shield Standard (included)
# Already active for Route 53

# Option 3: Upgrade to AWS Shield Advanced
# AWS Console → AWS Shield → Subscribe to Shield Advanced
# Cost: $3,000/month but includes:
# - Advanced DDoS protection
# - DDoS cost protection
# - 24/7 support
```

### Application-Level DDoS Prevention

Already configured in nginx.conf:

```nginx
# 1. Rate limiting (see above)
# 2. Connection limiting
limit_conn_zone $binary_remote_addr zone=addr:10m;
limit_conn addr 10;

# 3. Request size limiting
client_max_body_size 50M;

# 4. Timeouts (prevent slowloris attacks)
client_body_timeout 10s;
client_header_timeout 10s;
send_timeout 10s;
```

---

## Part 6: Monitoring & Alerts

### Setup Monitoring Alerts

```bash
# SSH to Droplet
ssh root@123.45.67.89

# 1. Install monitoring
apt install -y nagios-plugins-standard

# 2. Check system resources
check_disk -w 80 -c 90 /opt/google-stats
check_load -w 4,4,4 -c 6,6,6
check_procs -w 200 -c 250

# 3. Log important events
tail -f /var/log/syslog | grep -i "error\|fail\|denied"
docker-compose -f /opt/google-stats/docker-compose.prod.yml logs -f
```

### Setup CloudWatch Alarms (AWS)

```bash
# Monitor Route 53 Health Check
AWS Console → CloudWatch → Alarms → Create Alarm

Metric:     HealthCheckStatus
Condition:  3 consecutive failures
Action:     SNS notification → Email admin

# Monitor Route 53 Query Patterns
Metric:     DNSQueries
Condition:  Spike or anomaly
Action:     SNS notification → Email admin
```

---

## Security Checklist

### Before Going Live

- [ ] DigitalOcean firewall created and applied to Droplet
- [ ] UFW enabled on Droplet with SSH restricted (if using IP restriction)
- [ ] Route 53 DNSSEC enabled
- [ ] Route 53 query logging configured
- [ ] IAM policies configured (least privilege)
- [ ] SSL certificate valid and renewed automatically
- [ ] Rate limiting enabled in Nginx
- [ ] Security headers configured in Nginx
- [ ] Health checks configured in Route 53
- [ ] CloudWatch alarms created
- [ ] Backup strategy implemented
- [ ] Log monitoring configured
- [ ] DDoS protection evaluated (Cloudflare recommended)

### Ongoing

- [ ] Review firewall rules monthly
- [ ] Monitor CloudWatch logs weekly
- [ ] Check SSL certificate expiration (automated via Certbot)
- [ ] Update system packages weekly
- [ ] Review and rotate credentials quarterly
- [ ] Test disaster recovery quarterly

---

## Common Security Issues & Fixes

### Issue 1: SSH Brute Force Attempts

**Symptoms**: Logs show many failed login attempts

**Fix**:
```bash
# Review failed attempts
grep "Failed password" /var/log/auth.log | tail -20

# Option 1: Use key-only authentication (already recommended)
# Option 2: Change SSH port
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart sshd

# Update firewall:
ufw delete allow 22/tcp
ufw allow 2222/tcp

# Option 3: Use fail2ban
apt install -y fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

### Issue 2: High HTTP Traffic (DDoS Probe)

**Symptoms**: HTTP logs show spikes from single IPs

**Fix**:
```bash
# View suspicious IPs
tail -1000 /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn | head -20

# Block IP in firewall (temporarily)
ufw deny from 192.0.2.100

# Or block in Nginx:
echo "deny 192.0.2.100;" >> /etc/nginx/nginx.conf
nginx -t
systemctl reload nginx

# Use Cloudflare for DDoS protection (recommended)
```

### Issue 3: Certificate Issues

**Symptoms**: HTTPS not working or certificate expired

**Fix**:
```bash
# Check certificate
certbot certificates --config-dir /opt/google-stats/ssl/live

# Renew manually
certbot renew --force-renewal \
  --config-dir /opt/google-stats/ssl/live

# View renewal logs
cat /opt/google-stats/ssl/logs/letsencrypt.log

# Restart Nginx
docker-compose -f /opt/google-stats/docker-compose.prod.yml restart nginx
```

### Issue 4: API Rate Limit Errors

**Symptoms**: Google Analytics or Ads API returns quota exceeded

**Fix**:
```bash
# 1. Increase Nginx rate limits
# Edit nginx.conf:
limit_req_zone $binary_remote_addr zone=api:10m rate=50r/s;

# 2. Implement caching in application
# (See app.py for caching strategy)

# 3. Stagger report generation
# Don't run all reports simultaneously

# 4. Request quota increase in Google Cloud Console
# APIs & Services → Quotas → Select API → Edit → Request increase
```

---

## Security Testing

### Self-Assessment

```bash
# 1. Check DNS security
dig +dnssec analytics.ndestates.com

# 2. Test HTTPS
curl -I https://analytics.ndestates.com
# Should show TLS 1.3 and valid certificate

# 3. Check security headers
curl -I https://analytics.ndestates.com | grep -i "strict-transport\|x-content-type\|x-frame"

# 4. Test rate limiting
# (Should get 429 after exceeding limit)
for i in {1..100}; do curl -s https://analytics.ndestates.com > /dev/null; done

# 5. Port scanning (from external)
nmap -p 22,80,443 analytics.ndestates.com
# Should show: 22 filtered, 80 open, 443 open
```

### Third-Party Testing

- **SSL Labs**: https://www.ssllabs.com/ssltest/
- **Mozilla Observatory**: https://observatory.mozilla.org/
- **OWASP ZAP**: https://www.zaproxy.org/ (for penetration testing)

---

## Disaster Recovery

### Backup Strategy

```bash
# Daily backup script
#!/bin/bash
tar -czf /backups/google-stats-$(date +%Y%m%d).tar.gz \
  /opt/google-stats/reports/ \
  /opt/google-stats/.env \
  /opt/google-stats/ssl/live/

# Store backups:
# - Local: /backups/ (keep 30 days)
# - Remote: DigitalOcean Spaces or AWS S3
```

### Disaster Recovery Plan

```
1. Droplet Failure
   ├─ Alert triggered (health check fails)
   ├─ Manual intervention:
   │  ├─ Create new Droplet
   │  ├─ Run deploy-digitalocean.sh
   │  ├─ Restore from backup
   │  └─ Route 53 failover (or update A record)
   └─ Expected recovery time: 15 minutes

2. DNS Failure
   ├─ Failover to secondary Droplet (if configured)
   ├─ Manual: Update A record in Route 53
   └─ Recovery time: < 5 minutes (TTL dependent)

3. Data Loss
   ├─ Restore from daily backups
   ├─ Reports lost: regenerate
   └─ Recovery time: 30 minutes
```

---

## References

- **DigitalOcean Firewall**: https://docs.digitalocean.com/products/networking/firewalls/
- **AWS Route 53 Security**: https://docs.aws.amazon.com/route53/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cybersecurity/framework
- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **SSL Labs Best Practices**: https://github.com/ssllabs/research/wiki/SSL-and-TLS-Deployment-Best-Practices

---

**Security Configuration Complete!**  
Your Google Stats deployment is protected at multiple layers:
1. DigitalOcean Firewall
2. UFW (server-level)
3. Nginx (application-level)
4. Route 53 DNSSEC
5. Rate limiting & security headers

Regular monitoring and updates keep your system secure.
