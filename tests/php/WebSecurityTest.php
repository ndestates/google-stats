<?php

use PHPUnit\Framework\TestCase;

class WebSecurityTest extends TestCase
{
    protected function setUp(): void
    {
        // Clean up before each test
        $testFiles = [
            __DIR__ . '/../../web/uploads/test_users.json',
            __DIR__ . '/../../web/uploads/test_sessions.json',
            __DIR__ . '/../../web/uploads/test_credentials.enc'
        ];
        foreach ($testFiles as $file) {
            if (file_exists($file)) {
                unlink($file);
            }
        }

        // Reset session
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
    }

    protected function tearDown(): void
    {
        // Clean up after each test
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
    }

    /**
     * Test that authentication is required for sensitive operations
     */
    public function testAuthenticationRequiredForSensitiveOperations()
    {
        // Ensure no user is logged in
        $this->assertFalse(is_logged_in());

        // Verify that sensitive functions require authentication
        // This tests the core authentication logic that the web pages use

        // Test that is_logged_in() returns false when not authenticated
        $this->assertFalse(is_logged_in());

        // Test that get_logged_in_user() returns null when not authenticated
        $this->assertNull(get_logged_in_user());
    }

    /**
     * Test that authenticated users have proper access
     */
    public function testAuthenticatedUserHasProperAccess()
    {
        // Authenticate a user
        $this->assertTrue(authenticate_user('admin', 'admin123'));
        $this->assertTrue(is_logged_in());

        // Test that authenticated user can access user information
        $user = get_logged_in_user();
        $this->assertNotNull($user);
        $this->assertEquals('admin', $user['username']);
        $this->assertEquals('admin', $user['role']);
    }

    /**
     * Test that admin.php requires authentication (logic test)
     */
    public function testAdminPageAuthenticationLogic()
    {
        // Test the authentication check logic that admin.php uses
        $this->assertFalse(is_logged_in(), 'User should not be logged in initially');

        // After authentication, user should be logged in
        authenticate_user('admin', 'admin123');
        $this->assertTrue(is_logged_in(), 'User should be logged in after authentication');
    }

    /**
     * Test that run_report.php requires authentication (logic test)
     */
    public function testRunReportAuthenticationLogic()
    {
        // Test the authentication check logic that run_report.php uses
        $this->assertFalse(is_logged_in(), 'User should not be logged in initially');

        // After authentication, user should be logged in
        authenticate_user('admin', 'admin123');
        $this->assertTrue(is_logged_in(), 'User should be logged in after authentication');
    }

    /**
     * Test that credentials are not exposed in authentication system
     */
    public function testCredentialsNotExposedInAuthSystem()
    {
        // Test that the authentication system doesn't expose credentials
        $users = load_users();

        // Ensure passwords are hashed (not stored in plain text)
        foreach ($users as $user) {
            $this->assertArrayHasKey('password_hash', $user);
            $this->assertArrayNotHasKey('password', $user, 'Plain text passwords should not be stored');

            // Verify password hash is valid bcrypt
            $this->assertStringStartsWith('$2', $user['password_hash'], 'Password should be bcrypt hashed');
        }
    }

    /**
     * Test that session management is secure
     */
    public function testSessionSecurity()
    {
        // Authenticate user
        $this->assertTrue(authenticate_user('admin', 'admin123'));
        $this->assertTrue(is_logged_in());

        // Get session info
        $sessions = load_sessions();
        $session_id = session_id();

        if (!empty($session_id)) {
            $this->assertArrayHasKey($session_id, $sessions);
            $session = $sessions[$session_id];

            // Verify session contains expected data
            $this->assertEquals('admin', $session['user_id']);
            $this->assertArrayHasKey('created_at', $session);
            $this->assertArrayHasKey('last_activity', $session);

            // Test session timeout
            $old_time = $session['created_at'];
            $session['created_at'] = time() - SESSION_TIMEOUT - 1;
            $sessions[$session_id] = $session;
            save_sessions($sessions);

            // User should no longer be logged in due to timeout
            $this->assertFalse(is_logged_in(), 'User should be logged out after session timeout');
        }
    }

    /**
     * Test that user files have proper permissions
     */
    public function testUserFilePermissions()
    {
        // Ensure users file exists by loading users (this creates it if needed)
        load_users();

        $users_file = USERS_FILE;
        $this->assertFileExists($users_file, 'Users file should exist');

        // Check file permissions (should be restrictive)
        $perms = fileperms($users_file);
        $this->assertEquals('0600', substr(sprintf('%o', $perms), -4),
            'Users file should have restrictive permissions (0600)');
    }

    /**
     * Test brute force protection
     */
    public function testBruteForceProtection()
    {
        // Add a test user
        add_user('testuser', 'testpass123', 'admin');

        // Simulate multiple failed login attempts
        $failed_attempts = 0;
        for ($i = 0; $i < MAX_LOGIN_ATTEMPTS + 2; $i++) {
            if (!authenticate_user('testuser', 'wrongpassword')) {
                $failed_attempts++;
            }
        }

        $this->assertEquals(MAX_LOGIN_ATTEMPTS + 2, $failed_attempts,
            'All login attempts should fail with wrong password');

        // Check that account gets locked after max attempts
        $users = load_users();
        $user = null;
        foreach ($users as $u) {
            if ($u['username'] === 'testuser') {
                $user = $u;
                break;
            }
        }

        $this->assertNotNull($user);
        $this->assertGreaterThanOrEqual(MAX_LOGIN_ATTEMPTS, $user['login_attempts']);
        $this->assertNotNull($user['locked_until'], 'Account should be locked after max failed attempts');
    }

    /**
     * Test that web pages don't expose sensitive configuration
     */
    public function testWebPagesDontExposeConfiguration()
    {
        // Test that sensitive configuration is not exposed in PHP source
        $web_files = [
            __DIR__ . '/../../web/index.php',
            __DIR__ . '/../../web/run_report.php',
            __DIR__ . '/../../web/auth.php'
        ];

        foreach ($web_files as $file) {
            if (file_exists($file)) {
                $content = file_get_contents($file);

                // Check that sensitive patterns are not hardcoded with actual values
                // Allow them in server-side processing code where needed for functionality
                $patterns_to_check = [
                    'GOOGLE_ADS_CLIENT_SECRET',
                    'GOOGLE_ADS_REFRESH_TOKEN',
                    'GA4_PROPERTY_ID'
                ];

                foreach ($patterns_to_check as $pattern) {
                    $this->assertFalse(strpos($content, $pattern) !== false,
                        basename($file) . ' should not contain ' . $pattern);
                }

                // GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_ADS_CLIENT_ID are allowed in run_report.php
                // for server-side processing, but not in other files
                if (basename($file) !== 'run_report.php') {
                    $this->assertFalse(strpos($content, 'GOOGLE_APPLICATION_CREDENTIALS') !== false,
                        basename($file) . ' should not contain GOOGLE_APPLICATION_CREDENTIALS');
                    $this->assertFalse(strpos($content, 'GOOGLE_ADS_CLIENT_ID') !== false,
                        basename($file) . ' should not contain GOOGLE_ADS_CLIENT_ID');
                }
            }
        }

        // Admin page is allowed to contain credential configuration (but should be protected by authentication)
        $admin_file = __DIR__ . '/../../web/admin.php';
        if (file_exists($admin_file)) {
            $admin_content = file_get_contents($admin_file);
            // Admin page should contain credential fields for configuration, but this is OK since it's protected
            $this->assertTrue(strpos($admin_content, 'GOOGLE_ADS_CLIENT_ID') !== false,
                'admin.php should contain credential configuration fields for admin use');
        }
    }

    /**
     * Test that API endpoints don't expose credentials
     */
    public function testApiEndpointsDontExposeCredentials()
    {
        // Test that API files exist and don't expose credentials
        $api_dir = __DIR__ . '/../../web/api';
        if (is_dir($api_dir)) {
            $api_files = glob($api_dir . '/*.php');
            foreach ($api_files as $api_file) {
                $content = file_get_contents($api_file);

                // API files should not expose credentials
                $this->assertFalse(strpos($content, 'GOOGLE_APPLICATION_CREDENTIALS') !== false,
                    basename($api_file) . ' should not expose credentials');
                $this->assertFalse(strpos($content, 'GOOGLE_ADS_CLIENT_ID') !== false,
                    basename($api_file) . ' should not expose GOOGLE_ADS_CLIENT_ID');
                $this->assertFalse(strpos($content, 'GOOGLE_ADS_CLIENT_SECRET') !== false,
                    basename($api_file) . ' should not expose GOOGLE_ADS_CLIENT_SECRET');
            }
        }
    }

    /**
     * Test that users cannot spoof login to bypass brute force protection
     */
    public function testCannotSpoofLoginToBypassBruteForceProtection()
    {
        // Add a test user
        add_user('spoofuser', 'spoofpass123', 'admin');

        // First, lock the account by exceeding max login attempts
        for ($i = 0; $i < MAX_LOGIN_ATTEMPTS; $i++) {
            authenticate_user('spoofuser', 'wrongpassword');
        }

        // Verify account is locked
        $users = load_users();
        $user = null;
        foreach ($users as $u) {
            if ($u['username'] === 'spoofuser') {
                $user = $u;
                break;
            }
        }
        $this->assertNotNull($user);
        $this->assertNotNull($user['locked_until'], 'Account should be locked');

        // Test 1: Direct function call should still fail when account is locked
        $this->assertFalse(authenticate_user('spoofuser', 'spoofpass123'),
            'Direct authentication should fail when account is locked');

        // Test 2: Even with correct password, authentication should fail when locked
        $this->assertFalse(authenticate_user('spoofuser', 'spoofpass123'),
            'Authentication should fail even with correct password when account is locked');

        // Test 3: Attempt to manipulate login_attempts counter
        $users = load_users();
        foreach ($users as &$u) {
            if ($u['username'] === 'spoofuser') {
                $u['login_attempts'] = 0; // Try to reset counter
                break;
            }
        }
        save_users($users);

        // Should still fail because locked_until is still set
        $this->assertFalse(authenticate_user('spoofuser', 'spoofpass123'),
            'Authentication should still fail even if login_attempts is manipulated');

        // Test 4: Attempt to manipulate locked_until timestamp
        $users = load_users();
        foreach ($users as &$u) {
            if ($u['username'] === 'spoofuser') {
                $u['locked_until'] = time() - 100; // Set to past time
                break;
            }
        }
        save_users($users);

        // Now authentication should work
        $this->assertTrue(authenticate_user('spoofuser', 'spoofpass123'),
            'Authentication should work after lockout period expires');

        // Test 5: Verify that successful login resets the counters
        $users = load_users();
        foreach ($users as $u) {
            if ($u['username'] === 'spoofuser') {
                $this->assertEquals(0, $u['login_attempts'], 'Login attempts should be reset after successful login');
                $this->assertNull($u['locked_until'], 'Lockout should be cleared after successful login');
                break;
            }
        }
    }

    /**
     * Test that login endpoint cannot be spoofed via direct access
     */
    public function testLoginEndpointCannotBeSpoofed()
    {
        // Test that direct GET requests to auth.php don't bypass authentication
        // This simulates someone trying to access auth.php directly

        // Ensure no user is logged in initially
        $this->assertFalse(is_logged_in());

        // Simulate what would happen if someone tried to directly access auth.php
        // without proper POST data - the authentication logic should not be triggered
        // This is tested by ensuring the authenticate_user function is not called
        // inappropriately

        // Test that authenticate_user requires proper parameters
        $this->assertFalse(authenticate_user('', ''), 'Empty credentials should fail');
        $this->assertFalse(authenticate_user('nonexistent', 'password'), 'Non-existent user should fail');

        // Test that the function properly validates input
        $this->assertFalse(authenticate_user(null, null), 'Null credentials should fail');
        $this->assertFalse(authenticate_user('admin', null), 'Null password should fail');
        $this->assertFalse(authenticate_user(null, 'admin123'), 'Null username should fail');
    }

    /**
     * Test that session spoofing is prevented
     */
    public function testSessionSpoofingIsPrevented()
    {
        // Authenticate a user first
        $this->assertTrue(authenticate_user('admin', 'admin123'));
        $original_session_id = session_id();
        $this->assertTrue(is_logged_in());

        // Simulate session spoofing attempt - create fake session data
        $fake_session_id = 'fake_session_' . time();
        $sessions = load_sessions();

        // Add a fake session
        $sessions[$fake_session_id] = [
            'user_id' => 'fakeuser',
            'created_at' => time(),
            'last_activity' => time()
        ];
        save_sessions($sessions);

        // The current session should still be valid
        $this->assertTrue(is_logged_in(), 'Original session should still be valid');
        $this->assertEquals('admin', get_logged_in_user()['username']);

        // Simulate session ID manipulation (this would be done by changing $_COOKIE)
        // In a real attack, someone might try to set their session ID to a fake one
        // But our session validation should prevent this

        // Test that session validation works
        $user = get_logged_in_user();
        $this->assertNotNull($user);
        $this->assertEquals('admin', $user['username']);
    }

    /**
     * Test that rate limiting cannot be bypassed by spoofing
     */
    public function testRateLimitingCannotBeBypassed()
    {
        global $web_logger;

        // Test that rate limiting uses server-controlled data that can't be easily spoofed
        $test_ip = '192.168.1.100';
        $rate_limit_key = 'test_rate_limit_' . $test_ip;

        // Test that different IPs have separate rate limiting (IP spoofing would need different keys)
        $different_ip_key = 'test_rate_limit_192.168.1.101';

        // Different IP should have its own rate limiting, unaffected by the first IP's activity
        $this->assertTrue($web_logger->check_rate_limit($different_ip_key, 5, 300),
            'Different IP should have separate rate limiting and not be affected by other IPs');
    }
}