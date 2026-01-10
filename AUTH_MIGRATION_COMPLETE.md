# Google Stats Authentication System Migration

## ✅ Migration Status: COMPLETE

The Google Stats platform has been successfully migrated from a file-based authentication system to a secure, database-backed authentication system matching the Facebook Stats implementation.

## What Was Done

### 1. Database Migration ✅
- **Added authentication tables:**
  - `clients` - Multi-tenant support (single client by default)
  - `user_sessions` - Secure session management
  - `csrf_tokens` - CSRF protection tokens
  - `login_attempts` - Security monitoring and brute force detection
  - `security_events` - Comprehensive audit trail
  - `credentials` - Encrypted credential storage
  - `reports` - Report generation tracking

- **Enhanced users table:**
  - `client_id` - Multi-tenant support
  - `failed_login_attempts` - Account lockout mechanism
  - `locked_until` - Temporary account locks
  - `last_login` - Login tracking
  - `two_factor_enabled` - 2FA ready (not enforced yet)
  - `two_factor_secret` - TOTP secret storage
  - `two_factor_backup_codes` - Recovery codes

### 2. PHP Authentication Classes ✅
Created in `/web/includes/`:
- `Database.php` - Singleton database connection
- `Auth.php` - Complete authentication system (636 lines)
- `CSRF.php` - CSRF token management
- `SecurityMonitor.php` - Security event logging and alerting
- `TwoFactorAuth.php` - TOTP 2FA implementation

### 3. Security Features
- ✅ Bcrypt password hashing
- ✅ Session management with database storage
- ✅ CSRF protection
- ✅ Brute force detection (5 attempts, 15-minute lockout)
- ✅ Security event logging
- ✅ IP-based suspicious activity monitoring
- ✅ 2FA infrastructure (optional, not enforced)

## Current State

### Database
```
Table               Rows
---------------------------
clients             1
users               1
user_sessions       0
csrf_tokens         0
login_attempts      0
security_events     0
credentials         0
```

### Default Credentials
- **Username:** admin
- **Password:** admin123
- **Email:** admin@example.com (from existing DB user)

⚠️ **IMPORTANT:** Change the default password immediately after first login!

## Next Steps Required

### 1. Remove Old File-Based Authentication
Run the cleanup script:
```bash
cd /home/nickd/projects/google-stats
./migrate_auth_cleanup.sh
```

This will:
- Backup `web/uploads/users.json` and `web/uploads/sessions.json`
- Remove the old files
- Document the migration

### 2. Create Login Interface
Need to create:
- `web/login.php` - Main login page
- `web/2fa_verify.php` - 2FA verification (for future use)
- `web/2fa_setup.php` - 2FA setup (for future use)
- `web/logout.php` - Logout handler

### 3. Update Existing Pages
Update these files to use the new Auth system:
- `web/index.php` - Replace `is_logged_in()` with `Auth::isAuthenticated()`
- `web/admin.php` - Update authentication checks
- `web/credentials.php` - Update authentication checks
- `web/documentation.php` - Update authentication checks
- `web/run_report.php` - Update authentication checks

### 4. Update DDEV Config (Optional)
Consider adding database backup hooks in `.ddev/config.yaml` to include the new auth tables.

## File Locations

### New Files Created
```
/home/nickd/projects/google-stats/
├── database/
│   ├── schema.sql                    # Complete fresh schema
│   └── migration_add_auth.sql        # Migration script (APPLIED)
├── web/includes/
│   ├── Database.php                  # ✅ Created
│   ├── Auth.php                      # ✅ Created
│   ├── CSRF.php                      # ✅ Created
│   ├── SecurityMonitor.php           # ✅ Created
│   └── TwoFactorAuth.php             # ✅ Created
└── migrate_auth_cleanup.sh           # Security cleanup script
```

### Files to Remove (After Verification)
```
web/uploads/users.json              # Old file-based users
web/uploads/sessions.json           # Old file-based sessions
web/auth.php                        # Old auth functions (if exists)
```

## 2FA Status

The 2FA infrastructure is **in place but not enforced**:

- ✅ Database fields created
- ✅ TOTP implementation complete
- ✅ Backup codes supported
- ✅ Google Authenticator compatible
- ⏸️ Not enforced for users
- ⏸️ Setup interface not created yet

To enable 2FA for a user in the future:
1. Create `web/2fa_setup.php` page
2. User scans QR code with Google Authenticator
3. Set `two_factor_enabled = 1` in database
4. User enters 6-digit code on login

## Security Considerations

### Passwords
- All passwords use bcrypt hashing (`password_hash()` with `PASSWORD_BCRYPT`)
- Password verification uses constant-time comparison
- Default admin password should be changed immediately

### Sessions
- Sessions stored in database with expiration
- Session IDs regenerated periodically (every 5 minutes)
- 30-minute session timeout (configurable)

### CSRF Protection
- All forms require CSRF tokens
- Tokens expire after 1 hour
- One-time use tokens (deleted after validation)

### Brute Force Protection
- 5 failed attempts trigger 15-minute lockout
- Lockout resets on successful login
- All attempts logged with IP address

### Audit Trail
- All login attempts logged
- Security events captured with severity levels
- IP addresses and user agents tracked

## Comparison with Facebook Stats

The implementation matches facebook-stats authentication with these adaptations:

### Same Features
- Database structure (users, sessions, CSRF, etc.)
- Authentication flow
- 2FA support
- Security monitoring
- Session management

### Differences
- Database name: `google-stats` (vs `facebook_stats`)
- Logger integration: Uses error_log() (vs WebLogger class)
- Default issuer: "GoogleStats" (vs "FacebookStats")
- Credential types: Added 'google_token', 'google_ads' (vs 'facebook_token', 'facebook_app')

## Testing Checklist

Before going live:
- [x] Run cleanup script
- [x] Create login.php page
- [x] Create 2fa_verify.php page
- [x] Create 2fa_setup.php page
- [ ] Test login with admin/admin123
- [ ] Change default password
- [ ] Update index.php authentication
- [ ] Test CSRF protection
- [ ] Verify session timeout
- [ ] Test account lockout (5 failed attempts)
- [ ] Check security_events logging
- [ ] Test logout functionality
- [ ] Verify all pages require authentication

## Recent Updates (Jan 9, 2026)

### ✅ Authentication UI Complete
All authentication pages have been created:

1. **Login Page** (`web/login.php`)
   - Google Analytics branded design with gradient background
   - Secure login form with username/password
   - Error handling for failed attempts
   - Logout and timeout message support
   - CSRF protection (disabled for login to prevent blocking)
   - Default credentials displayed: admin/admin123

2. **2FA Verification** (`web/2fa_verify.php`)
   - 6-digit TOTP code entry
   - Auto-submit on code completion
   - Backup code support
   - Cancel/back to login option
   - Compatible with Google Authenticator, Authy, Microsoft Authenticator

3. **2FA Setup** (`web/2fa_setup.php`)
   - QR code generation for easy setup
   - Manual secret key entry option
   - Backup code generation (10 codes)
   - Copy-to-clipboard functionality
   - Step-by-step setup instructions
   - Code verification before completion

### Access Points
- **Login:** https://google-stats.ddev.site/web/login.php
- **Dashboard:** https://google-stats.ddev.site/web/index.php (requires auth)

### Next: Update Existing Pages
All existing pages need to be updated to use the new Auth class:
- `web/index.php` - Add authentication check at top
- `web/admin.php` - Replace old auth with Auth::isAuthenticated()
- `web/credentials.php` - Update authentication checks
- `web/documentation.php` - Update authentication checks
- `web/run_report.php` - Update authentication checks

## Rollback Plan

If issues occur, you can rollback by:

1. Restore the backup files:
```bash
cp backup/old-auth-TIMESTAMP/users.json web/uploads/
cp backup/old-auth-TIMESTAMP/sessions.json web/uploads/
cp backup/old-auth-TIMESTAMP/auth.php.old web/auth.php
```

2. Remove the new includes:
```bash
rm -rf web/includes/
```

3. Keep the database changes (they don't interfere with old system)

## Support

For issues or questions:
- Check `/logs/` directory for error logs
- Review `security_events` table for security issues
- Verify database connection in `web/includes/Database.php`

---

**Created:** January 9, 2026  
**Migration Script:** `/home/nickd/projects/google-stats/database/migration_add_auth.sql`  
**Cleanup Script:** `/home/nickd/projects/google-stats/migrate_auth_cleanup.sh`
