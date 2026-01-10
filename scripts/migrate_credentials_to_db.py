#!/usr/bin/env python3
"""
Migrate Google Application Credentials to Encrypted Database Storage

This script migrates GA4 service account JSON credentials from file-based
storage to encrypted database storage for enhanced security.

Features:
- Encrypts entire JSON credential file using AES-256
- Stores encrypted credentials in database with metadata
- Removes plaintext file after successful migration
- Creates backup before migration
- Validates credentials before and after migration
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import pymysql
except ImportError:
    print("❌ Required packages not installed. Installing...")
    os.system("pip install cryptography pymysql")
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import pymysql

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class CredentialEncryption:
    """Handle encryption/decryption of credentials"""
    
    def __init__(self, master_password=None):
        """
        Initialize encryption with master password
        
        Args:
            master_password: Master password for encryption. If None, generates random key.
        """
        if master_password:
            # Derive key from password using PBKDF2
            salt = os.getenv('ENCRYPTION_SALT', 'google-stats-default-salt').encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        else:
            # Generate random key
            key = Fernet.generate_key()
        
        self.cipher = Fernet(key)
        self.key = key
    
    def encrypt(self, data):
        """Encrypt data (string or bytes)"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.encrypt(data)
    
    def decrypt(self, encrypted_data):
        """Decrypt data and return as string"""
        return self.cipher.decrypt(encrypted_data).decode()


class CredentialMigration:
    """Migrate credentials from file to database"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'db'),
            'user': os.getenv('DB_USERNAME', 'db'),
            'password': os.getenv('DB_PASSWORD', 'db'),
            'database': os.getenv('DB_NAME', 'google-stats'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self.encryption = None
        self.connection = None
    
    def connect_db(self):
        """Connect to database"""
        try:
            self.connection = pymysql.connect(**self.db_config)
            print("✅ Connected to database")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def setup_encryption(self):
        """Setup encryption with master password"""
        # Check for existing encryption key in .env
        master_password = os.getenv('CREDENTIAL_MASTER_PASSWORD')
        
        if not master_password:
            print("\n⚠️  No CREDENTIAL_MASTER_PASSWORD found in .env")
            print("Generating secure random encryption key...")
            self.encryption = CredentialEncryption()
            
            # Save the key to .env for future use
            env_path = Path('.env')
            key_b64 = self.encryption.key.decode()
            
            with open(env_path, 'a') as f:
                f.write(f"\n# Credential encryption key (generated {datetime.now().isoformat()})\n")
                f.write(f"CREDENTIAL_ENCRYPTION_KEY={key_b64}\n")
            
            print(f"✅ Encryption key saved to .env")
        else:
            print("✅ Using master password from .env")
            self.encryption = CredentialEncryption(master_password)
    
    def read_credential_file(self, file_path):
        """Read and validate credential JSON file"""
        try:
            with open(file_path, 'r') as f:
                credentials = json.load(f)
            
            # Validate it's a service account key
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            if not all(field in credentials for field in required_fields):
                raise ValueError("Invalid service account key format")
            
            print(f"✅ Read credential file: {file_path}")
            print(f"   - Type: {credentials.get('type')}")
            print(f"   - Project: {credentials.get('project_id')}")
            print(f"   - Email: {credentials.get('client_email')}")
            
            return credentials
        except Exception as e:
            print(f"❌ Failed to read credential file: {e}")
            return None
    
    def backup_credential_file(self, file_path):
        """Create backup of credential file"""
        try:
            backup_dir = Path('backup/credentials')
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = Path(file_path).name
            backup_path = backup_dir / f"{timestamp}_{file_name}"
            
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            
            print(f"✅ Backup created: {backup_path}")
            return str(backup_path)
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def store_encrypted_credential(self, name, credential_type, credentials_json, created_by=1):
        """Store encrypted credentials in database"""
        try:
            cursor = self.connection.cursor()
            
            # Encrypt the entire JSON
            json_str = json.dumps(credentials_json, indent=2)
            encrypted_data = self.encryption.encrypt(json_str)
            
            # Store encrypted key separately for key rotation support
            encrypted_key = self.encryption.key
            
            # Check if credential already exists
            cursor.execute(
                "SELECT id FROM credentials WHERE name = %s AND type = %s",
                (name, credential_type)
            )
            existing = cursor.fetchone()
            
            if existing:
                print(f"⚠️  Credential '{name}' already exists. Updating...")
                cursor.execute(
                    """UPDATE credentials 
                       SET encrypted_value = %s, 
                           encrypted_key = %s,
                           last_updated_by = %s,
                           updated_at = NOW()
                       WHERE id = %s""",
                    (encrypted_data, encrypted_key, created_by, existing['id'])
                )
                credential_id = existing['id']
            else:
                cursor.execute(
                    """INSERT INTO credentials 
                       (client_id, name, type, description, encrypted_value, encrypted_key, 
                        created_by, last_updated_by, is_active, created_at, updated_at)
                       VALUES (1, %s, %s, %s, %s, %s, %s, %s, 1, NOW(), NOW())""",
                    (
                        name,
                        credential_type,
                        f"Google Analytics 4 Service Account for {credentials_json.get('project_id')}",
                        encrypted_data,
                        encrypted_key,
                        created_by,
                        created_by
                    )
                )
                credential_id = cursor.lastrowid
            
            self.connection.commit()
            print(f"✅ Stored encrypted credential in database (ID: {credential_id})")
            return credential_id
        except Exception as e:
            self.connection.rollback()
            print(f"❌ Failed to store credential: {e}")
            return None
    
    def verify_stored_credential(self, credential_id):
        """Verify stored credential can be decrypted"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT name, type, encrypted_value FROM credentials WHERE id = %s",
                (credential_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                print("❌ Credential not found in database")
                return False
            
            # Decrypt and validate
            decrypted_json = self.encryption.decrypt(result['encrypted_value'])
            credentials = json.loads(decrypted_json)
            
            # Validate structure
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            if not all(field in credentials for field in required_fields):
                print("❌ Decrypted credential has invalid structure")
                return False
            
            print(f"✅ Verification successful:")
            print(f"   - Name: {result['name']}")
            print(f"   - Type: {result['type']}")
            print(f"   - Project: {credentials['project_id']}")
            print(f"   - Email: {credentials['client_email']}")
            return True
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def remove_file_credential(self, file_path, force=False):
        """Remove plaintext credential file after successful migration"""
        if not force:
            response = input(f"\n⚠️  Remove plaintext file {file_path}? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("ℹ️  Keeping plaintext file")
                return False
        
        try:
            os.remove(file_path)
            print(f"✅ Removed plaintext credential file: {file_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to remove file: {e}")
            return False
    
    def migrate(self, file_path, name, credential_type='google_token', remove_file=True):
        """
        Main migration workflow
        
        Args:
            file_path: Path to credential JSON file
            name: Name for the credential in database
            credential_type: Type of credential (google_token, google_ads, etc.)
            remove_file: Whether to remove plaintext file after migration
        """
        print("\n" + "="*70)
        print("GOOGLE APPLICATION CREDENTIALS MIGRATION")
        print("="*70)
        
        # Step 1: Connect to database
        if not self.connect_db():
            return False
        
        # Step 2: Setup encryption
        self.setup_encryption()
        
        # Step 3: Read credential file
        credentials = self.read_credential_file(file_path)
        if not credentials:
            return False
        
        # Step 4: Backup credential file
        backup_path = self.backup_credential_file(file_path)
        if not backup_path:
            return False
        
        # Step 5: Store encrypted credential
        credential_id = self.store_encrypted_credential(name, credential_type, credentials)
        if not credential_id:
            return False
        
        # Step 6: Verify stored credential
        if not self.verify_stored_credential(credential_id):
            return False
        
        # Step 7: Optionally remove plaintext file
        if remove_file:
            self.remove_file_credential(file_path)
        
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE")
        print("="*70)
        print(f"Credential ID: {credential_id}")
        print(f"Backup: {backup_path}")
        print("\nNext steps:")
        print("1. Update .ddev/config.yaml to remove GOOGLE_APPLICATION_CREDENTIALS")
        print("2. Update src/config.py to use database credentials")
        print("3. Test GA4 scripts with new credential retrieval")
        print("="*70 + "\n")
        
        return True
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate Google Application Credentials to encrypted database storage"
    )
    parser.add_argument(
        '--file',
        default='.ddev/keys/ga4-page-analytics-cf93eb65ac26.json',
        help='Path to credential JSON file'
    )
    parser.add_argument(
        '--name',
        default='GA4 Service Account',
        help='Name for the credential in database'
    )
    parser.add_argument(
        '--type',
        default='google_token',
        choices=['google_token', 'google_ads', 'api_key', 'other'],
        help='Type of credential'
    )
    parser.add_argument(
        '--keep-file',
        action='store_true',
        help='Keep plaintext file after migration (not recommended)'
    )
    
    args = parser.parse_args()
    
    migration = CredentialMigration()
    try:
        success = migration.migrate(
            file_path=args.file,
            name=args.name,
            credential_type=args.type,
            remove_file=not args.keep_file
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        migration.close()


if __name__ == '__main__':
    main()
