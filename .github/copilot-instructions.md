# Google Stats - AI Agent Instructions

## Architecture Overview
This is a Google Analytics 4 (GA4) data analysis platform that integrates multiple marketing APIs. The codebase follows a modular structure:

- **`scripts/`**: Individual analysis scripts (20+ specialized tools for traffic, ads, email, SEO)
- **`src/`**: Core modules (`config.py`, `ga4_client.py`, `pdf_generator.py`)
- **`web/`**: PHP-based web interface for report execution (`index.php`, `run_report.php`, `documentation.php`)
- **`reports/`**: CSV output directory with date-stamped filenames
- **`app.py`**: Alternative Flask web interface (secondary to PHP frontend)

## Core Patterns

### Script Structure
All analysis scripts follow this pattern:
```python
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config import REPORTS_DIR
from src.ga4_client import run_report, create_date_range

# Get data
response = run_report(dimensions=[...], metrics=[...], date_ranges=[...])
# Process with pandas
df = pd.DataFrame(...)
# Save to reports/
df.to_csv(os.path.join(REPORTS_DIR, f"report_{start_date}_to_{end_date}.csv"), index=False)
```

### Date Handling
Use helper functions from `src/ga4_client.py`:
- `create_date_range(start, end)` - GA4 DateRange objects
- `get_yesterday_date()` - "YYYY-MM-DD" format
- `get_last_30_days_range()` - DateRange for last 30 days

### API Integration
- GA4: Primary data source via `google-analytics-data` library
- Google Ads: Campaign performance via `google-ads` library
- Mailchimp: Email analytics via API client
- GSC: Search Console data integration

## Development Workflow

### Running Scripts
```bash
# Via DDEV (recommended)
ddev exec python3 scripts/yesterday_report.py

# Direct execution (if Python environment configured)
python3 scripts/yesterday_report.py
```

### Environment Setup
- DDEV provides isolated Python 3.11 environment
- Credentials via `.env` file (gitignored)
- Service account keys in `.ddev/keys/`
- `GOOGLE_APPLICATION_CREDENTIALS` set automatically

### Report Generation
- All CSVs saved to `reports/` with format: `{report_type}_{start_date}_to_{end_date}.csv`
- Web interface (`app.py`) provides UI for script execution
- PDF reports generated via `src/pdf_generator.py`

## Testing Workflow

### Running Tests
```bash
# All tests
python run_tests.py

# Unit tests only
python run_tests.py unit

# Integration tests
python run_tests.py integration

# Specific script tests
python run_tests.py --script content_performance

# With coverage
python run_tests.py --coverage
```

### Test Structure
- Unit tests in `tests/test_*.py`
- Script tests in `tests/test_scripts/`
- Integration tests in `tests/test_integration/`
- Mocks for API calls to avoid requiring credentials

## Key Conventions

### Error Handling
```python
if response.row_count == 0:
    print("❌ No data found for the specified date range.")
    return
```

### Data Processing
- Use pandas for DataFrame operations
- Convert GA4 metrics: `int(row.metric_values[0].value)`
- Handle missing data gracefully

### Import Pattern
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.config import GA4_PROPERTY_ID, REPORTS_DIR
```

## Integration Points

### Web Interface
- **Primary**: PHP-based frontend (`web/index.php`, `web/run_report.php`, `web/documentation.php`)
- **Secondary**: Flask app (`app.py`) - alternative Python-based interface
- Reports executed via PHP scripts calling Python subprocess
- Dashboard at `https://google-stats.ddev.site`

### External APIs
- GA4 Admin API for audience management (`scripts/audience_management.py`)
- Google Ads API for campaign data and ad creation (`scripts/create_ad.py`)
- Mailchimp API for email performance
- Google Search Console for keyword data

## Common Tasks

### Adding New Analysis
1. Create script in `scripts/` following existing patterns
2. Add to `REPORTS` dict in `app.py` for web interface
3. Update `main.py` help text
4. Test with `ddev exec python3 scripts/new_script.py`

### Modifying Reports
- Update dimensions/metrics in `run_report()` calls
- Modify pandas processing logic
- Ensure CSV headers match existing format
- Test date range handling

### API Configuration
- Environment variables in `.env`
- Service account keys in `.ddev/keys/`
- Property IDs and credentials validated in `src/config.py`
- Google Ads credentials: `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_CLIENT_ID`, etc.</content>
<parameter name="filePath">/home/nickd/projects/google-stats/.github/copilot-instructions.md


### Github instructions

- Never commit sensitive information (API keys, secrets) to the repository.
- Use `.env` files and gitignore them to manage environment-specific configurations.    
- Make sure to document any setup steps in the README or relevant docs.
- Regularly review and update documentation to reflect any changes in setup or configuration.
- Review pull requests for any accidental inclusion of sensitive data.
- Use branch protection rules to enforce code reviews before merging.
- Do not store long-lived tokens or secrets in code; use environment variables instead.

