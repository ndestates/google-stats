<?php
/**
 * Authentication and User Management System
 * Provides secure session-based authentication with bcrypt password hashing
 */

// Only start session if not in test mode and not already started
if (!defined('TEST_MODE') && session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Test session storage
if (defined('TEST_MODE')) {
    $GLOBALS['test_session'] = [];
}

/**
 * Get session value (works in test mode)
 */
function test_session_get($key, $default = null) {
    if (defined('TEST_MODE')) {
        return $GLOBALS['test_session'][$key] ?? $default;
    }
    return $_SESSION[$key] ?? $default;
}

/**
 * Set session value (works in test mode)
 */
function test_session_set($key, $value) {
    if (defined('TEST_MODE')) {
        $GLOBALS['test_session'][$key] = $value;
    } else {
        $_SESSION[$key] = $value;
    }
}

/**
 * Check if session key is set (works in test mode)
 */
function test_session_isset($key) {
    if (defined('TEST_MODE')) {
        return isset($GLOBALS['test_session'][$key]);
    }
    return isset($_SESSION[$key]);
}

/**
 * Get session ID (works in test mode)
 */
function test_session_id() {
    if (defined('TEST_MODE')) {
        if (session_status() === PHP_SESSION_ACTIVE) {
            return session_id();
        }
        return $GLOBALS['test_session_id'] ?? ($GLOBALS['test_session_id'] = uniqid('test_session_'));
    }
    return session_id();
}

// Include logger for security events
require_once 'logger.php';

// User storage file
if (!defined('USERS_FILE')) define('USERS_FILE', __DIR__ . '/uploads/users.json');
if (!defined('SESSIONS_FILE')) define('SESSIONS_FILE', __DIR__ . '/uploads/sessions.json');

// Security settings
if (!defined('MAX_LOGIN_ATTEMPTS')) define('MAX_LOGIN_ATTEMPTS', 5);
if (!defined('LOCKOUT_TIME')) define('LOCKOUT_TIME', 900); // 15 minutes
if (!defined('SESSION_TIMEOUT')) define('SESSION_TIMEOUT', 3600); // 1 hour
if (!defined('TWO_FACTOR_WINDOW')) define('TWO_FACTOR_WINDOW', 1); // +/- 1 time slice
if (!defined('TWO_FACTOR_PERIOD')) define('TWO_FACTOR_PERIOD', 30); // 30s TOTP window

/**
 * Initialize users file if it doesn't exist
 */
function init_users_file() {
    if (!file_exists(USERS_FILE)) {
        // Create default admin user
        $default_user = [
            'username' => 'admin',
            'password_hash' => password_hash('admin123', PASSWORD_BCRYPT),
            'role' => 'admin',
            'created_at' => date('Y-m-d H:i:s'),
            'last_login' => null,
            'login_attempts' => 0,
            'locked_until' => null,
            'two_factor_enabled' => false,
            'two_factor_secret' => null,
            'two_factor_recovery_codes' => []
        ];
        $users = [$default_user];
        file_put_contents(USERS_FILE, json_encode($users, JSON_PRETTY_PRINT));
        chmod(USERS_FILE, 0600); // Restrictive permissions
    }
}

/**
 * Load users from file
 */
function load_users() {
    if (!file_exists(USERS_FILE)) {
        init_users_file();
    }
        $data = json_decode(file_get_contents(USERS_FILE), true);
        $users = $data ?: [];

        // Backward compatibility: ensure new fields exist
        foreach ($users as &$user) {
            if (!array_key_exists('two_factor_enabled', $user)) {
                $user['two_factor_enabled'] = false;
            }
            if (!array_key_exists('two_factor_secret', $user)) {
                $user['two_factor_secret'] = null;
            }
            if (!array_key_exists('two_factor_recovery_codes', $user)) {
                $user['two_factor_recovery_codes'] = [];
            }
        }

        return $users;

    // Backward compatibility: ensure new fields exist
    foreach ($users as &$user) {
        if (!array_key_exists('two_factor_enabled', $user)) {
            $user['two_factor_enabled'] = false;
        }
        if (!array_key_exists('two_factor_secret', $user)) {
            $user['two_factor_secret'] = null;
        }
        if (!array_key_exists('two_factor_recovery_codes', $user)) {
            $user['two_factor_recovery_codes'] = [];
        }
    }

    return $users;
}

/**
 * Save users to file
 */
function save_users($users) {
    file_put_contents(USERS_FILE, json_encode($users, JSON_PRETTY_PRINT));
}

/**
 * Load sessions from file
 */
function load_sessions() {
    if (!file_exists(SESSIONS_FILE)) {
        return [];
    }
    $data = json_decode(file_get_contents(SESSIONS_FILE), true);
    return $data ?: [];
}

/**
 * Save sessions to file
 */
function save_sessions($sessions) {
    file_put_contents(SESSIONS_FILE, json_encode($sessions, JSON_PRETTY_PRINT));
}

/**
 * Utility: fetch user by username
 */
function &find_user($username, &$users) {
    foreach ($users as &$u) {
        if ($u['username'] === $username) {
            return $u;
        }
    }
    static $null = null;
    return $null;
}

/**
 * Generate a random Base32 secret for TOTP
 */
function generate_totp_secret($length = 16) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $secret = '';
    for ($i = 0; $i < $length; $i++) {
        $secret .= $alphabet[random_int(0, strlen($alphabet) - 1)];
    }
    return $secret;
}

/**
 * Decode Base32 (RFC 4648) without padding
 */
function base32_decode_nopad($b32) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $b32 = strtoupper($b32);
    $bits = '';
    $bytes = '';

    for ($i = 0; $i < strlen($b32); $i++) {
        $val = strpos($alphabet, $b32[$i]);
        if ($val === false) {
            continue;
        }
        $bits .= str_pad(decbin($val), 5, '0', STR_PAD_LEFT);
    }

    for ($i = 0; $i + 8 <= strlen($bits); $i += 8) {
        $bytes .= chr(bindec(substr($bits, $i, 8)));
    }

    return $bytes;
}

/**
 * Generate a TOTP code for a secret
 */
function generate_totp($secret, $time_slice = null) {
    $time_slice = $time_slice ?? floor(time() / TWO_FACTOR_PERIOD);
    $secret_key = base32_decode_nopad($secret);

    $time = pack('N*', 0) . pack('N*', $time_slice);
    $hash = hash_hmac('sha1', $time, $secret_key, true);
    $offset = ord(substr($hash, -1)) & 0x0F;
    $truncated = (ord($hash[$offset]) & 0x7F) << 24 |
                 (ord($hash[$offset + 1]) & 0xFF) << 16 |
                 (ord($hash[$offset + 2]) & 0xFF) << 8 |
                 (ord($hash[$offset + 3]) & 0xFF);
    $code = $truncated % 1000000;
    return str_pad($code, 6, '0', STR_PAD_LEFT);
}

/**
 * Verify a TOTP code within the allowed window
 */
function verify_totp($secret, $code) {
    if (!$secret || !$code) {
        return false;
    }
    $code = preg_replace('/\s+/', '', $code);
    if (!preg_match('/^\d{6}$/', $code)) {
        return false;
    }

    $current_slice = floor(time() / TWO_FACTOR_PERIOD);
    for ($i = -TWO_FACTOR_WINDOW; $i <= TWO_FACTOR_WINDOW; $i++) {
        if (hash_equals(generate_totp($secret, $current_slice + $i), $code)) {
            return true;
        }
    }
    return false;
}

/**
 * Create a login session for a user
 */
function create_user_session($username, $ip = 'unknown') {
    $sessions = load_sessions();
    $session_id = test_session_id();
    $sessions[$session_id] = [
        'user_id' => $username,
        'created_at' => time(),
        'last_activity' => time(),
        'ip' => $ip
    ];
    save_sessions($sessions);
    test_session_set('user_id', $username);
}

/**
 * Mark the user as pending 2FA challenge
 */
function set_pending_two_factor($username, $redirect = 'admin.php') {
    test_session_set('pending_2fa_user', $username);
    test_session_set('pending_2fa_expires', time() + 600);
    test_session_set('pending_2fa_redirect', $redirect);
}

/**
 * Clear any pending 2FA markers
 */
function clear_pending_two_factor() {
    test_session_set('pending_2fa_user', null);
    test_session_set('pending_2fa_expires', null);
    test_session_set('pending_2fa_redirect', null);
}

/**
 * Persist login metadata and create the session record
 */
function finalize_login_success(&$users, $username, $ip = 'unknown') {
    foreach ($users as &$user) {
        if ($user['username'] === $username) {
            $user['login_attempts'] = 0;
            $user['locked_until'] = null;
            $user['last_login'] = date('Y-m-d H:i:s');
            break;
        }
    }
    save_users($users);
    create_user_session($username, $ip);
}

/**
 * Persist 2FA settings for a user
 */
function set_two_factor_settings($username, $enabled, $secret = null) {
    $users = load_users();
    foreach ($users as &$user) {
        if ($user['username'] === $username) {
            $user['two_factor_enabled'] = $enabled;
            $user['two_factor_secret'] = $secret;
            if (!$enabled) {
                $user['two_factor_recovery_codes'] = [];
            }
            save_users($users);
            return true;
        }
    }
    return false;
}

/**
 * Check if user is logged in
 */
function is_logged_in() {
    if (!test_session_isset('user_id')) {
        return false;
    }

    $sessions = load_sessions();
    $session_id = test_session_id();

    if (!isset($sessions[$session_id])) {
        return false;
    }

    $session = $sessions[$session_id];

    // Check session timeout
    if (time() - $session['created_at'] > SESSION_TIMEOUT) {
        logout_user();
        return false;
    }

    // Update session timestamp
    $session['last_activity'] = time();
    $sessions[$session_id] = $session;
    save_sessions($sessions);

    return true;
}

/**
 * Get current logged in user
 */
function get_logged_in_user() {
    if (!is_logged_in()) {
        return null;
    }

    $sessions = load_sessions();
    $session_id = test_session_id();
    $user_id = $sessions[$session_id]['user_id'];

    $users = load_users();
    foreach ($users as $user) {
        if ($user['username'] === $user_id) {
            return $user;
        }
    }

    return null;
}

/**
 * Authenticate user
 */
function authenticate_user($username, $password) {
    global $web_logger;

    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';

    // Check if IP is blocked
    if ($web_logger->is_ip_blocked($ip)) {
        $web_logger->log_security_event('BLOCKED_IP_ACCESS_ATTEMPT', ['username' => $username]);
        return false;
    }

    // Check rate limiting for login attempts
    $rate_limit_key = 'login_' . $ip;
    if (!$web_logger->check_rate_limit($rate_limit_key, 10, 600)) { // 10 attempts per 10 minutes
        return false;
    }

    $users = load_users();
    $user = &find_user($username, $users);

    if (!$user) {
        $web_logger->log_authentication(false, $username);
        return false;
    }

    // Check if account is locked
    if ($user['locked_until'] && time() < $user['locked_until']) {
        $web_logger->log_authentication(false, $username, 'Account locked');
        return false;
    }

    // Verify password
    if (!password_verify($password, $user['password_hash'])) {
        $user['login_attempts']++;
        if ($user['login_attempts'] >= MAX_LOGIN_ATTEMPTS) {
            $user['locked_until'] = time() + LOCKOUT_TIME;
            $web_logger->log_security_event('ACCOUNT_LOCKED', ['username' => $username, 'attempts' => $user['login_attempts']]);
        } else {
            $web_logger->log_authentication(false, $username);
        }
        save_users($users);
        return false;
    }

    // Password validated
    $user['login_attempts'] = 0;
    $user['locked_until'] = null;
    save_users($users);

    // If 2FA is enabled, park the session until OTP is confirmed
    if (!empty($user['two_factor_enabled']) && !empty($user['two_factor_secret'])) {
        set_pending_two_factor($username, $_GET['redirect'] ?? 'admin.php');
        $web_logger->log_authentication(true, $username, '2FA_REQUIRED');
        return '2fa_required';
    }

    finalize_login_success($users, $username, $ip);
    $web_logger->log_authentication(true, $username, 'PASSWORD_ONLY');
    return true;
}

/**
 * Logout user
 */
function logout_user() {
    $sessions = load_sessions();
    $session_id = test_session_id();

    if (isset($sessions[$session_id])) {
        unset($sessions[$session_id]);
        save_sessions($sessions);
    }

    clear_pending_two_factor();

    // Clear test session
    if (defined('TEST_MODE')) {
        $GLOBALS['test_session'] = [];
        unset($GLOBALS['test_session_id']);
    } else if (session_status() === PHP_SESSION_ACTIVE) {
        session_destroy();
        session_start();
    }
}

/**
 * Add new user
 */
function add_user($username, $password, $role = 'admin') {
    $users = load_users();

    // Check if user exists
    foreach ($users as $user) {
        if ($user['username'] === $username) {
            return false;
        }
    }

    $new_user = [
        'username' => $username,
        'password_hash' => password_hash($password, PASSWORD_BCRYPT),
        'role' => $role,
        'created_at' => date('Y-m-d H:i:s'),
        'last_login' => null,
        'login_attempts' => 0,
        'locked_until' => null,
        'two_factor_enabled' => false,
        'two_factor_secret' => null,
        'two_factor_recovery_codes' => []
    ];

    $users[] = $new_user;
    save_users($users);

    global $web_logger;
    $web_logger->info("New user created", ['username' => $username, 'role' => $role]);

    return true;
}

/**
 * Delete user
 */
function delete_user($username) {
    $users = load_users();
    $found = false;

    foreach ($users as $key => $user) {
        if ($user['username'] === $username) {
            unset($users[$key]);
            $found = true;
            break;
        }
    }

    if ($found) {
        save_users(array_values($users));
        global $web_logger;
        $web_logger->info("User deleted", ['username' => $username]);
    }

    return $found;
}

/**
 * Change user password
 */
function change_password($username, $new_password) {
    $users = load_users();

    foreach ($users as &$user) {
        if ($user['username'] === $username) {
            $user['password_hash'] = password_hash($new_password, PASSWORD_BCRYPT);
            save_users($users);
            global $web_logger;
            $web_logger->info("Password changed", ['username' => $username]);
            return true;
        }
    }

    return false;
}

/**
 * CSRF PROTECTION FUNCTIONS
 */

/**
 * Generate a new CSRF token
 */
function generate_csrf_token() {
    $token = bin2hex(random_bytes(32));
    test_session_set('csrf_token', $token);
    test_session_set('csrf_token_time', time());
    return $token;
}

/**
 * Get current CSRF token (generate if not exists)
 */
function get_csrf_token() {
    $token = test_session_get('csrf_token');
    
    // Generate token if it doesn't exist
    if (!$token) {
        $token = generate_csrf_token();
    }

    return $token;
}

/**
 * Validate CSRF token from POST request
 */
function validate_csrf_token() {
    $token = $_POST['csrf_token'] ?? '';
    
    if (empty($token)) {
        return false;
    }
    
    // Get current session token
    $session_token = test_session_get('csrf_token');
    $token_time = test_session_get('csrf_token_time', 0);
    
    // Check if posted token matches current session token
    if (!empty($session_token) && hash_equals($session_token, $token)) {
        // Check if token is older than 1 hour and regenerate if needed
        if ((time() - $token_time) > 3600) {
            generate_csrf_token();
        }
        // Don't regenerate after every validation to avoid breaking concurrent requests
        return true;
    }
    
    return false;
}

/**
 * Get CSRF token HTML input field
 */
function csrf_token_field() {
    $token = get_csrf_token();
    return '<input type="hidden" name="csrf_token" value="' . htmlspecialchars($token) . '">';
}

/**
 * Handle authentication actions
 */
if (isset($_GET['action'])) {
    switch ($_GET['action']) {
        case 'login':
            if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                // Validate CSRF token
                if (!validate_csrf_token()) {
                    global $web_logger;
                    $web_logger->log_security_event('CSRF_TOKEN_INVALID', ['action' => 'login']);
                    header('Location: admin.php?error=csrf_invalid');
                    exit;
                }

                $username = trim($_POST['username'] ?? '');
                $password = $_POST['password'] ?? '';

                $result = authenticate_user($username, $password);
                if ($result === true) {
                    // Regenerate CSRF token after successful login for security
                    generate_csrf_token();
                    $redirect = $_GET['redirect'] ?? 'admin.php';
                    header('Location: ' . $redirect);
                    exit;
                } elseif ($result === '2fa_required') {
                    // Preserve intended redirect for after 2FA success
                    $redirect = $_GET['redirect'] ?? 'admin.php';
                    test_session_set('pending_2fa_redirect', $redirect);
                    header('Location: twofactor.php');
                    exit;
                } else {
                    $error = isset($_SESSION['login_error']) ? $_SESSION['login_error'] : 'invalid';
                    $redirect = $_GET['redirect'] ?? 'admin.php';
                    header('Location: ' . $redirect . '?error=' . $error);
                    exit;
                }
            }
            break;

        case 'logout':
            logout_user();
            header('Location: admin.php');
            exit;

        case 'add_user':
            if (is_logged_in() && $_SERVER['REQUEST_METHOD'] === 'POST') {
                // Validate CSRF token
                if (!validate_csrf_token()) {
                    global $web_logger;
                    $web_logger->log_security_event('CSRF_TOKEN_INVALID', ['action' => 'add_user']);
                    header('Location: admin.php?error=csrf_invalid');
                    exit;
                }

                $new_username = trim($_POST['new_username'] ?? '');
                $new_password = $_POST['new_password'] ?? '';
                $confirm_password = $_POST['confirm_password'] ?? '';

                if ($new_password !== $confirm_password) {
                    header('Location: admin.php?error=password_mismatch');
                    exit;
                }

                if (add_user($new_username, $new_password)) {
                    header('Location: admin.php?success=user_added');
                    exit;
                } else {
                    header('Location: admin.php?error=user_exists');
                    exit;
                }
            }
            break;

        case 'delete_user':
            if (is_logged_in() && $_SERVER['REQUEST_METHOD'] === 'POST') {
                // Validate CSRF token
                if (!validate_csrf_token()) {
                    global $web_logger;
                    $web_logger->log_security_event('CSRF_TOKEN_INVALID', ['action' => 'delete_user']);
                    header('Location: admin.php?error=csrf_invalid');
                    exit;
                }

                $delete_username = $_POST['delete_username'] ?? '';
                $current_user = get_logged_in_user();

                if ($delete_username !== $current_user['username']) {
                    delete_user($delete_username);
                    header('Location: admin.php?success=user_deleted');
                    exit;
                } else {
                    header('Location: admin.php?error=cannot_delete_self');
                    exit;
                }
            }
            break;

        case 'change_password':
            if (is_logged_in() && $_SERVER['REQUEST_METHOD'] === 'POST') {
                // Validate CSRF token
                if (!validate_csrf_token()) {
                    global $web_logger;
                    $web_logger->log_security_event('CSRF_TOKEN_INVALID', ['action' => 'change_password']);
                    header('Location: admin.php?error=csrf_invalid');
                    exit;
                }

                $current_password = $_POST['current_password'] ?? '';
                $new_password = $_POST['new_password'] ?? '';
                $confirm_password = $_POST['confirm_password'] ?? '';

                $current_user = get_logged_in_user();
                if (password_verify($current_password, $current_user['password_hash'])) {
                    if ($new_password === $confirm_password) {
                        change_password($current_user['username'], $new_password);
                        header('Location: admin.php?success=password_changed');
                        exit;
                    } else {
                        header('Location: admin.php?error=password_mismatch');
                        exit;
                    }
                } else {
                    header('Location: admin.php?error=wrong_current_password');
                    exit;
                }
            }
            break;

        case 'enable_2fa':
            if (is_logged_in() && $_SERVER['REQUEST_METHOD'] === 'POST') {
                if (!validate_csrf_token()) {
                    header('Location: admin.php?error=csrf_invalid');
                    exit;
                }

                $current_user = get_logged_in_user();
                $secret = test_session_get('two_factor_setup_secret');
                $code = $_POST['two_factor_code'] ?? '';

                if (!$secret) {
                    header('Location: admin.php?error=twofa_missing_secret');
                    exit;
                }

                if (!verify_totp($secret, $code)) {
                    header('Location: admin.php?error=twofa_invalid_code');
                    exit;
                }

                set_two_factor_settings($current_user['username'], true, $secret);
                test_session_set('two_factor_setup_secret', null);
                header('Location: admin.php?success=twofa_enabled');
                exit;
            }
            break;

        case 'disable_2fa':
            if (is_logged_in() && $_SERVER['REQUEST_METHOD'] === 'POST') {
                if (!validate_csrf_token()) {
                    header('Location: admin.php?error=csrf_invalid');
                    exit;
                }

                $current_user = get_logged_in_user();
                set_two_factor_settings($current_user['username'], false, null);
                test_session_set('two_factor_setup_secret', null);
                header('Location: admin.php?success=twofa_disabled');
                exit;
            }
            break;

        case 'regenerate_2fa_secret':
            if (is_logged_in()) {
                test_session_set('two_factor_setup_secret', generate_totp_secret());
                header('Location: admin.php?success=twofa_secret_regenerated');
                exit;
            }
            break;
    }
}

// Initialize users file on first load
init_users_file();
?>