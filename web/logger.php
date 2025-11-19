<?php
/**
 * Web Interface Logging Utility
 * Provides centralized logging for the Google Stats web interface
 */

class WebLogger {
    private $log_file;
    private $log_level;
    private $security_file;
    private $rate_limit_file;

    const LEVEL_DEBUG = 'DEBUG';
    const LEVEL_INFO = 'INFO';
    const LEVEL_WARNING = 'WARNING';
    const LEVEL_ERROR = 'ERROR';

    public function __construct($log_file = null, $log_level = null) {
        if ($log_file === null) {
            // Get the project root from the current file path
            $project_root = realpath(dirname(dirname(__FILE__)));
            $log_dir = $project_root . '/logs';

            if (!is_dir($log_dir)) {
                mkdir($log_dir, 0755, true);
            }
            $this->log_file = $log_dir . '/web_interface.log';
            $this->security_file = $log_dir . '/security.log';
            $this->rate_limit_file = $log_dir . '/rate_limits.json';
        } else {
            $this->log_file = $log_file;
            $this->security_file = dirname($log_file) . '/security.log';
            $this->rate_limit_file = dirname($log_file) . '/rate_limits.json';
        }

        // Determine log level from environment variable or parameter
        if ($log_level === null) {
            $env_level = getenv('WEB_LOG_LEVEL') ?: getenv('LOG_LEVEL') ?: 'INFO';
            $env_level = strtoupper($env_level);

            $level_map = [
                'DEBUG' => self::LEVEL_DEBUG,
                'INFO' => self::LEVEL_INFO,
                'WARNING' => self::LEVEL_WARNING,
                'ERROR' => self::LEVEL_ERROR,
                'OFF' => 'OFF'  // Special value to disable logging
            ];

            $log_level = $level_map[$env_level] ?? self::LEVEL_INFO;
        }

        $this->log_level = $log_level;
    }

    private function should_log($level) {
        // If logging is turned off, don't log anything
        if ($this->log_level === 'OFF') {
            return false;
        }

        $levels = [
            self::LEVEL_DEBUG => 1,
            self::LEVEL_INFO => 2,
            self::LEVEL_WARNING => 3,
            self::LEVEL_ERROR => 4
        ];

        return $levels[$level] >= $levels[$this->log_level];
    }

    private function write_log($level, $message, $context = []) {
        if (!$this->should_log($level)) {
            return;
        }

        $timestamp = date('Y-m-d H:i:s');
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
        $request_uri = $_SERVER['REQUEST_URI'] ?? 'unknown';
        $method = $_SERVER['REQUEST_METHOD'] ?? 'unknown';

        $log_entry = sprintf(
            "[%s] %s [%s] %s %s - %s",
            $timestamp,
            $level,
            $ip,
            $method,
            $request_uri,
            $message
        );

        if (!empty($context)) {
            $log_entry .= " | Context: " . json_encode($context);
        }

        $log_entry .= " | User-Agent: " . substr($user_agent, 0, 200) . "\n";

        // Also log to PHP error log for immediate visibility
        error_log("WebLogger: " . trim($log_entry));

        // Write to file
        file_put_contents($this->log_file, $log_entry, FILE_APPEND | LOCK_EX);
    }

    public function debug($message, $context = []) {
        $this->write_log(self::LEVEL_DEBUG, $message, $context);
    }

    public function info($message, $context = []) {
        $this->write_log(self::LEVEL_INFO, $message, $context);
    }

    public function warning($message, $context = []) {
        $this->write_log(self::LEVEL_WARNING, $message, $context);
    }

    public function error($message, $context = []) {
        $this->write_log(self::LEVEL_ERROR, $message, $context);
    }

    public function log_script_execution($script, $args, $exit_code, $output = '', $errors = '') {
        $context = [
            'script' => $script,
            'args' => $args,
            'exit_code' => $exit_code,
            'output_length' => strlen($output),
            'errors_length' => strlen($errors)
        ];

        if ($exit_code === 0) {
            $this->info("Script executed successfully: $script", $context);
        } else {
            $this->error("Script execution failed: $script (exit code: $exit_code)", $context);
            if (!empty($errors)) {
                $this->error("Script errors: " . substr($errors, 0, 500), $context);
            }
        }
    }

    public function log_api_request($endpoint, $method, $params = []) {
        $this->info("API request: $method $endpoint", [
            'params' => $this->sanitize_params($params)
        ]);
    }

    // Security monitoring methods
    public function log_security_event($event, $details = []) {
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';

        $this->log_to_file($this->security_file, 'SECURITY', $event, array_merge($details, [
            'ip' => $ip,
            'user_agent' => $user_agent,
            'timestamp' => date('Y-m-d H:i:s')
        ]));
    }

    public function check_rate_limit($identifier, $max_attempts = 10, $time_window = 300) {
        $rate_limits = $this->load_rate_limits();
        $now = time();
        $window_start = $now - $time_window;

        if (!isset($rate_limits[$identifier])) {
            $rate_limits[$identifier] = [];
        }

        // Remove old attempts outside the time window
        $rate_limits[$identifier] = array_filter($rate_limits[$identifier], function($timestamp) use ($window_start) {
            return $timestamp > $window_start;
        });

        // Check if rate limit exceeded
        if (count($rate_limits[$identifier]) >= $max_attempts) {
            $this->log_security_event('RATE_LIMIT_EXCEEDED', [
                'identifier' => $identifier,
                'attempts' => count($rate_limits[$identifier]),
                'max_attempts' => $max_attempts
            ]);
            return false;
        }

        // Add current attempt
        $rate_limits[$identifier][] = $now;
        $this->save_rate_limits($rate_limits);

        return true;
    }

    public function block_ip($ip, $reason = 'manual') {
        $blocked_ips = $this->load_blocked_ips();
        $blocked_ips[$ip] = [
            'blocked_at' => time(),
            'reason' => $reason
        ];
        $this->save_blocked_ips($blocked_ips);
        $this->log_security_event('IP_BLOCKED', ['ip' => $ip, 'reason' => $reason]);
    }

    public function is_ip_blocked($ip) {
        $blocked_ips = $this->load_blocked_ips();
        return isset($blocked_ips[$ip]);
    }

    public function log_failed_login($username, $ip) {
        $this->log_security_event('FAILED_LOGIN', [
            'username' => $username,
            'ip' => $ip
        ]);

        // Check for brute force attack
        $identifier = 'login_' . $ip;
        if (!$this->check_rate_limit($identifier, 5, 900)) { // 5 attempts per 15 minutes
            $this->block_ip($ip, 'brute_force_login');
        }
    }

    public function log_suspicious_activity($activity, $details = []) {
        $this->log_security_event('SUSPICIOUS_ACTIVITY', array_merge($details, [
            'activity' => $activity
        ]));
    }

    private function load_rate_limits() {
        if (!file_exists($this->rate_limit_file)) {
            return [];
        }
        $data = json_decode(file_get_contents($this->rate_limit_file), true);
        return $data ?: [];
    }

    private function save_rate_limits($rate_limits) {
        file_put_contents($this->rate_limit_file, json_encode($rate_limits));
    }

    private function load_blocked_ips() {
        $blocked_file = dirname($this->security_file) . '/blocked_ips.json';
        if (!file_exists($blocked_file)) {
            return [];
        }
        $data = json_decode(file_get_contents($blocked_file), true);
        return $data ?: [];
    }

    private function save_blocked_ips($blocked_ips) {
        $blocked_file = dirname($this->security_file) . '/blocked_ips.json';
        file_put_contents($blocked_file, json_encode($blocked_ips));
    }

    private function log_to_file($file, $level, $message, $context = []) {
        if ($this->log_level === 'OFF') {
            return;
        }

        $timestamp = date('Y-m-d H:i:s');
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $method = $_SERVER['REQUEST_METHOD'] ?? 'unknown';
        $request_uri = $_SERVER['REQUEST_URI'] ?? 'unknown';

        $log_entry = sprintf(
            "[%s] %s [%s] %s %s - %s",
            $timestamp, $level, $ip, $method, $request_uri, $message
        );

        if (!empty($context)) {
            $log_entry .= ' ' . json_encode($context);
        }

        $log_entry .= "\n";

        file_put_contents($file, $log_entry, FILE_APPEND);
    }

    public function log_authentication($success, $username = null) {
        if ($success) {
            $this->info("Authentication successful", ['username' => $username]);
        } else {
            $this->warning("Authentication failed", [
                'username' => $username,
                'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
            ]);
            $this->log_failed_login($username, $_SERVER['REMOTE_ADDR'] ?? 'unknown');
        }
    }

    private function sanitize_params($params) {
        // Remove sensitive information from logged parameters
        $sensitive_keys = ['password', 'token', 'secret', 'key'];
        $sanitized = [];

        foreach ($params as $key => $value) {
            if (in_array(strtolower($key), $sensitive_keys)) {
                $sanitized[$key] = '[REDACTED]';
            } else {
                $sanitized[$key] = is_string($value) ? substr($value, 0, 100) : $value;
            }
        }

        return $sanitized;
    }
}

// Global logger instance
try {
    $web_logger = new WebLogger();
} catch (Exception $e) {
    // Fallback: create a simple logger that writes to a known location
    $web_logger = null;
    file_put_contents('/tmp/web_logger_error.log', "Logger creation failed: " . $e->getMessage() . "\n", FILE_APPEND);
}