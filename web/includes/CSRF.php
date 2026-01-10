<?php
/**
 * CSRF Protection Utility
 * Provides CSRF token generation and validation for forms
 */

class CSRF {
    private $db;

    public function __construct() {
        $this->db = Database::getInstance()->getConnection();
    }

    /**
     * Generate hidden input field with CSRF token
     */
    public function getTokenField() {
        $token = $this->generateTokenPrivate();
        if (!$token) {
            return '';
        }

        return '<input type="hidden" name="csrf_token" value="' . htmlspecialchars($token) . '">';
    }

    /**
     * Generate CSRF token (public version for direct token access)
     */
    public function generateToken() {
        return $this->generateTokenPrivate();
    }

    /**
     * Generate CSRF token (works for both authenticated and unauthenticated users)
     */
    private function generateTokenPrivate() {
        // For authenticated users, use session-based tokens
        if (isset($_SESSION['session_id'])) {
            $auth = new Auth();
            return $auth->generateCSRFToken();
        }

        // For unauthenticated users (like login form), create temporary token
        $temp_session_id = session_id();
        if (empty($temp_session_id)) {
            session_start();
            $temp_session_id = session_id();
        }

        $token = bin2hex(random_bytes(32));
        $expires_at = date('Y-m-d H:i:s', time() + 3600);

        try {
            $stmt = $this->db->prepare("INSERT INTO csrf_tokens (token, session_id, client_id, expires_at) VALUES (?, ?, 1, ?)");
            $stmt->execute([$token, 'temp_' . $temp_session_id, $expires_at]);
            return $token;
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Validate CSRF token from POST data
     */
    public function validateCSRFToken($token = null) {
        if ($token !== null) {
            $original_post = $_POST;
            $_POST['csrf_token'] = $token;
            $result = $this->validateToken();
            $_POST = $original_post;
            return $result;
        }
        return $this->validateToken();
    }

    /**
     * Validate CSRF token from POST data
     */
    public function validateToken() {
        $token = $_POST['csrf_token'] ?? '';

        // For authenticated users, use the standard validation
        if (isset($_SESSION['session_id'])) {
            $auth = new Auth();
            return $auth->validateCSRFToken($token);
        }

        // For unauthenticated users, validate temporary token
        $temp_session_id = session_id();
        if (empty($temp_session_id)) {
            return false;
        }

        $token = trim($token);
        if (strlen($token) !== 64 || !preg_match('/^[a-f0-9]+$/', $token)) {
            return false;
        }

        try {
            $stmt = $this->db->prepare("
                SELECT id FROM csrf_tokens
                WHERE token = ? AND session_id = ? AND expires_at > NOW()
                LIMIT 1
            ");
            $stmt->execute([$token, 'temp_' . $temp_session_id]);
            $result = $stmt->fetch();

            if ($result) {
                $stmt = $this->db->prepare("DELETE FROM csrf_tokens WHERE token = ?");
                $stmt->execute([$token]);
                return true;
            }
        } catch (Exception $e) {
            error_log("CSRF validation database error: " . $e->getMessage());
        }

        return false;
    }

    /**
     * Get CSRF token as JSON for AJAX requests
     */
    public function getTokenJSON() {
        $auth = new Auth();
        $token = $auth->generateCSRFToken();
        return json_encode(['csrf_token' => $token]);
    }
}
?>
