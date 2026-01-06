# AWS Route 53 DNS Configuration for Google Stats

**Complete Guide to Configuring Route 53 for analytics.ndestates.com**

---

## 📋 Prerequisites

- ✅ AWS Account with Route 53 access
- ✅ Domain `ndestates.com` already registered and configured in Route 53
- ✅ DigitalOcean Droplet IP address (e.g., 123.45.67.89)
- ✅ Admin access to AWS Console

---

## Step 1: Access Route 53 in AWS Console

1. **Sign in to AWS Console**
   - Go to https://console.aws.amazon.com/

2. **Navigate to Route 53**
   - Type "Route 53" in search bar
   - Click on "Route 53" service
   - OR: Services menu → Networking & Content Delivery → Route 53

3. **Select Hosted Zone**
   - Click "Hosted zones" in left sidebar
   - Find and click on `ndestates.com`

---

## Step 2: Create A Record for Subdomain

### Basic Configuration (Recommended)

1. **Click "Create Record"** button

2. **Fill in Record Details**
   ```
   Record name:        analytics
   Record type:        A
   Value:              123.45.67.89  (Your DigitalOcean Droplet IP)
   TTL:                300 (5 minutes)
   Routing policy:     Simple routing
   ```

3. **Click "Create records"**

### Full Record Details Table

| Field | Value | Notes |
|-------|-------|-------|
| **Record name** | `analytics` | Creates: analytics.ndestates.com |
| **Record type** | `A` | IPv4 address record |
| **Value** | Your Droplet IP | Without dashes or spaces |
| **TTL** | `300` | 5 minutes (fast updates) |
| **Routing** | Simple | Basic one-to-one mapping |

### Example: Multiple Values (Load Balancing - Advanced)

If you have multiple Droplets:

```
Record name:    analytics
Record type:    A
Values:
  - 123.45.67.89
  - 456.78.90.12
  - 789.01.23.45
TTL:            300
Routing:        Weighted (or Simple for round-robin)
```

---

## Step 3: Create www Subdomain Alias (Optional)

If you want `www.analytics.ndestates.com` to also work:

1. **Create CNAME Record**
   ```
   Record name:        www.analytics
   Record type:        CNAME
   Value:              analytics.ndestates.com
   TTL:                300
   Routing policy:     Simple routing
   ```

2. **Click "Create records"**

---

## Step 4: Create IPv6 Record (Optional but Recommended)

If your DigitalOcean Droplet has IPv6:

1. **Get IPv6 Address from DigitalOcean**
   - Log in to DigitalOcean console
   - Click your Droplet
   - Look for "IPv6" address (e.g., `2001:0db8:...`)

2. **Create AAAA Record**
   ```
   Record name:        analytics
   Record type:        AAAA
   Value:              Your IPv6 address
   TTL:                300
   Routing policy:     Simple routing
   ```

3. **Click "Create records"**

---

## Step 5: Verify DNS Configuration

### From Your Local Machine

```bash
# Test DNS resolution (using Google's nameserver)
nslookup analytics.ndestates.com 8.8.8.8

# Output should show:
# Server: 8.8.8.8
# Address: 8.8.8.8#53
# 
# Non-authoritative answer:
# Name: analytics.ndestates.com
# Address: 123.45.67.89

# Alternative: dig command
dig analytics.ndestates.com

# Should return your Droplet IP in the ANSWER SECTION
```

### From Your DigitalOcean Droplet

```bash
# SSH to your Droplet
ssh root@123.45.67.89

# Test DNS resolution
nslookup analytics.ndestates.com

# Should resolve to your Droplet's IP
```

### Test Specific Nameservers

```bash
# Query Route 53 nameservers directly
nslookup analytics.ndestates.com ns-123.awsdns-45.com

# Your Route 53 nameservers are shown in AWS Console:
# Click Hosted Zone → ndestates.com → NS record
# Look for values like:
# - ns-123.awsdns-45.com
# - ns-456.awsdns-78.org
# - etc.
```

---

## Step 6: Verify in AWS Console

1. **Check Record Status**
   - Hosted zones → ndestates.com
   - Look for new `analytics` record
   - Status should show checkmark (✓)

2. **View Record Details**
   - Click on the analytics record
   - Verify:
     - Name: `analytics.ndestates.com`
     - Type: `A`
     - Value: Your Droplet IP
     - TTL: `300`

---

## DNS Propagation Timing

| Stage | Time | What's Happening |
|-------|------|-----------------|
| Record created | Immediate | Added to Route 53 |
| AWS nameservers updated | < 1 minute | Propagated to AWS DNS |
| ISP caches updated | 5-10 minutes | Most users can resolve |
| Global cache updated | 15-30 minutes | Everyone can resolve |
| TTL expires | 300 seconds (5 min) | Cache refreshes with new IP |

**⏰ Tip**: Test after 10 minutes. If still not resolving, check your ISP's DNS cache with `ipconfig /flushdns` (Windows) or `sudo dscacheutil -flushcache` (Mac).

---

## Step 7: Advanced Configuration (Optional)

### Add Health Check

Monitor if your Droplet is up:

1. **Create Health Check**
   - Route 53 → Health checks → Create health check
   - Settings:
     ```
     Endpoint:           https://analytics.ndestates.com
     Port:               443
     Path:               /health
     Protocol:           HTTPS
     Interval:           30 seconds
     Failure threshold:  3 consecutive failures
     ```

2. **Link to Record** (for failover)
   - Edit analytics record
   - Enable "Evaluate target health"
   - Link to health check

### Configure Failover (High Availability)

If you have multiple Droplets:

1. **Create Primary Record**
   ```
   Name:               analytics
   Type:               A
   Value:              123.45.67.89 (Primary Droplet)
   Routing:            Failover
   Failover:           Primary
   Health check:       Associated health check
   ```

2. **Create Secondary Record**
   ```
   Name:               analytics
   Type:               A
   Value:              456.78.90.12 (Backup Droplet)
   Routing:            Failover
   Failover:           Secondary
   ```

3. **How It Works**
   - Primary Droplet serves traffic
   - If health check fails, Route 53 automatically switches to secondary
   - Ideal for 24/7 availability

### Add Weighted Routing (Load Balancing)

Distribute traffic among multiple Droplets:

```
Record 1:
  Name:       analytics
  Type:       A
  Value:      123.45.67.89
  Routing:    Weighted
  Weight:     50
  
Record 2:
  Name:       analytics
  Type:       A
  Value:      456.78.90.12
  Routing:    Weighted
  Weight:     50
```

Requests are distributed: 50% to Droplet 1, 50% to Droplet 2.

---

## Step 8: Enable DNSSEC (Security - Optional)

Prevent DNS spoofing attacks:

1. **Click Hosted Zone**
   - ndestates.com

2. **Click "DNSSEC signing"** button
   - Check "Enable signing"

3. **Create KSK** (Key Signing Key)
   - Click "Create KSK"
   - Accept defaults
   - Wait for status to show "Active"

4. **Create ZSK** (Zone Signing Key)
   - Click "Create ZSK"
   - Wait for status to show "Active"

**Note**: DNSSEC adds extra security but may have a small performance impact.

---

## Step 9: Setup Query Logging (Monitoring - Optional)

Monitor DNS queries for troubleshooting:

1. **Enable Query Logging**
   - Hosted zone → ndestates.com
   - Click "Query logging"
   - Click "Create query logging config"

2. **CloudWatch Settings**
   ```
   CloudWatch Logs group: /aws/route53/ndestates.com
   Region: us-east-1 (or your region)
   ```

3. **View Logs**
   - CloudWatch → Logs → Log groups
   - /aws/route53/ndestates.com
   - View log stream for analytics subdomain

**Sample Query Log Entry**
```
{
  "version": "1.0",
  "account_id": "123456789012",
  "region": "us-east-1",
  "vpc_id": "vpc-12345678",
  "query_timestamp": "2025-01-01T12:00:00Z",
  "query_name": "analytics.ndestates.com",
  "query_type": "A",
  "query_class": "IN",
  "response_code": "NOERROR",
  "query_count": 1
}
```

---

## Troubleshooting DNS Issues

### Issue 1: DNS Not Resolving

**Symptoms**: `nslookup analytics.ndestates.com` fails

**Solutions**:

```bash
# 1. Check if domain's nameservers point to Route 53
nslookup ndestates.com

# Should show Route 53 nameservers:
# ns-123.awsdns-45.com
# ns-456.awsdns-78.org
# (exact values in Route 53 console)

# 2. Query Route 53 nameservers directly
nslookup analytics.ndestates.com ns-123.awsdns-45.com

# 3. Check AWS Route 53 console
# - Hosted zones → ndestates.com
# - Verify NS record shows correct nameservers
# - Verify A record exists for 'analytics'

# 4. Wait for propagation
# DNS changes take 5-30 minutes globally
sleep 600  # Wait 10 minutes
nslookup analytics.ndestates.com

# 5. Flush local DNS cache
# Linux: systemctl restart systemd-resolved
# macOS: sudo dscacheutil -flushcache
# Windows: ipconfig /flushdns
```

### Issue 2: Resolves to Wrong IP

**Symptoms**: `nslookup` returns old or wrong IP

**Solutions**:

```bash
# 1. Verify TTL has expired
# TTL shown in nslookup results (default 300 seconds)
# Wait that many seconds before trying again

# 2. Check AWS Route 53
# - Click analytics record
# - Verify "Value" shows correct Droplet IP
# - If wrong, click "Edit" and update IP

# 3. Flush all caches
# Your machine DNS cache
sudo dscacheutil -flushcache  # macOS
ipconfig /flushdns  # Windows
sudo systemctl restart systemd-resolved  # Linux

# Router DNS cache (might need reboot)
# ISP DNS cache (contact ISP if issue persists)

# 4. Query nameservers directly
nslookup analytics.ndestates.com ns-123.awsdns-45.com
# Should show correct IP within TTL
```

### Issue 3: SERVFAIL or NODATA Response

**Symptoms**: `nslookup` returns SERVFAIL or empty response

**Solutions**:

```bash
# 1. Check record exists
dig analytics.ndestates.com

# Look for:
# ANSWER SECTION should have your A record
# If empty, record doesn't exist - create it

# 2. Check nameserver status
dig +trace analytics.ndestates.com

# Shows full resolution path through all nameservers
# Look for failures at each step

# 3. Verify authoritative nameservers
dig NS ndestates.com

# Should show Route 53 nameservers
# If shows registrar's nameservers, update registrar
# to point to Route 53 nameservers
```

### Issue 4: Inconsistent Results

**Symptoms**: Sometimes resolves, sometimes doesn't

**Solutions**:

```bash
# 1. Check all Route 53 nameservers
# From AWS Route 53 console, NS record shows:
# ns-123.awsdns-45.com
# ns-456.awsdns-78.org
# ns-789.awsdns-01.net
# ns-012.awsdns-34.com

# Test each:
for ns in ns-123.awsdns-45.com ns-456.awsdns-78.org; do
  echo "Testing $ns:"
  nslookup analytics.ndestates.com $ns
done

# All should return same IP

# 2. Check record doesn't have conflicting values
# AWS Route 53 console → analytics record
# Should have ONE primary record
# (Can have multiple with Weighted/Failover routing)

# 3. Monitor with query logging
# CloudWatch → Logs → /aws/route53/ndestates.com
# Look for SERVFAIL responses
```

---

## Performance & Security Best Practices

### TTL Optimization

```
Stable IP:          TTL = 3600 (1 hour)
Dynamic IP:         TTL = 300 (5 minutes)
During migration:   TTL = 60 (1 minute) before change
```

### Security

- ✅ Enable DNSSEC signing (prevents spoofing)
- ✅ Use Route 53 health checks (automatic failover)
- ✅ Monitor query logs (CloudWatch)
- ✅ Restrict Route 53 API access (IAM policies)

### Monitoring

```bash
# Alert when:
# - Health check fails (email notification)
# - Query count exceeds threshold
# - NXDOMAIN (domain doesn't exist) errors spike
# - SERVFAIL errors increase

# Configure CloudWatch alarms:
# CloudWatch → Alarms → Create alarm
# Metric: HealthCheckStatus
# Condition: Fails 3 consecutive checks
# Action: Send SNS notification
```

---

## Example: Complete Multi-Region Setup

For enterprise deployment with global distribution:

```
Primary Region (US-East):
  Droplet IP: 123.45.67.89
  Health Check: https://analytics.ndestates.com/health

Secondary Region (EU):
  Droplet IP: 456.78.90.12
  Health Check: https://analytics-eu.ndestates.com/health

Route 53 Configuration:
  
  Record 1 (analytics - Primary):
    Type: A
    Value: 123.45.67.89
    Routing: Failover
    Failover: Primary
    Health Check: US health check
  
  Record 2 (analytics - Secondary):
    Type: A
    Value: 456.78.90.12
    Routing: Failover
    Failover: Secondary
    Health Check: EU health check

Behavior:
  - Requests go to 123.45.67.89 (primary)
  - If health check fails, Route 53 switches to 456.78.90.12
  - Automatic failover in <60 seconds
  - No manual intervention needed
```

---

## Common Mistakes to Avoid

| Mistake | Impact | Fix |
|---------|--------|-----|
| Forgot to update registrar nameservers | Domain doesn't work | Update registrar to point to Route 53 nameservers |
| Wrong IP address in A record | Traffic goes to wrong server | Edit record, update IP |
| TTL too high (3600+) | Changes take hours to propagate | Set to 300 for frequent changes |
| No health checks | No automatic failover | Add health checks to records |
| DNSSEC not configured | Vulnerable to DNS spoofing | Enable DNSSEC signing |
| No query logging | Can't troubleshoot DNS issues | Enable CloudWatch query logging |

---

## Final Verification

Run this checklist after configuration:

```bash
# 1. DNS resolves correctly
nslookup analytics.ndestates.com
# ✓ Returns your Droplet IP

# 2. HTTPS works
curl -I https://analytics.ndestates.com
# ✓ Returns 200 OK with valid SSL certificate

# 3. Health check works (if configured)
curl https://analytics.ndestates.com/health
# ✓ Returns 200 OK

# 4. Propagation complete
dig analytics.ndestates.com @1.1.1.1
# ✓ Returns A record with your IP

# 5. Nameservers match Route 53
dig NS ndestates.com
# ✓ Shows Route 53 nameservers
```

---

## Cost Optimization

| Item | Cost | Notes |
|------|------|-------|
| Route 53 Hosted Zone | $0.40/month | Per domain |
| Route 53 Queries | $0.40 per million | ~1 million per week typical |
| Health Checks | $0.50/month each | Optional, recommended |
| DNSSEC | Free | Included with hosted zone |
| Query Logging | $0.50/month | Optional monitoring |

**Typical Total**: $0.50-1.50/month for Route 53

---

## References

- **AWS Route 53 Documentation**: https://docs.aws.amazon.com/route53/
- **Route 53 Pricing**: https://aws.amazon.com/route53/pricing/
- **DNS Best Practices**: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices.html
- **Route 53 Health Checks**: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-intro.html

---

**Configuration Complete!**  
Your subdomain `analytics.ndestates.com` is now managed by Route 53 and ready for deployment.
