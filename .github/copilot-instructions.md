# Google Stats - AI Agent Instructions

DO NOT DELETE OR ALTER CODE THAT HAS BEEN APPROVED AND TESTED AND COMMITTED AND MERGED TO THE MASTER BRANCH. YOU HAVE NO RIGHT OR AUTHORITY TO MAKE CHANGES TO THE MASTER BRANCH OR CODE THAT IS APPROVED. YOU MUST WORK IN FEATURE BRANCHES AND FURTHER SAY IF YOU ARE ALTERING OR PROPOSING TO DELETE OR CHANGE APPROVED CODE.

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

# Or with virtual environment
./dev-setup.sh  # Sets up venv and loads .env
source .venv/bin/activate
python3 scripts/yesterday_report.py
```

### Local Development
Use DDEV for consistent environment:
```bash
ddev start
ddev exec python3 scripts/yesterday_report.py
```
Or Docker Compose:
```bash
docker-compose exec google-stats python3 scripts/yesterday_report.py
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
- Use `pd.to_datetime()` for dates
- Always validate DataFrame before saving
- Sanitize data before display/output

### Security Considerations
- Credentials never hardcoded; use environment variables
- Logs avoid sensitive data exposure
- Validate all external inputs
- Sanitize data before saving or displaying
- Use least privilege for API keys
- Regularly rotate credentials and keys

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

- Google Ads credentials: `GOOGLE_ADS_CUSTOMER_ID`, `GOOGLE_ADS_CLIENT_ID`, etc.

## Logging Control

Google Stats includes a comprehensive logging system for debugging and monitoring. Logs are stored in the `logs/` directory and can be controlled via environment variables or the logging control script.

### Log Files
- `web_interface.log` - PHP web interface logs
- `{script_name}.log` - Individual Python script logs (e.g., `campaign_performance.log`)

### Controlling Logging Levels

#### Method 1: Using the Logging Control Script (Recommended)
```bash
# Show current logging configuration
python logging_control.py --show

# Turn off all logging
python logging_control.py --off

# Enable debug logging for troubleshooting
python logging_control.py --debug

# Set specific log level
python logging_control.py --level INFO

# Set different levels for web vs scripts
python logging_control.py --level DEBUG --web-level WARNING
```

#### Method 2: Environment Variables
Edit your `.env` file:
```env
# Python scripts logging level
LOG_LEVEL=INFO

# Web interface logging level (falls back to LOG_LEVEL if not set)
WEB_LOG_LEVEL=INFO
```

### Available Log Levels
- `DEBUG` - Detailed debugging information
- `INFO` - General information (default)
- `WARNING` - Warning messages only
- `ERROR` - Error messages only
- `CRITICAL` - Critical errors only
- `OFF` - Disable all logging

### Usage Examples

#### Debugging a Script
```bash
# Enable debug logging
python logging_control.py --debug

# Run your script
ddev exec python3 scripts/yesterday_report.py

# Review logs
cat logs/yesterday_report.log
```

#### Disabling All Logging
```bash
# Turn off all logging
python logging_control.py --off
```

## Project Management & Branch Strategy

### TODO File Conventions
- **Naming Convention**: Use `YYYY-MM-DD_TODO.md` format for daily TODO files (e.g., `2025-12-21_TODO.md`)
- **Numbered Tasks**: All tasks must be numbered for easy reference and tracking
- **Comprehensive Documentation**: Every task, decision, and change must be documented in TODO files for future searchability
- **Progress Tracking**: Use checkboxes `[x]` for completed tasks and `[ ]` for pending tasks
- **Categorization**: Group related tasks under clear headings with emoji indicators (✅ 🔍 🎯 📊 📝)

### Branch Management Rules
- **Purpose Adherence**: Never deviate from a branch's original purpose
  - If a branch was created for documentation (e.g., `feature/user-admin-documentation`), only work on documentation tasks
  - If you start working on unrelated features (database changes, new functionality, bug fixes), **STOP IMMEDIATELY**
  - Create a new appropriately named branch for the new work instead
- **Branch Naming**: Use descriptive, purpose-specific names:
  - `feature/feature-name` for new features
  - `fix/issue-description` for bug fixes
  - `docs/documentation-purpose` for documentation work
  - `refactor/refactor-description` for code refactoring
- **Single Responsibility**: Each branch should address one specific concern or feature
- **Regular Merging**: Keep branches up-to-date with develop through regular merges or rebases

### Warning System
When working in a branch, always verify that new work aligns with the branch's purpose:
- **Documentation branches**: Only documentation, README updates, or related files
- **Feature branches**: Only the specific feature implementation
- **Fix branches**: Only the specific bug fix
- **Database branches**: Only database schema changes and migrations


### Github instructions

- Never commit sensitive information (API keys, secrets) to the repository.
- Use `.env` files and gitignore them to manage environment-specific configurations.    
- Make sure to document any setup steps in the README or relevant docs.
- Regularly review and update documentation to reflect any changes in setup or configuration.
- Review pull requests for any accidental inclusion of sensitive data.
- Use branch protection rules to enforce code reviews before merging.
- Do not store long-lived tokens or secrets in code; use environment variables instead.

