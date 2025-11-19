<?php
/**
 * Web Interface Logging Utility
 * Provides centralized logging for the Google Stats web interface
 */

class WebLogger {
    private $log_file;
    private $log_level;

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
        } else {
            $this->log_file = $log_file;
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

    public function log_authentication($success, $username = null) {
        if ($success) {
            $this->info("Authentication successful", ['username' => $username]);
        } else {
            $this->warning("Authentication failed", [
                'username' => $username,
                'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown'
            ]);
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