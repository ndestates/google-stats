<?php
/**
 * Encrypted Credentials Management System
 * Provides secure storage and retrieval of Google API credentials
 */

if (!defined('CREDENTIALS_FILE')) define('CREDENTIALS_FILE', __DIR__ . '/uploads/credentials.enc');
if (!defined('MASTER_KEY_ENV')) define('MASTER_KEY_ENV', 'CREDENTIALS_MASTER_KEY');

// Generate a random master key if not set
function generate_master_key() {
    return bin2hex(random_bytes(32)); // 256-bit key
}

// Get master key from environment or generate if not exists
function get_master_key() {
    $key = getenv(MASTER_KEY_ENV);
    if (!$key) {
        $key_file = __DIR__ . '/uploads/master_key.txt';
        if (file_exists($key_file)) {
            $key = trim(file_get_contents($key_file));
        } else {
            $key = generate_master_key();
            file_put_contents($key_file, $key);
            chmod($key_file, 0600);
        }
    }
    return $key;
}

// Encrypt data using AES-256-CBC
function encrypt_data($data, $key) {
    $iv = random_bytes(16); // AES block size
    $encrypted = openssl_encrypt($data, 'AES-256-CBC', $key, 0, $iv);
    return base64_encode($iv . $encrypted);
}

// Decrypt data using AES-256-CBC
function decrypt_data($encrypted_data, $key) {
    $data = base64_decode($encrypted_data);
    $iv = substr($data, 0, 16);
    $encrypted = substr($data, 16);
    return openssl_decrypt($encrypted, 'AES-256-CBC', $key, 0, $iv);
}

// Load encrypted credentials
function load_credentials() {
    if (!file_exists(CREDENTIALS_FILE)) {
        return [];
    }

    $key = get_master_key();
    $encrypted = file_get_contents(CREDENTIALS_FILE);
    $decrypted = decrypt_data($encrypted, $key);

    if ($decrypted === false) {
        throw new Exception('Failed to decrypt credentials');
    }

    return json_decode($decrypted, true) ?: [];
}

// Save encrypted credentials
function save_credentials($credentials) {
    $key = get_master_key();
    $data = json_encode($credentials);
    $encrypted = encrypt_data($data, $key);

    if (file_put_contents(CREDENTIALS_FILE, $encrypted) === false) {
        throw new Exception('Failed to save encrypted credentials');
    }

    chmod(CREDENTIALS_FILE, 0600);
}

// Update a specific credential
function update_credential($key, $value) {
    $credentials = load_credentials();
    $credentials[$key] = $value;
    save_credentials($credentials);

    global $web_logger;
    $web_logger->info("Credential updated", ['key' => $key]);
}

// Get a specific credential
function get_credential($key) {
    $credentials = load_credentials();
    return $credentials[$key] ?? null;
}

// Get all credentials as environment variables
function load_credentials_to_env() {
    $credentials = load_credentials();
    foreach ($credentials as $key => $value) {
        putenv("$key=$value");
        $_ENV[$key] = $value;
        $_SERVER[$key] = $value;
    }
}

// Import credentials from .env file (for migration)
function import_from_env($env_path) {
    if (!file_exists($env_path)) {
        return false;
    }

    $lines = file($env_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $credentials = [];

    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) {
            continue;
        }

        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);

        // Only import Google-related credentials
        if (strpos($name, 'GOOGLE_') === 0 || strpos($name, 'GA4_') === 0 || strpos($name, 'GSC_') === 0) {
            $credentials[$name] = $value;
        }
    }

    if (!empty($credentials)) {
        save_credentials($credentials);
        global $web_logger;
        $web_logger->info("Credentials imported from .env file", ['count' => count($credentials)]);
        return true;
    }

    return false;
}

// Validate Google Ads credentials format
function validate_google_ads_credentials($credentials) {
    $required = [
        'GOOGLE_ADS_CUSTOMER_ID',
        'GOOGLE_ADS_CLIENT_ID',
        'GOOGLE_ADS_CLIENT_SECRET',
        'GOOGLE_ADS_REFRESH_TOKEN',
        'GOOGLE_ADS_DEVELOPER_TOKEN'
    ];

    foreach ($required as $key) {
        if (empty($credentials[$key])) {
            return false;
        }
    }

    // Basic format validation
    if (!preg_match('/^\d{10}$/', $credentials['GOOGLE_ADS_CUSTOMER_ID'])) {
        return false;
    }

    if (!preg_match('/\.googleusercontent\.com$/', $credentials['GOOGLE_ADS_CLIENT_ID'])) {
        return false;
    }

    return true;
}

// Validate GA4 credentials format
function validate_ga4_credentials($credentials) {
    $required = ['GA4_PROPERTY_ID', 'GA4_KEY_PATH'];

    foreach ($required as $key) {
        if (empty($credentials[$key])) {
            return false;
        }
    }

    if (!preg_match('/^\d+$/', $credentials['GA4_PROPERTY_ID'])) {
        return false;
    }

    return true;
}

// Initialize credentials file if it doesn't exist
function init_credentials() {
    if (!file_exists(CREDENTIALS_FILE)) {
        save_credentials([]);
    }
}

// Call init on include
init_credentials();
?>