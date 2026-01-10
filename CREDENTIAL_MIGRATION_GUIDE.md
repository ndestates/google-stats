# Database-Encrypted Credential Storage Migration Guide

## Overview

This guide walks through migrating Google Application Credentials from file-based storage (`.json` files in `.ddev/keys/`) to encrypted database storage for enhanced security.

## Why Migrate?

### Security Risks of File-Based Credentials:
- ❌ Plain JSON files contain sensitive private keys
- ❌ Files can be accidentally committed to version control
- ❌ File paths exposed in configuration files
- ❌ Difficult to rotate credentials
- ❌ No audit trail of credential usage
- ❌ No centralized credential management

### Benefits of Database-Encrypted Storage:
- ✅ AES-256 encryption using Fernet (symmetric encryption)
- ✅ Encrypted at rest in database
- ✅ Centralized credential management
- ✅ Easy credential rotation
- ✅ Audit trail via database timestamps
- ✅ No plaintext files on filesystem
- ✅ Compatible with existing code (transparent temp file creation)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Google Stats Application                                    │
│                                                               │
│  ┌──────────────┐        ┌────────────────────────┐          │
│  │ src/config.py│───────>│ credential_manager.py  │          │
│  │              │        │ - Decrypt credentials  │          │
│  │ GA4 Scripts  │        │ - Create temp files    │          │
│  └──────────────┘        │ - Cache credentials    │          │
│         │                └───────────┬────────────┘          │
│         │                            │                       │
│         │                            ▼                       │
│         │                   ┌────────────────┐              │
│         │                   │    Database    │              │
│         │                   │  credentials   │              │
│         │                   │     table      │              │
│         │                   └────────────────┘              │
│         │                                                    │
│         ▼                                                    │
│  ┌────────────────────────┐                                 │
│  │  Google Analytics API  │                                 │
│  └────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

## Migration Steps

### Step 1: Install Required Packages

```bash
cd /home/nickd/projects/google-stats
ddev exec pip install cryptography pymysql
```

### Step 2: Run Migration Script

```bash
# Default migration (removes plaintext file after backup)
ddev exec python3 scripts/migrate_credentials_to_db.py

# Keep plaintext file (not recommended for production)
ddev exec python3 scripts/migrate_credentials_to_db.py --keep-file

# Custom credential name
ddev exec python3 scripts/migrate_credentials_to_db.py \
  --file .ddev/keys/ga4-page-analytics-cf93eb65ac26.json \
  --name "GA4 Production Account" \
  --type google_token
```

### Step 3: Verify Migration

The script will:
1. ✅ Connect to database
2. ✅ Generate/load encryption key
3. ✅ Read and validate credential JSON
4. ✅ Create backup in `backup/credentials/`
5. ✅ Encrypt and store in database
6. ✅ Verify decryption works
7. ✅ Optionally remove plaintext file

Expected output:
```
======================================================================
GOOGLE APPLICATION CREDENTIALS MIGRATION
======================================================================
✅ Connected to database
✅ Encryption key saved to .env
✅ Read credential file: .ddev/keys/ga4-page-analytics-cf93eb65ac26.json
   - Type: service_account
   - Project: ga4-page-analytics
   - Email: ga4-service@ga4-page-analytics.iam.gserviceaccount.com
✅ Backup created: backup/credentials/20260109_123456_ga4-page-analytics-cf93eb65ac26.json
✅ Stored encrypted credential in database (ID: 1)
✅ Verification successful:
   - Name: GA4 Service Account
   - Type: google_token
   - Project: ga4-page-analytics
   - Email: ga4-service@ga4-page-analytics.iam.gserviceaccount.com
✅ Removed plaintext credential file: .ddev/keys/ga4-page-analytics-cf93eb65ac26.json

======================================================================
✅ MIGRATION COMPLETE
======================================================================
Credential ID: 1
Backup: backup/credentials/20260109_123456_ga4-page-analytics-cf93eb65ac26.json

Next steps:
1. Update .ddev/config.yaml to remove GOOGLE_APPLICATION_CREDENTIALS
2. Update src/config.py to use database credentials
3. Test GA4 scripts with new credential retrieval
======================================================================
```

### Step 4: Enable Database Credentials

Add to `.env`:
```env
# Enable database-backed credentials (recommended for production)
USE_DATABASE_CREDENTIALS=true
```

### Step 5: Update DDEV Config

Edit `.ddev/config.yaml` and **remove** the line:
```yaml
    - GOOGLE_APPLICATION_CREDENTIALS=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json
```

Or comment it out:
```yaml
    # Legacy file-based credential (migrated to database)
    # - GOOGLE_APPLICATION_CREDENTIALS=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json
```

### Step 6: Restart DDEV

```bash
ddev restart
```

### Step 7: Test GA4 Scripts

```bash
# Test with any GA4 script
ddev exec python3 scripts/yesterday_report.py

# Should see no errors and normal report generation
```

## How It Works

### Encryption Process

1. **Key Generation**: Uses PBKDF2 with SHA-256 to derive encryption key from master password (or generates random key)
2. **Encryption**: Entire JSON credential encrypted with AES-256 using Fernet
3. **Storage**: Encrypted blob stored in `credentials.encrypted_value` column
4. **Key Storage**: Encryption key stored in `credentials.encrypted_key` (also encrypted) or in `.env`

### Credential Retrieval Process

1. **Query Database**: Fetch encrypted credential by name and type
2. **Decrypt**: Use encryption key to decrypt credential
3. **Cache**: Store decrypted credential in memory cache
4. **Temp File**: Create temporary JSON file for Google client libraries
5. **Auto-Cleanup**: Temporary files deleted when script ends

### Code Changes

**Before (File-Based):**
```python
# src/config.py
GA4_KEY_PATH = os.getenv("GA4_KEY_PATH")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GA4_KEY_PATH
```

**After (Database-Backed):**
```python
# src/config.py - automatically uses database if USE_DATABASE_CREDENTIALS=true
from src.credential_manager import get_google_application_credentials

cred_path = get_ga4_credentials_path()  # Returns temp file path from database
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
```

## Database Schema

```sql
CREATE TABLE credentials (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL DEFAULT 1,
    name VARCHAR(100) NOT NULL,
    type ENUM('google_token','google_ads','api_key','database','other') NOT NULL,
    description TEXT,
    encrypted_value BLOB NOT NULL,          -- AES-256 encrypted JSON
    encrypted_key BLOB,                     -- Encryption key (for key rotation)
    created_by INT NOT NULL,
    last_updated_by INT,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_active (is_active),
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (last_updated_by) REFERENCES users(id)
);
```

## Environment Variables

Add these to `.env`:

```env
# Database credentials (already configured in DDEV)
DB_HOST=db
DB_NAME=google-stats
DB_USERNAME=db
DB_PASSWORD=db

# Enable database-backed credentials
USE_DATABASE_CREDENTIALS=true

# Encryption key (auto-generated by migration script)
CREDENTIAL_ENCRYPTION_KEY=<base64-encoded-key>

# Optional: Master password instead of random key
# CREDENTIAL_MASTER_PASSWORD=your-secure-password-here

# Optional: Custom salt for key derivation
# ENCRYPTION_SALT=google-stats-custom-salt
```

## Security Best Practices

### ✅ DO:
- Use database credentials in production
- Rotate encryption keys periodically
- Backup encrypted database regularly
- Use strong master passwords if not using random keys
- Keep `.env` file secure and gitignored
- Monitor `security_events` table for suspicious activity
- Set credential expiration dates where appropriate

### ❌ DON'T:
- Commit `.env` file to version control
- Use weak master passwords
- Store encryption keys in application code
- Share credentials between environments
- Keep inactive credentials enabled
- Log decrypted credential data

## Credential Management

### List Credentials

```python
from src.credential_manager import DatabaseCredentialManager

with DatabaseCredentialManager() as manager:
    for cred in manager.list_credentials():
        print(f"{cred['name']} ({cred['type']}) - Updated: {cred['updated_at']}")
```

### Retrieve Credential

```python
from src.credential_manager import DatabaseCredentialManager

with DatabaseCredentialManager() as manager:
    # Get as dict
    cred_data = manager.get_credential("GA4 Service Account", "google_token")
    
    # Get as temp file (for Google libraries)
    cred_path = manager.get_credential_as_temp_file("GA4 Service Account", "google_token")
```

### Update Credential

Run migration script again with same name to update:
```bash
ddev exec python3 scripts/migrate_credentials_to_db.py \
  --file path/to/new/credential.json \
  --name "GA4 Service Account"
```

### Rotate Encryption Key

1. Retrieve all credentials
2. Generate new encryption key
3. Re-encrypt all credentials with new key
4. Update `.env` with new key

(Automated rotation script coming in future version)

## Rollback Plan

If issues occur, rollback to file-based credentials:

### Step 1: Restore Backup File
```bash
cp backup/credentials/TIMESTAMP_ga4-page-analytics-cf93eb65ac26.json \
   .ddev/keys/ga4-page-analytics-cf93eb65ac26.json
```

### Step 2: Disable Database Credentials
Edit `.env`:
```env
USE_DATABASE_CREDENTIALS=false
```

### Step 3: Update DDEV Config
Restore in `.ddev/config.yaml`:
```yaml
    - GOOGLE_APPLICATION_CREDENTIALS=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json
```

### Step 4: Restart
```bash
ddev restart
```

## Troubleshooting

### Error: "Credential not found in database"

**Solution**: Run migration script to import credential:
```bash
ddev exec python3 scripts/migrate_credentials_to_db.py
```

### Error: "No encryption key available"

**Solution**: Check `.env` for `CREDENTIAL_ENCRYPTION_KEY` or `CREDENTIAL_MASTER_PASSWORD`

### Error: "Failed to decrypt credential"

**Cause**: Encryption key mismatch or corrupted data

**Solution**: 
1. Restore from backup
2. Re-run migration script
3. Check `.env` for correct encryption key

### Script fails with database connection error

**Solution**: Verify database is running and credentials are correct:
```bash
ddev mysql -e "SELECT 1;" google-stats
```

## Web Interface (Future Enhancement)

A web-based credential management interface will be added in a future update:
- `/web/credentials.php` - Manage credentials securely
- Upload new credentials via web form
- View credential metadata (never displays decrypted values)
- Rotate encryption keys
- Audit credential usage

## Support

For issues or questions:
- Check logs in `/logs/` directory
- Review database `security_events` table
- Verify `.env` configuration
- Test database connection

---

**Created:** January 9, 2026  
**Migration Script:** `/home/nickd/projects/google-stats/scripts/migrate_credentials_to_db.py`  
**Credential Manager:** `/home/nickd/projects/google-stats/src/credential_manager.py`  
**Updated Config:** `/home/nickd/projects/google-stats/src/config.py`
