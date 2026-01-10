<?php
/**
 * Secure Authentication and Session Management Class
 * Implements industry-standard security practices
 */

require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/SecurityMonitor.php';

class Auth {
    private $db;
    private $session_lifetime = 1800; // 30 minutes
    private $max_login_attempts = 5;
    private $lockout_duration = 900; // 15 minutes
    private $csrf_token_lifetime = 3600; // 1 hour
    private $security_monitor;

    public function __construct() {
        $this->db = Database::getInstance()->getConnection();
        $this->security_monitor = new SecurityMonitor();
        $this->initSecureSession();
    }

    /**
     * Initialize secure session settings
     */
    private function initSecureSession() {
        // Set secure session cookie parameters (only if no session is active)
        if (session_status() === PHP_SESSION_NONE) {
            session_set_cookie_params([
                'lifetime' => 0, // Session cookie
                'path' => '/',
                'domain' => $_SERVER['HTTP_HOST'] ?? '',
                'secure' => isset($_SERVER['HTTPS']),
                'httponly' => true,
                'samesite' => 'Strict'
            ]);
        }

        // Start session if not already started
        if (session_status() === PHP_SESSION_NONE) {
            session_start();
        }

        // Regenerate session ID periodically for security
        if (!isset($_SESSION['created'])) {
            $_SESSION['created'] = time();
        } elseif (time() - $_SESSION['created'] > 300) { // Regenerate every 5 minutes
            $old_session_id = $_SESSION['session_id'] ?? null;

            if ($old_session_id) {
                // Generate new session ID
                session_regenerate_id(true);
                $new_session_id = session_id();

                try {
                    // Update session_id in database
                    $stmt = $this->db->prepare("UPDATE user_sessions SET id = ? WHERE id = ?");
                    $stmt->execute([$new_session_id, $old_session_id]);

                    // Update CSRF tokens to use new session_id
                    $stmt = $this->db->prepare("UPDATE csrf_tokens SET session_id = ? WHERE session_id = ?");
                    $stmt->execute([$new_session_id, $old_session_id]);

                    $_SESSION['session_id'] = $new_session_id;
                    $_SESSION['created'] = time();
                } catch (Exception $e) {
                    // If database update fails, regenerate session anyway for security
                    $_SESSION['session_id'] = session_id();
                    $_SESSION['created'] = time();
                    error_log("Session regeneration database error: " . $e->getMessage());
                }
            } else {
                // No old session ID, just update timestamp
                $_SESSION['created'] = time();
            }
        }
    }

    /**
     * Authenticate user with secure password verification
     */
    public function login($username, $password, $ip_address, $user_agent) {
        // Validate input to prevent injection
        $username = trim($username);
        $password = trim($password);

        if (empty($username) || empty($password)) {
            $this->security_monitor->logSecurityEvent('invalid_login_input', [
                'username_provided' => !empty($username),
                'password_provided' => !empty($password)
            ], 'warning');
            throw new Exception("Username and password are required.");
        }

        if (strlen($username) > 50 || strlen($password) > 255) {
            $this->security_monitor->logSecurityEvent('suspicious_input_length', [
                'username_length' => strlen($username),
                'password_length' => strlen($password)
            ], 'warning');
            throw new Exception("Invalid input length.");
        }

        // Log the attempt
        $this->logLoginAttempt($username, $ip_address, $user_agent, false);

        // Check if account is locked
        if ($this->isAccountLocked($username)) {
            $this->security_monitor->logSecurityEvent('account_locked_attempt', [
                'username' => $username,
                'ip' => $ip_address
            ], 'warning');
            throw new Exception("Account is temporarily locked due to too many failed login attempts.");
        }

        // Get user from database
        $stmt = $this->db->prepare("SELECT id, client_id, username, password_hash, role, is_active, failed_login_attempts, two_factor_enabled FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $user = $stmt->fetch();

        if (!$user || !$user['is_active']) {
            $this->incrementFailedAttempts($username);
            $this->security_monitor->logSecurityEvent('invalid_credentials', [
                'username' => $username,
                'user_exists' => $user !== false,
                'user_active' => $user ? $user['is_active'] : false
            ], 'info');
            throw new Exception("Invalid username or password.");
        }

        // Verify password
        if (!password_verify($password, $user['password_hash'])) {
            $this->incrementFailedAttempts($username);
            $this->security_monitor->logSecurityEvent('password_verification_failed', [
                'username' => $username
            ], 'info');
            throw new Exception("Invalid username or password.");
        }

        // Reset failed attempts on successful login
        $this->resetFailedAttempts($user['id']);

        // 2FA is now mandatory for all users
        if ($user['two_factor_enabled']) {
            // Store temporary session for 2FA verification
            $this->createTempSessionFor2FA($user, $ip_address, $user_agent);
            throw new Exception("2FA_REQUIRED");
        } else {
            // User needs to set up 2FA first
            $this->createTempSessionFor2FASetup($user, $ip_address, $user_agent);
            throw new Exception("2FA_SETUP_REQUIRED");
        }

        // Update last login
        $stmt = $this->db->prepare("UPDATE users SET last_login = NOW() WHERE id = ?");
        $stmt->execute([$user['id']]);

        // Create secure session
        $this->createSecureSession($user, $ip_address, $user_agent);

        // Log successful login
        $this->logLoginAttempt($username, $ip_address, $user_agent, true);

        $this->security_monitor->logSecurityEvent('successful_login', [
            'username' => $username,
            'role' => $user['role']
        ], 'info');

        return true;
    }

    /**
     * Create a secure session entry in database
     */
    private function createSecureSession($user, $ip_address, $user_agent) {
        // Generate secure session ID
        $session_id = bin2hex(random_bytes(64));
        $expires_at = date('Y-m-d H:i:s', time() + $this->session_lifetime);

        // Store session in database
        $stmt = $this->db->prepare("INSERT INTO user_sessions (id, user_id, client_id, ip_address, user_agent, expires_at) VALUES (?, ?, 1, ?, ?, ?)");
        $stmt->execute([$session_id, $user['id'], $ip_address, $user_agent, $expires_at]);

        // Set session variables
        $_SESSION['user_id'] = $user['id'];
        $_SESSION['client_id'] = $user['client_id'];
        $_SESSION['username'] = $user['username'];
        $_SESSION['user_role'] = $user['role'];
        $_SESSION['session_id'] = $session_id;
        $_SESSION['authenticated'] = true;
        $_SESSION['login_time'] = time();
        $_SESSION['ip_address'] = $ip_address;
    }

    /**
     * Create temporary session for 2FA verification
     */
    private function createTempSessionFor2FA($user, $ip_address, $user_agent) {
        // Generate temporary session ID
        $temp_session_id = 'temp_' . bin2hex(random_bytes(32));
        $expires_at = date('Y-m-d H:i:s', time() + 300); // 5 minutes for 2FA

        // Store temporary session
        $_SESSION['temp_2fa_user_id'] = $user['id'];
        $_SESSION['temp_2fa_username'] = $user['username'];
        $_SESSION['temp_2fa_session_id'] = $temp_session_id;
        $_SESSION['temp_2fa_expires'] = time() + 300;
        $_SESSION['temp_2fa_ip'] = $ip_address;
    }

    /**
     * Create temporary session for mandatory 2FA setup
     */
    private function createTempSessionFor2FASetup($user, $ip_address, $user_agent) {
        // Generate temporary session ID
        $temp_session_id = 'setup_' . bin2hex(random_bytes(32));
        $expires_at = date('Y-m-d H:i:s', time() + 600); // 10 minutes for setup

        // Store temporary session
        $_SESSION['temp_2fa_setup_user_id'] = $user['id'];
        $_SESSION['temp_2fa_setup_username'] = $user['username'];
        $_SESSION['temp_2fa_setup_session_id'] = $temp_session_id;
        $_SESSION['temp_2fa_setup_expires'] = time() + 600;
        $_SESSION['temp_2fa_setup_ip'] = $ip_address;
    }

    /**
     * Verify 2FA code and complete login
     */
    public function verify2FA($code, $ip_address, $user_agent) {
        if (!isset($_SESSION['temp_2fa_user_id']) || !isset($_SESSION['temp_2fa_expires'])) {
            throw new Exception("No 2FA verification in progress.");
        }

        if (time() > $_SESSION['temp_2fa_expires']) {
            $this->clearTemp2FASession();
            throw new Exception("2FA verification timed out. Please log in again.");
        }

        $user_id = $_SESSION['temp_2fa_user_id'];
        $username = $_SESSION['temp_2fa_username'];

        // Get user data including 2FA info
        $stmt = $this->db->prepare("
            SELECT id, client_id, username, role, two_factor_secret, two_factor_backup_codes
            FROM users WHERE id = ?
        ");
        $stmt->execute([$user_id]);
        $user = $stmt->fetch();

        if (!$user) {
            $this->clearTemp2FASession();
            throw new Exception("User not found.");
        }

        require_once __DIR__ . '/TwoFactorAuth.php';
        $tfa = new TwoFactorAuth();

        // Try TOTP code first
        if ($tfa->verifyCode($user['two_factor_secret'], $code)) {
            $this->complete2FALogin($user, $ip_address, $user_agent);
            return true;
        }

        // Try backup code
        if ($tfa->verifyBackupCode($user['id'], $code)) {
            $this->complete2FALogin($user, $ip_address, $user_agent);
            return true;
        }

        // Invalid code
        $this->security_monitor->logSecurityEvent('2fa_verification_failed', [
            'username' => $username,
            'ip' => $ip_address
        ], 'warning');

        throw new Exception("Invalid 2FA code.");
    }

    /**
     * Complete 2FA login after successful verification
     */
    private function complete2FALogin($user, $ip_address, $user_agent) {
        // Clear temporary session
        $this->clearTemp2FASession();

        // Update last login
        $stmt = $this->db->prepare("UPDATE users SET last_login = NOW() WHERE id = ?");
        $stmt->execute([$user['id']]);

        // Create secure session
        $this->createSecureSession($user, $ip_address, $user_agent);

        // Log successful login
        $this->logLoginAttempt($user['username'], $ip_address, $user_agent, true);

        $this->security_monitor->logSecurityEvent('successful_2fa_login', [
            'username' => $user['username'],
            'role' => $user['role']
        ], 'info');
    }

    /**
     * Complete mandatory 2FA setup
     */
    public function complete2FASetup($secret, $backupCodes, $ip_address, $user_agent) {
        if (!isset($_SESSION['temp_2fa_setup_user_id'])) {
            throw new Exception("No 2FA setup in progress.");
        }

        if (time() > $_SESSION['temp_2fa_setup_expires']) {
            $this->clearTemp2FASetupSession();
            throw new Exception("2FA setup timed out. Please log in again.");
        }

        $user_id = $_SESSION['temp_2fa_setup_user_id'];
        $username = $_SESSION['temp_2fa_setup_username'];

        require_once __DIR__ . '/TwoFactorAuth.php';
        $tfa = new TwoFactorAuth();

        if ($tfa->enable2FA($user_id, $secret, $backupCodes)) {
            // Clear temporary session
            $this->clearTemp2FASetupSession();

            // Get updated user data
            $stmt = $this->db->prepare("SELECT id, client_id, username, role FROM users WHERE id = ?");
            $stmt->execute([$user_id]);
            $user = $stmt->fetch();

            if (!$user) {
                throw new Exception("User not found after 2FA setup.");
            }

            // Update last login
            $stmt = $this->db->prepare("UPDATE users SET last_login = NOW() WHERE id = ?");
            $stmt->execute([$user['id']]);

            // Create secure session
            $this->createSecureSession($user, $ip_address, $user_agent);

            // Log successful login
            $this->logLoginAttempt($user['username'], $ip_address, $user_agent, true);

            $this->security_monitor->logSecurityEvent('successful_2fa_setup_login', [
                'username' => $user['username'],
                'role' => $user['role']
            ], 'info');

            return true;
        }

        throw new Exception("Failed to enable 2FA.");
    }

    /**
     * Clear temporary 2FA session
     */
    private function clearTemp2FASession() {
        unset($_SESSION['temp_2fa_user_id']);
        unset($_SESSION['temp_2fa_username']);
        unset($_SESSION['temp_2fa_session_id']);
        unset($_SESSION['temp_2fa_expires']);
        unset($_SESSION['temp_2fa_ip']);
    }

    /**
     * Clear temporary 2FA setup session
     */
    private function clearTemp2FASetupSession() {
        unset($_SESSION['temp_2fa_setup_user_id']);
        unset($_SESSION['temp_2fa_setup_username']);
        unset($_SESSION['temp_2fa_setup_session_id']);
        unset($_SESSION['temp_2fa_setup_expires']);
        unset($_SESSION['temp_2fa_setup_ip']);
    }

    /**
     * Check if user is in 2FA verification phase
     */
    public function isIn2FAVerification() {
        return isset($_SESSION['temp_2fa_user_id']) && isset($_SESSION['temp_2fa_expires']) && time() <= $_SESSION['temp_2fa_expires'];
    }

    /**
     * Check if user is in mandatory 2FA setup phase
     */
    public function isIn2FASetup() {
        return isset($_SESSION['temp_2fa_setup_user_id']) && isset($_SESSION['temp_2fa_setup_expires']) && time() <= $_SESSION['temp_2fa_setup_expires'];
    }

    /**
     * Check if user is authenticated and session is valid
     */
    public function isAuthenticated() {
        if (!isset($_SESSION['authenticated']) || !$_SESSION['authenticated']) {
            return false;
        }

        if (!isset($_SESSION['session_id'])) {
            return false;
        }

        // Verify session exists in database and is not expired
        $stmt = $this->db->prepare("SELECT id FROM user_sessions WHERE id = ? AND expires_at > NOW()");
        $stmt->execute([$_SESSION['session_id']]);
        $session = $stmt->fetch();

        if (!$session) {
            $this->logout();
            return false;
        }

        // Run cleanup occasionally (1% chance per request)
        if (rand(1, 100) === 1) {
            $this->cleanupExpiredTokens();
        }

        // Update last activity
        $stmt = $this->db->prepare("UPDATE user_sessions SET last_activity = NOW() WHERE id = ?");
        $stmt->execute([$_SESSION['session_id']]);

        // Check session timeout
        if (time() - $_SESSION['login_time'] > $this->session_lifetime) {
            $this->logout();
            return false;
        }

        return true;
    }

    /**
     * Logout user and destroy session
     */
    public function logout() {
        if (isset($_SESSION['session_id'])) {
            // Remove session from database
            $stmt = $this->db->prepare("DELETE FROM user_sessions WHERE id = ?");
            $stmt->execute([$_SESSION['session_id']]);
        }

        // Destroy PHP session
        session_destroy();
        session_start(); // Start new session to prevent errors
    }

    /**
     * Generate CSRF token
     */
    public function generateCSRFToken() {
        if (!isset($_SESSION['session_id'])) {
            error_log("CSRF generateCSRFToken failed: no session_id in " . session_id());
            return false;
        }

        $token = bin2hex(random_bytes(32));
        $expires_at = date('Y-m-d H:i:s', time() + $this->csrf_token_lifetime);

        error_log("CSRF token generated: " . substr($token, 0, 10) . "... for session: " . $_SESSION['session_id'] . " (PHP session: " . session_id() . ") expires: " . $expires_at);

        try {
            // Store token in database
            $stmt = $this->db->prepare("INSERT INTO csrf_tokens (token, session_id, client_id, expires_at) VALUES (?, ?, 1, ?)");
            $stmt->execute([$token, $_SESSION['session_id'], $expires_at]);
            error_log("CSRF token stored in database successfully for session: " . $_SESSION['session_id']);
            return $token;
        } catch (Exception $e) {
            error_log("CSRF token storage failed: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Validate CSRF token
     */
    public function validateCSRFToken($token) {
        // Ensure we have a session and token
        if (!isset($_SESSION['session_id']) || empty($token)) {
            error_log("CSRF validation failed: missing session_id or token (PHP session: " . session_id() . ")");
            return false;
        }

        // Clean the token to prevent injection
        $token = trim($token);
        if (strlen($token) !== 64 || !preg_match('/^[a-f0-9]+$/', $token)) {
            error_log("CSRF validation failed: invalid token format - length: " . strlen($token) . ", regex match: " . (preg_match('/^[a-f0-9]+$/', $token) ? 'yes' : 'no'));
            return false;
        }

        try {
            // Check if token exists and is valid for current session
            $stmt = $this->db->prepare("
                SELECT id FROM csrf_tokens
                WHERE token = ? AND session_id = ? AND expires_at > NOW()
                LIMIT 1
            ");
            $stmt->execute([$token, $_SESSION['session_id']]);
            $result = $stmt->fetch();

            // If not found for current session, check for any recent token (grace period for session regeneration)
            if (!$result) {
                $stmt = $this->db->prepare("
                    SELECT id FROM csrf_tokens
                    WHERE token = ? AND expires_at > NOW() AND created_at > DATE_SUB(NOW(), INTERVAL 5 MINUTE)
                    LIMIT 1
                ");
                $stmt->execute([$token]);
                $result = $stmt->fetch();
                if ($result) {
                    error_log("CSRF token accepted via grace period (possible session regeneration)");
                }
            }

            error_log("CSRF token lookup result: " . ($result ? 'found' : 'not found') . " for session: " . $_SESSION['session_id'] . " (PHP session: " . session_id() . ")");

            if ($result) {
                // Token is valid - delete it to prevent reuse
                $stmt = $this->db->prepare("DELETE FROM csrf_tokens WHERE token = ?");
                $stmt->execute([$token]);
                error_log("CSRF token validated and deleted successfully");
                return true;
            }
        } catch (Exception $e) {
            // Log database errors but don't fail validation due to DB issues
            error_log("CSRF validation database error: " . $e->getMessage());
        }

        error_log("CSRF validation failed: token not found or expired");
        return false;
    }

    /**
     * Check if account is locked
     */
    private function isAccountLocked($username) {
        $stmt = $this->db->prepare("SELECT locked_until FROM users WHERE username = ? AND locked_until > NOW()");
        $stmt->execute([$username]);
        $result = $stmt->fetch();

        return $result !== false;
    }

    /**
     * Increment failed login attempts
     */
    private function incrementFailedAttempts($username) {
        $stmt = $this->db->prepare("UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE username = ?");
        $stmt->execute([$username]);

        // Check if account should be locked
        $stmt = $this->db->prepare("SELECT failed_login_attempts FROM users WHERE username = ?");
        $stmt->execute([$username]);
        $result = $stmt->fetch();

        if ($result && $result['failed_login_attempts'] >= $this->max_login_attempts) {
            $locked_until = date('Y-m-d H:i:s', time() + $this->lockout_duration);
            $stmt = $this->db->prepare("UPDATE users SET locked_until = ? WHERE username = ?");
            $stmt->execute([$locked_until, $username]);
        }
    }

    /**
     * Reset failed login attempts
     */
    private function resetFailedAttempts($user_id) {
        $stmt = $this->db->prepare("UPDATE users SET failed_login_attempts = 0, locked_until = NULL WHERE id = ?");
        $stmt->execute([$user_id]);
    }

    /**
     * Log login attempt
     */
    private function logLoginAttempt($username, $ip_address, $user_agent, $success) {
        $stmt = $this->db->prepare("INSERT INTO login_attempts (client_id, username, ip_address, user_agent, success) VALUES (1, ?, ?, ?, ?)");
        $stmt->bindParam(1, $username, PDO::PARAM_STR);
        $stmt->bindParam(2, $ip_address, PDO::PARAM_STR);
        $stmt->bindParam(3, $user_agent, PDO::PARAM_STR);
        $stmt->bindParam(4, $success, PDO::PARAM_INT);
        $stmt->execute();
    }

    /**
     * Get current user information
     */
    public function getCurrentUser() {
        if (!$this->isAuthenticated()) {
            return null;
        }

        // Get additional user info from database
        $stmt = $this->db->prepare("SELECT email, last_login FROM users WHERE id = ?");
        $stmt->execute([$_SESSION['user_id']]);
        $user_data = $stmt->fetch();

        return [
            'id' => $_SESSION['user_id'],
            'client_id' => $_SESSION['client_id'],
            'username' => $_SESSION['username'],
            'email' => $user_data ? $user_data['email'] : null,
            'role' => $_SESSION['user_role'],
            'last_login' => $user_data ? $user_data['last_login'] : null
        ];
    }

    /**
     * Get database connection (for use by other classes)
     */
    public function getDatabaseConnection() {
        return $this->db;
    }

    /**
     * Check if current user has role
     */
    public function hasRole($role) {
        $user = $this->getCurrentUser();
        return $user && $user['role'] === $role;
    }

    /**
     * Clean up expired CSRF tokens and sessions
     */
    public function cleanupExpiredTokens() {
        try {
            // Delete CSRF tokens older than 1 hour
            $stmt = $this->db->prepare("DELETE FROM csrf_tokens WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 HOUR)");
            $stmt->execute();
            
            // Delete expired user sessions
            $stmt = $this->db->prepare("DELETE FROM user_sessions WHERE expires_at < NOW()");
            $stmt->execute();
        } catch (Exception $e) {
            error_log("Token cleanup error: " . $e->getMessage());
        }
    }
}