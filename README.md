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

2. **Install Python dependencies:**
   ```bash
   ddev pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   ddev exec python3 main.py
   ```

## Development

### Available Commands

- `ddev exec python3 <script>` - Run Python scripts
- `ddev pip <command>` - Manage Python packages
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