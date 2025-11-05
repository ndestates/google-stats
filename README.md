# Google Stats

A Python application for processing and analyzing Google Analytics data.

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
   
   Copy the `.env` file and update it with your Google Analytics credentials:
   
   ```bash
   cp .env.example .env  # If you have an example file
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

## Development

### Available Commands

- `ddev exec python3 <script>` - Run Python scripts
- `ddev exec pip3 install --break-system-packages <package>` - Install Python packages
- `ddev exec pip3 list` - List installed packages
- `ddev exec -s python python <script>` - Run scripts in the dedicated Python service

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