<?php
/**
 * PHPUnit Bootstrap File
 * Sets up the testing environment for authentication tests
 */

// Define test constants
define('TEST_MODE', true);
define('USERS_FILE', __DIR__ . '/../../web/uploads/test_users.json');
define('SESSIONS_FILE', __DIR__ . '/../../web/uploads/test_sessions.json');
define('CREDENTIALS_FILE', __DIR__ . '/../../web/uploads/test_credentials.enc');

// Clean up any existing test files
$testFiles = [USERS_FILE, SESSIONS_FILE, CREDENTIALS_FILE];
foreach ($testFiles as $file) {
    if (file_exists($file)) {
        unlink($file);
    }
}

// Include the authentication functions
require_once __DIR__ . '/../../web/auth.php';
require_once __DIR__ . '/../../web/credentials.php';

// Mock the web logger for testing
class MockWebLogger {
    public $logs = [];

    public function log_authentication($success, $username = null) {
        $this->logs[] = ['type' => 'auth', 'success' => $success, 'username' => $username];
    }

    public function log_security_event($event, $details = []) {
        $this->logs[] = ['type' => 'security', 'event' => $event, 'details' => $details];
    }

    public function check_rate_limit($identifier, $max_attempts = 10, $time_window = 300) {
        return true; // Always allow in tests
    }

    public function is_ip_blocked($ip) {
        return false; // Never blocked in tests
    }

    public function block_ip($ip, $reason = 'manual') {
        $this->logs[] = ['type' => 'security', 'event' => 'IP_BLOCKED', 'details' => ['ip' => $ip, 'reason' => $reason]];
    }

    public function log_suspicious_activity($activity, $details = []) {
        $this->logs[] = ['type' => 'security', 'event' => 'SUSPICIOUS_ACTIVITY', 'details' => array_merge($details, ['activity' => $activity])];
    }

    public function log_failed_login($username, $ip) {
        $this->logs[] = ['type' => 'security', 'event' => 'FAILED_LOGIN', 'details' => ['username' => $username, 'ip' => $ip]];
    }

    public function info($message, $context = []) {
        $this->logs[] = ['type' => 'info', 'message' => $message, 'context' => $context];
    }

    public function warning($message, $context = []) {
        $this->logs[] = ['type' => 'warning', 'message' => $message, 'context' => $context];
    }
}

// Replace the global logger with our mock
global $web_logger;
$web_logger = new MockWebLogger();

// Helper function to clean up test files
function cleanup_test_files() {
    $testFiles = [USERS_FILE, SESSIONS_FILE, CREDENTIALS_FILE];
    foreach ($testFiles as $file) {
        if (file_exists($file)) {
            unlink($file);
        }
    }
}

// Register cleanup on shutdown
register_shutdown_function('cleanup_test_files');