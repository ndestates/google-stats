<?php
/**
 * Two-Factor Authentication (2FA) Class
 * Implements TOTP (Time-based One-Time Password) using Google Authenticator compatible algorithm
 */

class TwoFactorAuth {
    private $db;

    public function __construct() {
        $this->db = Database::getInstance()->getConnection();
    }

    /**
     * Generate a new TOTP secret
     */
    public function generateSecret() {
        $randomBytes = random_bytes(32);
        return $this->base32Encode($randomBytes);
    }

    /**
     * Encode binary data to base32
     */
    private function base32Encode($data) {
        $base32Chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        $binary = '';
        $result = '';

        for ($i = 0; $i < strlen($data); $i++) {
            $binary .= str_pad(decbin(ord($data[$i])), 8, '0', STR_PAD_LEFT);
        }

        for ($i = 0; $i < strlen($binary); $i += 5) {
            $chunk = substr($binary, $i, 5);
            $chunk = str_pad($chunk, 5, '0', STR_PAD_RIGHT);
            $index = bindec($chunk);
            $result .= $base32Chars[$index];
        }

        return $result;
    }

    /**
     * Generate backup recovery codes
     */
    public function generateBackupCodes($count = 10) {
        $codes = [];
        for ($i = 0; $i < $count; $i++) {
            $codes[] = bin2hex(random_bytes(4));
        }
        return $codes;
    }

    /**
     * Get QR code URL for Google Authenticator
     */
    public function getQRCodeUrl($username, $secret, $issuer = 'GoogleStats') {
        $encodedIssuer = urlencode($issuer);
        $encodedUsername = urlencode($username);
        return "otpauth://totp/{$encodedIssuer}:{$encodedUsername}?secret={$secret}&issuer={$encodedIssuer}";
    }

    /**
     * Verify TOTP code
     */
    public function verifyCode($secret, $code, $window = 1) {
        $time = floor(time() / 30);

        for ($i = -$window; $i <= $window; $i++) {
            $checkTime = $time + $i;
            if ($this->generateCode($secret, $checkTime) === $code) {
                return true;
            }
        }

        return false;
    }

    /**
     * Decode base32 string to binary
     */
    private function base32Decode($base32) {
        $base32Chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        $base32 = strtoupper($base32);
        $binary = '';
        $bits = '';

        for ($i = 0; $i < strlen($base32); $i++) {
            $char = $base32[$i];
            if ($char === '=') break;

            $value = strpos($base32Chars, $char);
            if ($value === false) continue;

            $bits .= str_pad(decbin($value), 5, '0', STR_PAD_LEFT);
        }

        for ($i = 0; $i < strlen($bits); $i += 8) {
            $byteBits = substr($bits, $i, 8);
            if (strlen($byteBits) < 8) break;
            $binary .= chr(bindec($byteBits));
        }

        return $binary;
    }

    /**
     * Generate TOTP code for a given time
     */
    private function generateCode($secret, $time) {
        $secret = $this->base32Decode($secret);
        $time = pack('N*', 0) . pack('N*', $time);

        $hash = hash_hmac('sha1', $time, $secret, true);
        $offset = ord($hash[19]) & 0x0F;

        $code = (
            ((ord($hash[$offset]) & 0x7F) << 24) |
            ((ord($hash[$offset + 1]) & 0xFF) << 16) |
            ((ord($hash[$offset + 2]) & 0xFF) << 8) |
            (ord($hash[$offset + 3]) & 0xFF)
        );

        return str_pad($code % (10 ** 6), 6, '0', STR_PAD_LEFT);
    }

    /**
     * Enable 2FA for a user
     */
    public function enable2FA($userId, $secret, $backupCodes) {
        $stmt = $this->db->prepare("
            UPDATE users
            SET two_factor_enabled = TRUE,
                two_factor_secret = ?,
                two_factor_backup_codes = ?,
                updated_at = NOW()
            WHERE id = ?
        ");
        return $stmt->execute([$secret, json_encode($backupCodes), $userId]);
    }

    /**
     * Disable 2FA for a user
     */
    public function disable2FA($userId) {
        $stmt = $this->db->prepare("
            UPDATE users
            SET two_factor_enabled = FALSE,
                two_factor_secret = NULL,
                two_factor_backup_codes = NULL,
                updated_at = NOW()
            WHERE id = ?
        ");
        return $stmt->execute([$userId]);
    }

    /**
     * Check if user has 2FA enabled
     */
    public function is2FAEnabled($userId) {
        $stmt = $this->db->prepare("SELECT two_factor_enabled FROM users WHERE id = ?");
        $stmt->execute([$userId]);
        $result = $stmt->fetch();
        return $result && $result['two_factor_enabled'];
    }

    /**
     * Get user's 2FA secret
     */
    public function getSecret($userId) {
        $stmt = $this->db->prepare("SELECT two_factor_secret FROM users WHERE id = ?");
        $stmt->execute([$userId]);
        $result = $stmt->fetch();
        return $result ? $result['two_factor_secret'] : null;
    }

    /**
     * Verify backup code and consume it
     */
    public function verifyBackupCode($userId, $code) {
        $stmt = $this->db->prepare("SELECT two_factor_backup_codes FROM users WHERE id = ?");
        $stmt->execute([$userId]);
        $result = $stmt->fetch();

        if (!$result || !$result['two_factor_backup_codes']) {
            return false;
        }

        $codes = json_decode($result['two_factor_backup_codes'], true);
        $index = array_search($code, $codes);

        if ($index !== false) {
            unset($codes[$index]);
            $stmt = $this->db->prepare("
                UPDATE users
                SET two_factor_backup_codes = ?,
                    updated_at = NOW()
                WHERE id = ?
            ");
            $stmt->execute([json_encode(array_values($codes)), $userId]);
            return true;
        }

        return false;
    }

    /**
     * Regenerate backup codes
     */
    public function regenerateBackupCodes($userId) {
        $codes = $this->generateBackupCodes();
        $stmt = $this->db->prepare("
            UPDATE users
            SET two_factor_backup_codes = ?,
                updated_at = NOW()
            WHERE id = ?
        ");
        $stmt->execute([json_encode($codes), $userId]);
        return $codes;
    }
}
?>
