# Google Analytics Platform

A comprehensive analytics platform for Google Analytics 4, Google Ads, Mailchimp, and Google Search Console data analysis.

## 🚀 Features

### Analytics Tools

- **Hourly Traffic Analysis** - Time-of-day traffic patterns with engagement metrics
- **Page Traffic Analysis** - Individual page performance with source attribution
- **Top Pages Report** - Best performing content identification
- **Keywords Analysis** - Combined GSC and GA4 keyword insights

### Marketing Tools

- **Google Ads Performance** - Campaign effectiveness and ROI tracking
- **Google Ads Ad Creation** - Create new responsive search ads programmatically
- **Mailchimp Performance** - Email marketing analytics
- **Audience Management** - GA4 audience creation and management

## 📊 Key Capabilities

- **Real-time Analysis** - Live data processing with immediate results
- **Comprehensive Metrics** - Users, sessions, engagement, conversions, and more
- **Multi-channel Attribution** - Source/medium, campaigns, and channel groupings
- **CSV Export** - Detailed data exports for further analysis
- **Web Interface** - User-friendly dashboard for all tools

## 🛠️ Quick Start

### Prerequisites

- DDEV environment
- Google Analytics 4 property access
- Google Ads API credentials (optional) - see [Google Ads Setup Guide](README_Google_Ads_Credentials.md)
- Mailchimp API key (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/ndestates/google-stats.git
cd google-stats

# Start DDEV
ddev start

# Access the web interface
# https://google-stats.ddev.site
```

### Usage Examples

#### Web Interface

Visit `https://google-stats.ddev.site` for the complete dashboard with all analytics tools.

#### Command Line

```bash
# Hourly traffic analysis
ddev exec python3 scripts/hourly_traffic_analysis.py /valuations 7

# Page traffic analysis
ddev exec python3 scripts/page_traffic_analysis.py /valuations 30

# Google Ads performance
ddev exec python3 scripts/google_ads_performance.py

# Create new Google Ads
ddev exec python3 scripts/create_ad.py --customer-id 1234567890 --headlines "Luxury Space Cruise" --descriptions "Book your adventure" --final-urls "https://example.com"

# Get Google Ads refresh token
ddev exec python3 get_google_ads_refresh_token.py
# OR use OAuth Playground (recommended): see GOOGLE_ADS_OAUTH_PLAYGROUND.md
# OR use manual script: python3 manual_google_ads_oauth.py

# Mailchimp reports
ddev exec python3 scripts/mailchimp_performance.py --report-type yesterday
ddev exec python3 scripts/mailchimp_performance.py --report-type date-range --start-date 2025-11-01 --end-date 2025-11-15
```

## 📖 Documentation

Complete documentation is available at:

- **Web Documentation**: `https://google-stats.ddev.site/documentation.php`
- **Repository**: See `web/documentation.php` for the full documentation

## 📁 Project Structure

```
google-stats/
├── scripts/                 # Python analysis scripts
│   ├── hourly_traffic_analysis.py
│   ├── page_traffic_analysis.py
│   ├── google_ads_performance.py
│   └── ...
├── web/                     # Web interface
│   ├── index.php           # Main dashboard
│   ├── documentation.php   # Full documentation
│   └── run_report.php      # Script execution handler
├── reports/                 # Generated CSV reports
├── src/                     # Core modules
│   ├── config.py           # Configuration
│   ├── ga4_client.py       # GA4 API client
│   └── ...
├── config/                  # Configuration files
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

### Google Analytics 4

- Property ID configured in `src/config.py`
- Service account credentials in `.ddev/keys/`

### Property Information (Optional)

Add property name and address to customize PDF reports:

```env
# Add to your .env file
PROPERTY_NAME="Your Business Name"
PROPERTY_ADDRESS="123 Main Street, City, State 12345"
```

### Google Ads (Optional)

- Customer ID and API credentials required
- See [Google Ads Setup Guide](README_Google_Ads_Credentials.md) for complete setup instructions
- Configure in `.env` file and respective scripts

### Mailchimp (Optional)

- API key required for email analytics
- Configure in `scripts/mailchimp_performance.py`

## 📊 Sample Output

### Hourly Traffic Analysis

```
1. Source/Medium: google / cpc
   Total Users: 1,569 (New: 1,098)
   Total Sessions: 1,625 (Engaged: 1,625)
   Best Hour: 18:00 (186 users)
   Channel Groups: Cross-network, Display
   Hourly Traffic:
   Hour | Users | New Users | Sessions | Engaged | Pageviews
   -----|-------|-----------|----------|----------|-----------
    18:00 |   162 |       115 |      164 |      164 |         0
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is proprietary software for NDEstates analytics.

## 🆘 Support

For technical support or feature requests:

- Check the documentation at `web/documentation.php`
- Contact the development team
- Review the code comments for implementation details

---

**Built with**: Python 3.11, Google Analytics 4 API, Google Ads API, Mailchimp API, Bootstrap 5
**Last Updated**: November 7, 2025

   Edit `.env` with your actual values:

   ```env
   GA4_PROPERTY_ID=your_ga4_property_id_here
   GA4_KEY_PATH=/path/to/your/service-account-key.json
   ```

   Or create `.env` with the following variables:

   ```env
   # Google Analytics 4 Configuration
   GA4_PROPERTY_ID=your_property_id_here
   GA4_KEY_PATH=/path/to/your/service-account-key.json
   ```

   **Note:** The `.env` file is gitignored for security. Never commit actual credentials to the repository.

2. **Google Analytics Setup:**

   - Create a Google Cloud Project
   - Enable the Google Analytics Data API
   - Create a Service Account and download the JSON key
   - Add the Service Account as a viewer to your GA4 property
   - Update the `GA4_KEY_PATH` in your `.env` file

## Usage

### Available Scripts

Run scripts using DDEV:

```bash
# Daily report (yesterday's data)
ddev exec python3 scripts/yesterday_report.py

# Monthly report (last 30 days)
ddev exec python3 scripts/all_pages_sources_report.py

# Top pages analysis
ddev exec python3 scripts/get_top_pages.py

# Google Ads performance analysis
ddev exec python3 scripts/google_ads_performance.py

# Show available scripts
ddev exec python3 main.py
```

### Report Output

All CSV reports are automatically saved to the `reports/` folder:

- `yesterday_report_YYYY-MM-DD.csv` - Daily detailed report
- `yesterday_summary_YYYY-MM-DD.csv` - Daily summary report
- `comprehensive_page_source_report_YYYY-MM-DD_to_YYYY-MM-DD.csv` - Monthly detailed report
- `page_summary_report_YYYY-MM-DD_to_YYYY-MM-DD.csv` - Monthly summary report
- `google_ads_campaign_performance_YYYY-MM-DD_to_YYYY-MM-DD.csv` - Ads campaign data
- `google_ads_hourly_performance_YYYY-MM-DD_to_YYYY-MM-DD.csv` - Ads hourly data

## Development

### Available Commands

- `ddev exec python3 <script>` - Run Python scripts
- `ddev exec pip3 install --break-system-packages <package>` - Install Python packages
- `ddev exec pip3 list` - List installed packages

### Project Structure

```
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── .ddev/                  # DDEV configuration
│   ├── config.yaml        # DDEV project configuration
│   ├── web-build/         # Custom web container setup
│   └── docker-compose.python.yaml  # Dedicated Python service
└── .gitignore             # Git ignore rules for Python
```

## Configuration

The project is configured with:

- Python 3.11+ in the web container
- Dedicated Python service for isolated development
- MariaDB database for data storage
- Nginx web server for serving web interfaces

## 🔒 Security

### Authentication & Access Control

- **Session-based Authentication** - Secure login with automatic session management
- **Role-based Access** - Admin users with configurable permissions
- **Password Security** - Bcrypt hashing with complexity requirements
- **Account Protection** - Automatic lockout after failed attempts

### Credential Management

- **Encrypted Storage** - AES-256 encryption for all API credentials
- **Secure Key Management** - Master encryption keys stored in environment variables
- **Access Logging** - All credential access and modifications logged
- **No Plain Text** - Credentials never stored or transmitted in plain text

### Monitoring & Protection

- **Security Logging** - Comprehensive logging of all security events
- **Rate Limiting** - Protection against brute force attacks
- **IP Blocking** - Automatic blocking of suspicious IP addresses
- **Intrusion Detection** - Pattern recognition for malicious activity

### Best Practices

- Use HTTPS in production
- Regularly rotate API keys and passwords
- Monitor security logs for suspicious activity
- Keep software and dependencies updated
- Use principle of least privilege for service accounts

For detailed security setup and monitoring, see the [Web Documentation](web/documentation.php#security).

## Contributing

1. Follow PEP 8 style guidelines
2. Use type hints where appropriate
3. Write tests for new functionality
4. Update documentation as needed
