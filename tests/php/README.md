# PHP Unit Tests for Authentication System

This directory contains PHPUnit tests for the PHP authentication and credential management system.

## Setup

1. Install Composer dependencies:

   ```bash
   ddev exec composer install
   ```

2. Run the tests:

   ```bash
   ddev exec ./vendor/bin/phpunit
   ```

## Test Files

- `AuthenticationTest.php` - Tests for user authentication, session management, and user CRUD operations
- `CredentialsTest.php` - Tests for encrypted credential storage and validation
- `SecurityTest.php` - Tests for security monitoring, rate limiting, and logging

## Test Coverage

### Authentication

- User registration and login
- Password hashing and verification
- Session management and persistence
- Account lockout after failed attempts
- Session timeout handling

### Credentials

- AES-256 encryption/decryption
- Credential storage and retrieval
- Google API credential validation
- Import from .env files
- Environment variable loading

### Security

- Authentication event logging
- Failed login tracking
- Rate limiting simulation
- IP blocking functionality
- Suspicious activity detection
- Brute force protection

## Test Environment

Tests use isolated file storage with test-specific filenames:

- `test_users.json` - User data for testing
- `test_sessions.json` - Session data for testing
- `test_credentials.enc` - Encrypted credentials for testing

All test files are automatically cleaned up after test execution.

## Mock Objects

- `MockWebLogger` - Simulates the security logging system
- Test constants override production file paths
- Isolated environment prevents interference with production data

## Running Specific Tests

```bash
# Run all tests
ddev exec ./vendor/bin/phpunit

# Run specific test class
ddev exec ./vendor/bin/phpunit tests/php/AuthenticationTest.php

# Run specific test method
ddev exec ./vendor/bin/phpunit --filter testAuthenticateValidUser

# Run with coverage
ddev exec ./vendor/bin/phpunit --coverage-html coverage/
```

## Test Dependencies

- PHPUnit 9.5+
- PHP 7.4+ with OpenSSL extension
- File system write permissions for test files

