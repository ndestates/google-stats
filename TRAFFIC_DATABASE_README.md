# Property Traffic Database - Complete Implementation

## Overview
Comprehensive traffic data system providing granular source/medium analytics for all properties. Stores individual traffic source combinations per property, allowing you to make informed decisions about which channels drive meaningful engagement.

## ✅ Implementation Complete

### Database Structure
**Table:** `property_traffic_detail`
- **Granularity:** One row per property + source/medium + date range combination
- **Unique Key:** (reference, report_date, period_days, traffic_source, traffic_medium)
- **Storage:** 1,360+ records for 40 properties (30-day period)

**Schema:**
```sql
reference VARCHAR(50)              -- Property reference (e.g., STH250129)
house_name VARCHAR(255)            -- Property name for display
property_url TEXT                  -- Full property URL
report_date DATE                   -- When this data was captured
period_days INT                    -- Data period (1, 7, 30, etc.)
traffic_source VARCHAR(100)        -- GA4 sessionSource (google, facebook, etc.)
traffic_medium VARCHAR(100)        -- GA4 sessionMedium (organic, cpc, email, etc.)
sessions INT                       -- Number of sessions
pageviews INT                      -- Total page views
users INT                          -- Unique users
avg_session_duration DECIMAL(10,2) -- Average time on site (seconds)
bounce_rate DECIMAL(5,4)          -- Bounce rate (0.0000 to 1.0000)
```

**Key Addition to Properties Table:**
```sql
is_active TINYINT DEFAULT 1       -- Track properties in/out of feed
```

### Available Scripts

#### 1. Feed Synchronization
**Script:** `scripts/sync_property_feed.py`
**Purpose:** Keep database in sync with property feed
**Feed URL:** `https://api.ndestates.com/feeds/ndefeed.xml`

```bash
# Dry run to preview changes
ddev exec python3 scripts/sync_property_feed.py --dry-run

# Apply sync
ddev exec python3 scripts/sync_property_feed.py
```

**What it does:**
- Fetches current property feed from API
- Compares feed properties with database
- Marks properties `is_active = 0` if not in feed
- Adds new properties from feed
- Reactivates properties that return to feed
- Updates changed property details (price, name, etc.)

**Last Run Results:**
- ✅ 40 properties in feed
- ✅ 40 properties in database
- 🔄 Updated 40 properties
- ⚠️ No inactive properties (all properties currently active)

#### 2. Populate Traffic Database
**Script:** `scripts/populate_traffic_database.py`
**Purpose:** Fetch GA4 data and store with source/medium granularity

```bash
# Populate last 30 days
ddev exec python3 scripts/populate_traffic_database.py --days 30

# Populate yesterday only
ddev exec python3 scripts/populate_traffic_database.py --days 1

# Available periods: 1, 7, 14, 30, 60, 90 days
```

**What it fetches:**
- Dimensions: `pagePath`, `sessionSource`, `sessionMedium` (separate!)
- Metrics: `sessions`, `screenPageViews`, `activeUsers`, `averageSessionDuration`, `bounceRate`
- Storage: Each source/medium combination = separate row

**Last Run Results:**
- ✅ 40 properties from database
- ✅ 641 unique pages analyzed
- ✅ 1,816 unique source/medium combinations
- 💾 1,360 new records inserted (30-day period)

#### 3. View Traffic Reports
**Script:** `scripts/view_traffic_report.py`
**Purpose:** Display raw traffic data WITHOUT performance judgments

```bash
# Compare all traffic sources
ddev exec python3 scripts/view_traffic_report.py --compare-sources

# View specific property
ddev exec python3 scripts/view_traffic_report.py --property STH250129

# Different time periods
ddev exec python3 scripts/view_traffic_report.py --days 7 --compare-sources

# Export to CSV
ddev exec python3 scripts/view_traffic_report.py --compare-sources --export-csv

# Sort by different metrics
ddev exec python3 scripts/view_traffic_report.py --compare-sources --sort-by pageviews
```

**Display Columns:**
- Source / Medium (e.g., "google / organic", "facebook / catalog")
- Properties (how many properties received traffic)
- Sessions (total visits)
- Pageviews (total page views)
- Users (unique visitors)
- Avg Duration (engagement time)
- Bounce Rate (% single-page sessions)

**Philosophy:** Presents FACTS ONLY. No "low performer" labels, no AI assumptions. YOU decide what's good or bad based on YOUR business goals.

## Sample Data Insights

### Top Traffic Sources (30-day period)
```
Source / Medium                    Properties   Sessions    Pageviews
------------------------------------------------ ---------- ----------
google / organic                           40      33,800      197,040
(direct) / (none)                          40      10,680       54,720
google / cpc                               40      10,200       63,200
facebook / catalog                         40       6,440       40,680
(not set) / (not set)                      40       4,240       19,440
bing / organic                             40       2,440       13,920
gov.je / referral                          40       2,360       10,200
```

### Individual Property Example (STH250129)
```
Source / Medium                    Sessions  Pageviews
------------------------------------------------ --------
google / organic                        845       4,926
(direct) / (none)                       267       1,368
google / cpc                            255       1,580
facebook / catalog                      161       1,017
(not set) / (not set)                   106         486
```

## Key Differentiators

### Source vs Medium Separation
**Old approach:** Combined "google/organic" as single dimension
**New approach:** Store `traffic_source` and `traffic_medium` separately
**Benefit:** More flexible querying and analysis

Example queries now possible:
```sql
-- All organic traffic regardless of source
SELECT * FROM property_traffic_detail WHERE traffic_medium = 'organic';

-- All Google traffic regardless of medium
SELECT * FROM property_traffic_detail WHERE traffic_source = 'google';

-- Facebook paid vs organic
SELECT * FROM property_traffic_detail 
WHERE traffic_source = 'facebook' AND traffic_medium IN ('catalog', 'fb_ads', 'paid');
```

### No Performance Assumptions
**Old system:** Categorized properties as "low performers" based on arbitrary thresholds
**New system:** Shows raw numbers, lets YOU decide what constitutes good performance

**Why this matters:**
- A luxury property with 50 sessions might be performing better than mass-market property with 500
- High bounce rate might be fine if users find what they need quickly
- Low session duration could mean efficient user experience, not poor engagement
- YOU understand your business goals, not the AI

### Granular Time Periods
Store multiple snapshots:
- **period_days = 1:** Yesterday's traffic (daily tracking)
- **period_days = 7:** Weekly trends
- **period_days = 30:** Monthly patterns
- **period_days = 90:** Quarterly analysis

Same property can have multiple rows for different time periods, enabling trend analysis.

## Integration with Existing Tools

### Enhanced Error Messages
**Script:** `scripts/viewing_requests_manager.py`
Now shows comprehensive troubleshooting when no conversion data exists:

```
⚠️ No conversion data available for last 30 days

TROUBLESHOOTING GUIDE:

1. Check if viewing requests exist:
   ddev exec python3 scripts/view_traffic_report.py --property STH250129

2. How to add a viewing request:
   ddev exec python3 scripts/add_viewing_request.py

3. Check if property analytics data exists:
   ddev exec python3 scripts/populate_traffic_database.py --days 30

4. Verify date ranges align...

5. Check database tables...
```

### Traffic Source Display
**Script:** `scripts/catalog_analytics_report.py`
Enhanced to show formatted traffic source tables:

```
TRAFFIC SOURCES:
Source / Medium                    Sessions    % of Total
------------------------------------------------ --------
google / organic                        845        41.5%
(direct) / (none)                       267        13.1%
google / cpc                            255        12.5%
facebook / catalog                      161         7.9%
```

### Web Interface Access
**Script:** `web/index.php`
Added Yesterday's Report card for easy access from dashboard.

## Maintenance & Operations

### Daily Routine
```bash
# Sync properties with feed (marks inactive properties)
ddev exec python3 scripts/sync_property_feed.py

# Populate yesterday's traffic
ddev exec python3 scripts/populate_traffic_database.py --days 1

# View yesterday's sources
ddev exec python3 scripts/view_traffic_report.py --days 1 --compare-sources
```

### Weekly Analysis
```bash
# Populate last 7 days
ddev exec python3 scripts/populate_traffic_database.py --days 7

# Compare sources over week
ddev exec python3 scripts/view_traffic_report.py --days 7 --compare-sources

# Export for deeper analysis
ddev exec python3 scripts/view_traffic_report.py --days 7 --compare-sources --export-csv
```

### Monthly Deep Dive
```bash
# Populate last 30 days
ddev exec python3 scripts/populate_traffic_database.py --days 30

# Analyze specific high-value properties
ddev exec python3 scripts/view_traffic_report.py --property STH250154
ddev exec python3 scripts/view_traffic_report.py --property STH250095

# Overall source comparison
ddev exec python3 scripts/view_traffic_report.py --days 30 --compare-sources --export-csv
```

### Data Retention
Database uses `ON DUPLICATE KEY UPDATE`, so:
- Running same period again updates existing records
- Different periods create new records
- Can store historical snapshots by keeping multiple `report_date` entries

Example: Running `--days 30` daily creates 30 separate snapshots, enabling trend analysis.

## Comparing Marketing Channels

### Mailchimp vs Facebook
```bash
# View all sources
ddev exec python3 scripts/view_traffic_report.py --compare-sources > traffic.txt

# Then search output:
grep -i mailchimp traffic.txt
grep -i facebook traffic.txt
```

**Sample comparison:**
```
mailchimp / email                           40         80          280
facebook / catalog                          40      6,440       40,680
facebook / fb_ads                           40         40          240
m.facebook.com / referral                   40        960        4,560
```

**Insights YOU can derive:**
- Facebook catalog (6,440 sessions) vastly outperforms direct Mailchimp (80 sessions)
- But check bounce rate and duration to see engagement quality
- Consider cost per session for each channel
- Track which properties get traffic from each source

### Organic vs Paid
```
google / organic                            40     33,800      197,040
google / cpc                                40     10,200       63,200
```

**Questions to answer:**
- Is paid traffic worth the cost? (10,200 sessions from PPC)
- Does organic traffic engage better? (Check duration/bounce rate)
- Which properties benefit most from paid vs organic?
- Are there properties getting zero organic traffic that need SEO work?

## Database Queries for Advanced Analysis

### Properties with no traffic from specific source
```sql
SELECT DISTINCT p.reference, p.house_name
FROM properties p
WHERE p.is_active = 1
  AND p.reference NOT IN (
    SELECT reference 
    FROM property_traffic_detail 
    WHERE traffic_source = 'facebook' 
      AND period_days = 30
  );
```

### Best performing source per property
```sql
SELECT reference, house_name, traffic_source, traffic_medium, sessions
FROM property_traffic_detail
WHERE period_days = 30
  AND (reference, sessions) IN (
    SELECT reference, MAX(sessions)
    FROM property_traffic_detail
    WHERE period_days = 30
    GROUP BY reference
  )
ORDER BY sessions DESC;
```

### Channel cost analysis
```sql
-- Combine with ad spend data to calculate cost per session
SELECT 
  traffic_source,
  traffic_medium,
  SUM(sessions) as total_sessions,
  SUM(users) as total_users,
  AVG(avg_session_duration) as avg_duration,
  AVG(bounce_rate) as avg_bounce
FROM property_traffic_detail
WHERE period_days = 30
  AND traffic_medium IN ('cpc', 'paid', 'email', 'catalog')
GROUP BY traffic_source, traffic_medium
ORDER BY total_sessions DESC;
```

### Properties missing from feed
```sql
SELECT reference, house_name, last_updated
FROM properties
WHERE is_active = 0
ORDER BY last_updated DESC;
```

## Future Enhancements

### Potential Additions
1. **Trend Analysis:** Compare same-period data across multiple months
2. **Alert System:** Notify when property traffic drops below historical average
3. **Cost Integration:** Track ad spend per source/medium for ROI calculation
4. **Conversion Tracking:** Link viewing requests to traffic sources
5. **Property Grouping:** Analyze traffic patterns by price range, bedrooms, parish
6. **Competitive Analysis:** Compare property performance within similar categories

### Database Expansion Ideas
```sql
-- Track historical changes
ALTER TABLE property_traffic_detail 
ADD COLUMN previous_period_sessions INT,
ADD COLUMN period_change_percent DECIMAL(5,2);

-- Link to conversions
ALTER TABLE property_traffic_detail
ADD COLUMN viewing_requests INT DEFAULT 0,
ADD COLUMN conversion_rate DECIMAL(5,4);
```

## Troubleshooting

### No data for specific property
**Check if property exists in feed:**
```bash
ddev exec python3 scripts/sync_property_feed.py --dry-run | grep STH250129
```

**Check if property has analytics data:**
```bash
ddev exec python3 scripts/view_traffic_report.py --property STH250129
```

**Check database directly:**
```sql
SELECT * FROM property_traffic_detail WHERE reference = 'STH250129';
```

### Data seems outdated
**Re-fetch from GA4:**
```bash
ddev exec python3 scripts/populate_traffic_database.py --days 30
```

### Feed sync failing
**Test with dry-run first:**
```bash
ddev exec python3 scripts/sync_property_feed.py --dry-run
```

**Check feed URL manually:**
```bash
curl https://api.ndestates.com/feeds/ndefeed.xml | head -50
```

### Database queries slow
**Check indexes:**
```sql
SHOW INDEX FROM property_traffic_detail;
```

**Existing indexes:**
- idx_reference
- idx_date
- idx_period
- idx_source
- idx_medium
- idx_sessions
- idx_date_period

## Critical Lessons Learned

### 1. Never Invent URLs
**Initial error:** Agent created `https://www.ndestates.com/properties.xml` which didn't exist
**Correct URL:** `https://api.ndestates.com/feeds/ndefeed.xml`
**Lesson:** Always verify URLs exist or ask user before implementing

### 2. Column Names Matter
**Initial error:** Used `updated_at` column that didn't exist in schema
**Correct column:** `last_updated`
**Lesson:** Check database schema before writing queries

### 3. Present Facts, Not Opinions
**User requirement:** "I WILL DECIDE WHAT IS A LOW PERFORMER NOT YOU"
**Implementation:** Remove all performance categorization, show raw numbers
**Lesson:** AI should provide data, humans make business decisions

### 4. Granularity Enables Flexibility
**Design choice:** Store source and medium as separate columns
**Benefit:** Can query by source alone, medium alone, or combination
**Lesson:** More granular data = more flexible analysis

## Support & Documentation

**Main README:** `/home/nickd/projects/google-stats/README.md`
**Architecture:** `/home/nickd/projects/google-stats/ARCHITECTURE.md`
**This Document:** `/home/nickd/projects/google-stats/TRAFFIC_DATABASE_README.md`

**Key Contact Points:**
- Feed URL: `https://api.ndestates.com/feeds/ndefeed.xml`
- Database: MariaDB via DDEV (`ddev exec mysql`)
- GA4 Property ID: Configured in `.env`

**Related Scripts:**
- `scripts/init_traffic_database.py` - Create table schema
- `scripts/populate_traffic_database.py` - Fetch and store data
- `scripts/view_traffic_report.py` - Display reports
- `scripts/sync_property_feed.py` - Sync with feed
- `scripts/catalog_analytics_report.py` - Enhanced with traffic sources
- `scripts/viewing_requests_manager.py` - Enhanced error messages

---

*Last Updated: 2026-01-09*
*Status: ✅ Fully Operational*
*Records: 1,360+ traffic source/medium combinations across 40 properties*
