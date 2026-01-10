"""
Database Credential Manager for Google Stats

Securely retrieves encrypted credentials from database instead of file system.
Supports caching and temporary file creation for Google client libraries.
"""

import os
import json
import base64
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from cryptography.fernet import Fernet
    import pymysql
except ImportError:
    raise ImportError(
        "Required packages not installed. Run: pip install cryptography pymysql"
    )


class DatabaseCredentialManager:
    """Manage encrypted credentials stored in database"""
    
    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """
        Initialize credential manager
        
        Args:
            db_config: Database connection config. If None, reads from environment.
        """
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'db'),
            'user': os.getenv('DB_USERNAME', 'db'),
            'password': os.getenv('DB_PASSWORD', 'db'),
            'database': os.getenv('DB_NAME', 'google-stats'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
        self._connection = None
        self._credential_cache = {}
        self._temp_files = {}
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
    
    def connect(self):
        """Connect to database"""
        if not self._connection:
            self._connection = pymysql.connect(**self.db_config)
    
    def get_credential(self, name: str, credential_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve and decrypt credential from database
        
        Args:
            name: Credential name
            credential_type: Optional credential type filter
        
        Returns:
            Decrypted credential as dict
        
        Raises:
            ValueError: If credential not found or decryption fails
        """
        # Check cache first
        cache_key = f"{name}:{credential_type or 'any'}"
        if cache_key in self._credential_cache:
            return self._credential_cache[cache_key]
        
        self.connect()
        
        try:
            cursor = self._connection.cursor()
            
            # Query credential
            if credential_type:
                cursor.execute(
                    """SELECT id, name, type, encrypted_value, encrypted_key 
                       FROM credentials 
                       WHERE name = %s AND type = %s AND is_active = 1
                       ORDER BY updated_at DESC LIMIT 1""",
                    (name, credential_type)
                )
            else:
                cursor.execute(
                    """SELECT id, name, type, encrypted_value, encrypted_key 
                       FROM credentials 
                       WHERE name = %s AND is_active = 1
                       ORDER BY updated_at DESC LIMIT 1""",
                    (name,)
                )
            
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Credential '{name}' not found in database")
            
            # Decrypt using stored key or environment key
            encryption_key = result['encrypted_key']
            if not encryption_key:
                # Fall back to environment key
                encryption_key = os.getenv('CREDENTIAL_ENCRYPTION_KEY')
                if not encryption_key:
                    raise ValueError("No encryption key available")
                encryption_key = encryption_key.encode()
            
            cipher = Fernet(encryption_key)
            decrypted_json = cipher.decrypt(result['encrypted_value']).decode()
            credential_data = json.loads(decrypted_json)
            
            # Cache the decrypted credential
            self._credential_cache[cache_key] = credential_data
            
            return credential_data
        except Exception as e:
            raise ValueError(f"Failed to retrieve credential: {e}")
    
    def get_credential_as_temp_file(self, name: str, credential_type: Optional[str] = None) -> str:
        """
        Get credential as temporary JSON file
        
        Useful for Google client libraries that require file path.
        The temp file is automatically cleaned up on manager cleanup.
        
        Args:
            name: Credential name
            credential_type: Optional credential type filter
        
        Returns:
            Path to temporary credential file
        """
        cache_key = f"{name}:{credential_type or 'any'}"
        
        # Check if we already created a temp file
        if cache_key in self._temp_files:
            return self._temp_files[cache_key]
        
        # Get credential
        credential_data = self.get_credential(name, credential_type)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            prefix='gs_cred_',
            delete=False
        )
        
        try:
            json.dump(credential_data, temp_file, indent=2)
            temp_file.close()
            
            # Store for cleanup
            self._temp_files[cache_key] = temp_file.name
            
            return temp_file.name
        except Exception as e:
            # Clean up on error
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise ValueError(f"Failed to create temporary credential file: {e}")
    
    def cleanup(self):
        """Clean up temporary files and close connection"""
        # Remove temporary credential files
        for temp_file in self._temp_files.values():
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception:
                pass
        
        self._temp_files.clear()
        self._credential_cache.clear()
        
        # Close database connection
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def list_credentials(self, credential_type: Optional[str] = None) -> list:
        """
        List available credentials
        
        Args:
            credential_type: Optional type filter
        
        Returns:
            List of credential metadata dicts
        """
        self.connect()
        
        try:
            cursor = self._connection.cursor()
            
            if credential_type:
                cursor.execute(
                    """SELECT id, name, type, description, created_at, updated_at 
                       FROM credentials 
                       WHERE type = %s AND is_active = 1
                       ORDER BY name""",
                    (credential_type,)
                )
            else:
                cursor.execute(
                    """SELECT id, name, type, description, created_at, updated_at 
                       FROM credentials 
                       WHERE is_active = 1
                       ORDER BY name"""
                )
            
            return cursor.fetchall()
        except Exception as e:
            raise ValueError(f"Failed to list credentials: {e}")


# Convenience function for backward compatibility
def get_google_application_credentials(credential_name: str = "GA4 Service Account") -> str:
    """
    Get Google Application Credentials path
    
    This function provides backward compatibility with code expecting a file path.
    It retrieves the credential from database and creates a temporary file.
    
    Args:
        credential_name: Name of credential in database
    
    Returns:
        Path to temporary credential file
    
    Example:
        >>> os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = get_google_application_credentials()
    """
    manager = DatabaseCredentialManager()
    try:
        return manager.get_credential_as_temp_file(credential_name, 'google_token')
    except Exception as e:
        # Fall back to file-based credential if database retrieval fails
        fallback_path = os.getenv('GA4_KEY_PATH')
        if fallback_path and os.path.exists(fallback_path):
            return fallback_path
        raise ValueError(f"Failed to get credentials: {e}")


if __name__ == '__main__':
    # Test credential retrieval
    print("Testing Database Credential Manager...")
    
    with DatabaseCredentialManager() as manager:
        print("\nAvailable credentials:")
        for cred in manager.list_credentials():
            print(f"  - {cred['name']} ({cred['type']})")
        
        print("\nTrying to retrieve GA4 Service Account...")
        try:
            cred_path = manager.get_credential_as_temp_file("GA4 Service Account", "google_token")
            print(f"✅ Credential retrieved: {cred_path}")
            
            # Verify it's valid JSON
            with open(cred_path, 'r') as f:
                data = json.load(f)
                print(f"   Project: {data.get('project_id')}")
                print(f"   Email: {data.get('client_email')}")
        except Exception as e:
            print(f"❌ Failed: {e}")
