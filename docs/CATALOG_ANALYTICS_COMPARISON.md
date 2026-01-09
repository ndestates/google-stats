# Catalog Analytics Comparison Tool

## Overview

The Catalog Analytics Comparison tool helps you analyze how your property listings are performing in Google Analytics compared to your catalog inventory. It identifies which listings need marketing attention, tracks viewing requests, correlates marketing campaigns with actual results, and provides platform-specific recommendations.

## Features

### 📊 Performance Analysis
- **Pageview Tracking**: Total views per listing over 7/14/30/60/90 days
- **User Engagement**: Unique visitors and session counts
- **Time on Page**: Average session duration per listing
- **Bounce Rate**: Percentage of visitors leaving immediately
- **Traffic Sources**: Breakdown by 10+ channels including:
  - Email Marketing (Mailchimp)
  - Facebook Ads & Organic
  - Instagram Ads & Organic
  - LinkedIn Ads & Organic
  - Google Ads (PPC)
  - Google Organic (SEO)
  - Buffer (Social Media Management)
  - Direct, Referral, Shopping

### 📞 Viewing Request Tracking
- **Request Recording**: Log viewing requests with dates and notes
- **Property History**: View all viewing requests per property
- **Conversion Analysis**: Calculate viewing-to-session conversion rates
- **Source Attribution**: Which traffic channels drive actual viewings

### 📢 Campaign Correlation
- **Campaign Tracking**: Monitor marketing campaigns across all platforms
- **Budget Management**: Track spending and ROI per campaign
- **Viewing Attribution**: Link viewing requests to active campaigns
- **Timeline Analysis**: See when campaigns and viewings happened together
- **Cost per Viewing**: Calculate marketing efficiency metrics

### 🎯 Performance Scoring
Each listing receives a score from 0-100 based on:
- **Pageviews** (40 points max): Volume of traffic
- **Users** (30 points max): Unique visitor count
- **Engagement** (15 points max): Time spent on page
- **Bounce Rate** (15 points max): Quality of engagement

### 💡 Marketing Recommendations
Automated recommendations for each listing based on:
- Current performance metrics
- Traffic source analysis
- Property value and type
- Historical trends

Recommendations include:
- **Priority Level**: Critical, High, Medium, Low
- **Platform**: Google Ads, Facebook/Instagram, SEO, Social Media
- **Action**: Specific steps to take
- **Budget Estimate**: Suggested monthly spend
- **Expected Impact**: Projected results

## Usage

### Basic Reports

```bash
# 30-day report (default)
ddev exec python3 scripts/catalog_analytics_report.py --days 30

# 60-day report
ddev exec python3 scripts/catalog_analytics_report.py --days 60

# 90-day report with marketing recommendations
ddev exec python3 scripts/catalog_analytics_report.py --days 90 --recommendations
```

### Filtered Reports

```bash
# Only buy properties
ddev exec python3 scripts/catalog_analytics_report.py --days 30 --type buy

# Only available properties
ddev exec python3 scripts/catalog_analytics_report.py --days 30 --status available

# Only low-performing listings (score < 40)
ddev exec python3 scripts/catalog_analytics_report.py --days 30 --low-performers
```

### Export Options

```bash
# Export to CSV
ddev exec python3 scripts/catalog_analytics_report.py --days 30 --export-csv

# Full report with recommendations and CSV export
ddev exec python3 scripts/catalog_analytics_report.py --days 30 --recommendations --export-csv
```

## Report Sections

### 1. Summary Statistics
- Total listings in catalog
- Listings with traffic vs. no traffic
- Total pageviews and users
- Average performance score

### 2. Top Performers 🏆
Shows your best 5 listings with:
- Performance score
- Key metrics (pageviews, users, time on page)

### 3. Listings Needing Attention ⚠️
Shows listings with score < 40:
- Full property details
- Performance breakdown
- Traffic source analysis
- Marketing recommendations (if enabled)

## Understanding Marketing Recommendations

### Priority Levels

**CRITICAL**: Immediate action required
- Zero traffic detected
- High-value property with no visibility

**HIGH**: Action needed soon
- Performance score < 30
- Significant gaps in traffic sources

**MEDIUM**: Should address
- Low organic traffic
- High bounce rates on decent traffic
- Missing paid advertising on premium properties

**LOW**: Monitor and optimize
- Moderate performance
- Good overall but room for improvement

### Platform Recommendations

#### Google Ads
- **When**: Low overall traffic, high-value properties
- **Budget**: £150-400/month depending on property value
- **Expected Impact**: High (immediate visibility)

#### Facebook/Instagram
- **When**: Need broader reach, visual appeal
- **Budget**: £100-200/month
- **Expected Impact**: Medium (brand awareness)

#### SEO
- **When**: Low organic traffic percentage
- **Budget**: £300-500 one-time or internal effort
- **Expected Impact**: Medium (long-term growth)

#### Social Media
- **When**: Minimal social traffic
- **Budget**: Internal effort
- **Expected Impact**: Low-Medium (engagement building)

#### Content/Website
- **When**: High bounce rate with decent traffic
- **Budget**: Internal effort
- **Expected Impact**: Medium (improved conversions)

## CSV Export Format

Exported CSV includes:
- Reference
- Property Name
- Type (buy/rent)
- Status
- Price
- URL
- Performance Score
- Pageviews
- Users
- Sessions
- Average Session Duration
- Bounce Rate
- Top Traffic Sources

## Best Practices

### 1. Regular Reviews
- Run weekly 30-day reports to spot trends
- Monthly 60-day reports for broader patterns
- Quarterly 90-day reports for strategic planning

### 2. Prioritize Actions
- Address CRITICAL items immediately
- Plan HIGH priority items within 1-2 weeks
- Schedule MEDIUM items for monthly review
- Monitor LOW priority items quarterly

### 3. Budget Allocation
- Start with listings that have zero traffic
- Focus on high-value properties next
- Gradually expand to moderate performers
- Test and measure results before scaling

### 4. Track Results
- Export reports before implementing changes
- Re-run after 2-4 weeks to measure impact
- Compare scores over time
- Adjust strategies based on data

## Example Scenarios

### Scenario 1: Zero Traffic Listing
```
Property: Luxury 4-bed, £650,000
Score: 0/100
Pageviews: 0
Recommendation: CRITICAL - Launch immediate PPC campaign
Budget: £250-400/month
Expected Impact: HIGH
```

### Scenario 2: High Traffic, High Bounce
```
Property: 2-bed flat, £325,000
Score: 45/100
Pageviews: 87
Bounce Rate: 78%
Recommendation: MEDIUM - Improve listing content and images
Budget: Internal effort
Expected Impact: MEDIUM
```

### Scenario 3: Good Performance
```
Property: 3-bed house, £475,000
Score: 78/100
Pageviews: 156
Users: 89
Recommendation: LOW - Maintain current efforts
Budget: Current spend
Expected Impact: Maintain results
```

## Integration with Audience Management

This tool complements the audience management features:
- Identify which listings need audience targeting
- Create audiences for specific property segments
- Target ads based on performance data
- Measure audience effectiveness over time

## Troubleshooting

### No analytics data returned
- Check GA4_PROPERTY_ID is set correctly
- Verify service account has Analytics read permissions
- Ensure date range has actual traffic

### Listings not matching analytics
- URL paths must match between feed and GA4
- Check for trailing slashes or query parameters
- Verify property URLs in feed are correct

### Feed fetch errors
- Check feed URL is accessible
- Verify XML format is correct
- Ensure network connectivity

## Future Enhancements

Planned features:
- Historical trend analysis
- Competitor benchmarking
- Automated alert system
- Integration with Google Ads API
- A/B testing recommendations
- ROI tracking per recommendation
- Email report delivery
- Dashboard visualization

## Related Documentation

- [Audience Management](./BULK_DELETE_AUDIENCES.md)
- [Property Database](../PROPERTY_DATABASE_README.md)
- [Architecture Overview](../ARCHITECTURE.md)
