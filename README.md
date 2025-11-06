# Google Stats

A Python application for processing and analyzing Google Analytics 4 data.

## Project Structure

```
google-stats/
├── scripts/                    # Executable analytics scripts
│   ├── yesterday_report.py     # Daily report (yesterday's data)
│   ├── all_pages_sources_report.py  # Monthly report (30 days)
│   ├── get_top_pages.py        # Top pages analysis
│   └── google_ads_performance.py   # Google Ads performance
├── src/                        # Shared source code
│   ├── config.py              # Environment variables & configuration
│   └── ga4_client.py          # GA4 API client utilities
├── reports/                   # Generated CSV reports (auto-generated)
├── config/                    # Configuration templates
│   └── .env.example           # Environment variables template
├── requirements.txt           # Python dependencies
├── main.py                    # Entry point with available scripts
├── .env                       # Your credentials (gitignored)
└── .ddev/                     # DDEV configuration
```

## Setup

This project uses DDEV for development environment management.

### Prerequisites

- [DDEV](https://ddev.readthedocs.io/en/stable/)
- Docker

### Getting Started

1. **Start DDEV:**
   ```bash
   ddev start
   ```

### Configuration

1. **Environment Variables:**
   
   Copy the config template and update it with your Google Analytics credentials:
   
   ```bash
   cp config/.env.example .env
   ```
   
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

## Contributing

1. Follow PEP 8 style guidelines
2. Use type hints where appropriate
3. Write tests for new functionality
4. Update documentation as needed