<?php
/**
 * Security Monitoring and Alerting Class  
 * Monitors for suspicious activities and security events
 */

class SecurityMonitor {
    private $db;

    // Security thresholds
    private $max_failed_attempts = 5;
    private $alert_window_minutes = 15;
    private $suspicious_ip_threshold = 3;

    public function __construct() {
        $this->db = Database::getInstance()->getConnection();
    }

    /**
     * Log security event
     */
    public function logSecurityEvent($event_type, $details, $severity = 'info') {
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? 'unknown';
        $uri = $_SERVER['REQUEST_URI'] ?? 'unknown';

        $event_data = [
            'event_type' => $event_type,
            'ip_address' => $ip,
            'user_agent' => $user_agent,
            'uri' => $uri,
            'details' => $details,
            'timestamp' => date('Y-m-d H:i:s')
        ];

        // Log to database
        $this->logToDatabase($event_data);

        // Log to error log
        error_log("SECURITY [$severity]: $event_type - " . json_encode($details));

        // Check for alerts
        $this->checkForAlerts($event_type, $ip);
    }

    /**
     * Log security event to database
     */
    private function logToDatabase($event_data) {
        try {
            $stmt = $this->db->prepare("
                INSERT INTO security_events
                (client_id, event_type, ip_address, user_agent, uri, details, severity, created_at)
                VALUES (1, ?, ?, ?, ?, ?, 'info', NOW())
            ");
            $stmt->execute([
                $event_data['event_type'],
                $event_data['ip_address'],
                $event_data['user_agent'],
                $event_data['uri'],
                json_encode($event_data['details'])
            ]);
        } catch (Exception $e) {
            error_log("Security monitoring DB error: " . $e->getMessage());
        }
    }

    /**
     * Check for security alerts
     */
    private function checkForAlerts($event_type, $ip) {
        switch ($event_type) {
            case 'failed_login':
                $this->checkBruteForceAlert($ip);
                break;
            case 'csrf_attempt':
                $this->alertCSRF($ip);
                break;
            case 'suspicious_request':
                $this->alertSuspiciousActivity($ip);
                break;
        }
    }

    /**
     * Check for brute force attack patterns
     */
    private function checkBruteForceAlert($ip) {
        $time_window = date('Y-m-d H:i:s', time() - ($this->alert_window_minutes * 60));

        $stmt = $this->db->prepare("
            SELECT COUNT(*) as attempts
            FROM login_attempts
            WHERE ip_address = ? AND attempt_time > ? AND success = FALSE
        ");
        $stmt->execute([$ip, $time_window]);
        $result = $stmt->fetch();

        if ($result && $result['attempts'] >= $this->max_failed_attempts) {
            $this->logSecurityEvent('brute_force_detected', [
                'ip' => $ip,
                'attempts' => $result['attempts'],
                'time_window' => $this->alert_window_minutes . ' minutes'
            ], 'critical');

            $this->blockIP($ip);
        }
    }

    /**
     * Alert on CSRF attempts
     */
    private function alertCSRF($ip) {
        $this->logSecurityEvent('csrf_attack_detected', [
            'ip' => $ip,
            'action' => 'CSRF token validation failed'
        ], 'warning');
    }

    /**
     * Alert on suspicious activity
     */
    private function alertSuspiciousActivity($ip) {
        $time_window = date('Y-m-d H:i:s', time() - 3600);

        $stmt = $this->db->prepare("
            SELECT COUNT(*) as events
            FROM security_events
            WHERE ip_address = ? AND created_at > ? AND event_type = 'suspicious_request'
        ");
        $stmt->execute([$ip, $time_window]);
        $result = $stmt->fetch();

        if ($result && $result['events'] >= $this->suspicious_ip_threshold) {
            $this->logSecurityEvent('suspicious_ip_detected', [
                'ip' => $ip,
                'events' => $result['events'],
                'time_window' => '1 hour'
            ], 'warning');
        }
    }

    /**
     * Block suspicious IP (log only for now)
     */
    private function blockIP($ip) {
        $this->logSecurityEvent('ip_blocked', [
            'ip' => $ip,
            'action' => 'IP blocked due to suspicious activity',
            'block_type' => 'logged_only'
        ], 'critical');
    }

    /**
     * Validate request for suspicious patterns
     */
    public function validateRequest() {
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';
        $uri = $_SERVER['REQUEST_URI'] ?? '';

        // Check for suspicious user agents
        $suspicious_agents = ['sqlmap', 'nmap', 'nikto', 'dirbuster', 'gobuster', 'wpscan'];

        foreach ($suspicious_agents as $agent) {
            if (stripos($user_agent, $agent) !== false) {
                $this->logSecurityEvent('suspicious_user_agent', [
                    'user_agent' => $user_agent,
                    'matched_pattern' => $agent
                ], 'warning');
                break;
            }
        }

        // Check for SQL injection patterns
        $sql_patterns = ['union select', 'information_schema', 'concat(', 'script>', 'javascript:', 'onload=', 'onerror='];
        $query_string = $_SERVER['QUERY_STRING'] ?? '';
        $post_data = file_get_contents('php://input');

        foreach ([$uri, $query_string, $post_data] as $data) {
            foreach ($sql_patterns as $pattern) {
                if (stripos($data, $pattern) !== false) {
                    $this->logSecurityEvent('suspicious_request', [
                        'data' => substr($data, 0, 200),
                        'matched_pattern' => $pattern,
                        'request_type' => 'potential_injection'
                    ], 'warning');
                    break 2;
                }
            }
        }
    }

    /**
     * Get security statistics
     */
    public function getSecurityStats($hours = 24) {
        $time_window = date('Y-m-d H:i:s', time() - ($hours * 3600));
        $stats = [];

        $stmt = $this->db->prepare("SELECT COUNT(*) as count FROM login_attempts WHERE attempt_time > ? AND success = FALSE");
        $stmt->execute([$time_window]);
        $stats['failed_logins'] = $stmt->fetch()['count'];

        $stmt = $this->db->prepare("SELECT COUNT(*) as count FROM login_attempts WHERE attempt_time > ? AND success = TRUE");
        $stmt->execute([$time_window]);
        $stats['successful_logins'] = $stmt->fetch()['count'];

        $stmt = $this->db->prepare("SELECT event_type, COUNT(*) as count FROM security_events WHERE created_at > ? GROUP BY event_type");
        $stmt->execute([$time_window]);
        $stats['security_events'] = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);

        return $stats;
    }
}
?>
