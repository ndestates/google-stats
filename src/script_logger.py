#!/usr/bin/env python3
"""
Logging utility for Google Stats Python scripts
Provides centralized logging with configurable levels and file output
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path

class ScriptLogger:
    """Centralized logging for Google Stats scripts"""

    def __init__(self, script_name=None, log_level=None):
        self.script_name = script_name or Path(sys.argv[0]).stem

        # Create logs directory if it doesn't exist
        self.log_dir = Path(__file__).parent.parent / 'logs'
        self.log_dir.mkdir(exist_ok=True)

        # Determine log level from environment variable or parameter
        if log_level is None:
            env_level = os.getenv('LOG_LEVEL', 'INFO').upper()
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL,
                'OFF': logging.CRITICAL + 1  # Effectively disable logging
            }
            log_level = level_map.get(env_level, logging.INFO)

        # Set up logger
        self.logger = logging.getLogger(f'google_stats.{self.script_name}')
        self.logger.setLevel(log_level)

        # Remove any existing handlers
        self.logger.handlers.clear()

        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # File handler with rotation
        log_file = self.log_dir / f'{self.script_name}.log'
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def debug(self, message, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)

    def log_script_start(self, args=None):
        """Log script execution start"""
        self.info(f"Script {self.script_name} started")
        if args:
            self.debug(f"Arguments: {args}")

    def log_script_end(self, success=True, error=None):
        """Log script execution end"""
        if success:
            self.info(f"Script {self.script_name} completed successfully")
        else:
            self.error(f"Script {self.script_name} failed: {error}")

    def log_api_call(self, endpoint, params=None, success=True, error=None):
        """Log API call details"""
        if success:
            self.debug(f"API call successful: {endpoint}")
        else:
            self.warning(f"API call failed: {endpoint} - {error}")
        if params:
            # Sanitize sensitive parameters
            safe_params = self._sanitize_params(params)
            self.debug(f"API parameters: {safe_params}")

    def log_data_processing(self, operation, records_count=None, duration=None):
        """Log data processing operations"""
        message = f"Data processing: {operation}"
        if records_count is not None:
            message += f" ({records_count} records)"
        if duration is not None:
            message += f" in {duration:.2f}s"
        self.info(message)

    def _sanitize_params(self, params):
        """Remove sensitive information from parameters"""
        if not isinstance(params, dict):
            return params

        sensitive_keys = ['access_token', 'token', 'secret', 'password', 'key', 'credentials']
        sanitized = {}

        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = value

        return sanitized

# Global logger instance for easy importing
logger = None

def get_logger(script_name=None):
    """Get or create a logger instance"""
    global logger
    if logger is None:
        logger = ScriptLogger(script_name)
    return logger

def setup_script_logging(script_name=None):
    """Convenience function to set up logging for a script"""
    logger = get_logger(script_name)
    logger.log_script_start(sys.argv[1:] if len(sys.argv) > 1 else None)