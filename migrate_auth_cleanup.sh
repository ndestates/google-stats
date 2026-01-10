#!/bin/bash
# Security Cleanup Script - Remove File-Based Authentication
# This script removes the old file-based authentication system for security reasons
# The new database-backed authentication system is now in place

echo "🔒 Google Stats Authentication System Migration"
echo "=============================================="
echo ""
echo "Backing up old file-based auth files..."

# Create backup directory
BACKUP_DIR="backup/old-auth-$(date +%Y%m%d%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup old auth files
if [ -f "web/uploads/users.json" ]; then
    cp web/uploads/users.json "$BACKUP_DIR/"
    echo "✓ Backed up users.json"
fi

if [ -f "web/uploads/sessions.json" ]; then
    cp web/uploads/sessions.json "$BACKUP_DIR/"
    echo "✓ Backed up sessions.json"
fi

# Backup old auth.php if it exists
if [ -f "web/auth.php" ]; then
    cp web/auth.php "$BACKUP_DIR/auth.php.old"
    echo "✓ Backed up old auth.php"
fi

echo ""
echo "Removing old file-based authentication files..."

# Remove old JSON auth files
if [ -f "web/uploads/users.json" ]; then
    rm web/uploads/users.json
    echo "✓ Removed users.json"
fi

if [ -f "web/uploads/sessions.json" ]; then
    rm web/uploads/sessions.json
    echo "✓ Removed sessions.json"
fi

echo ""
echo "✅ Migration Complete!"
echo ""
echo "Summary:"
echo "- Old authentication files backed up to: $BACKUP_DIR"
echo "- File-based authentication removed"
echo "- New database-backed authentication is active"
echo ""
echo "Next steps:"
echo "1. Test login at https://google-stats.ddev.site/login.php"
echo "2. Default credentials: admin / admin123"
echo "3. Change the default password immediately!"
echo ""
echo "⚠️  SECURITY NOTE: The backup contains password hashes."
echo "    Store it securely and delete after verification."
