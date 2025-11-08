# Google Analytics Test Suite

Comprehensive test suite for the Google Analytics 4 reporting platform.

## Overview

This test suite provides unit tests, integration tests, and mocks for testing all Google Analytics reporting scripts without requiring actual API calls or credentials.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_ga4_client.py         # Unit tests for GA4 client functions
├── test_scripts/              # Script-specific tests
│   ├── test_content_performance.py
│   ├── test_yesterday_report.py
│   └── test_google_ads_performance.py
└── test_integration/          # Integration tests
    └── test_full_workflow.py
```

## Running Tests

### Quick Start

```bash
# Run all tests
python run_tests.py

# Run unit tests only
python run_tests.py unit

# Run integration tests
python run_tests.py integration

# Run tests for specific script
python run_tests.py --script content_performance

# Run with coverage
python run_tests.py --coverage

# Run verbose output
python run_tests.py --verbose
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov=scripts

# Run specific test file
pytest tests/test_ga4_client.py

# Run tests matching pattern
pytest -k "content_performance"

# Run tests with detailed output
pytest -v
```

## Test Categories

### Unit Tests (`tests/test_ga4_client.py`)
- GA4 client function testing
- Date range creation and validation
- Dimension and metric creation
- Report request building

### Script Tests (`tests/test_scripts/`)
- Individual script functionality
- API call mocking
- Data processing validation
- Error handling

### Integration Tests (`tests/test_integration/`)
- Full workflow testing
- CSV output validation
- Data consistency checks
- Cross-script compatibility

## Mock Data

The test suite uses comprehensive mock data that simulates real GA4 API responses:

- **Sample page data**: Traffic metrics for different pages
- **Channel performance data**: Marketing channel analytics
- **Campaign data**: Google Ads campaign performance
- **Empty responses**: Testing no-data scenarios

## Key Features

### Comprehensive Mocking
- GA4 API calls are fully mocked
- No real API credentials required
- No external network calls
- Deterministic test results

### Data Validation
- Metric data type checking
- Value range validation (e.g., bounce rates 0-1)
- CSV export integrity
- Date format validation

### Error Testing
- API connection failures
- Missing credentials
- Invalid date ranges
- Empty data responses

### Coverage Reporting
- Code coverage measurement
- Missing test identification
- HTML coverage reports

## Test Fixtures

### `mock_ga4_response`
Mock GA4 RunReportResponse with sample data for 3 pages/channels.

### `mock_empty_ga4_response`
Mock response with no data (row_count = 0).

### `mock_ga4_client`
Mock GA4 client for testing API interactions.

### `sample_date_ranges`
Common date ranges used across tests.

### `sample_page_data` / `sample_channel_data`
Sample analytics data for validation testing.

## Writing New Tests

### Adding Script Tests

1. Create `tests/test_scripts/test_your_script.py`
2. Import the script functions
3. Use pytest fixtures for mocking
4. Test both success and error scenarios

Example:
```python
@patch('scripts.your_script.run_report')
def test_your_function_success(mock_run_report, mock_ga4_response):
    mock_run_report.return_value = mock_ga4_response

    result = your_script.your_function()

    assert result is not None
    # Add more assertions
```

### Adding Integration Tests

1. Create tests in `tests/test_integration/`
2. Test full workflows from API to CSV
3. Validate data consistency across scripts
4. Test error propagation

## CI/CD Integration

The test suite is designed for CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Tests
  run: |
    python run_tests.py --coverage --fail-fast

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./htmlcov/coverage.xml
```

## Test Data

Test data is stored in `tests/test_data/` and includes:
- Sample GA4 API responses (JSON)
- Expected CSV outputs
- Configuration test files

## Performance

Tests are optimized for speed:
- API calls are mocked (no network latency)
- Minimal file I/O for CSV testing
- Parallel test execution supported
- Fast feedback for development

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes project root
2. **Mock Failures**: Check fixture dependencies
3. **Coverage Issues**: Run `pytest --cov-report=html` for detailed reports

### Debugging Tests

```bash
# Run single test with debugging
pytest tests/test_scripts/test_content_performance.py::TestContentPerformance::test_analyze_content_engagement_success -s

# Run with pdb on failure
pytest --pdb

# Show all fixtures
pytest --fixtures
```

## Contributing

When adding new scripts or features:

1. Add corresponding unit tests
2. Update integration tests if needed
3. Maintain test coverage above 80%
4. Follow existing naming conventions
5. Add docstrings to test classes/methods

## Dependencies

Test dependencies are included in `requirements.txt`:
- pytest: Test framework
- pytest-cov: Coverage reporting
- unittest.mock: Mocking utilities (built-in)

Run tests in the DDEV environment for full compatibility:
```bash
ddev exec python run_tests.py
```