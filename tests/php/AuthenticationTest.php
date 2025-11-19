<?php

use PHPUnit\Framework\TestCase;

class AuthenticationTest extends TestCase
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

        // Reset session - only destroy if active, don't start new session
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
        // Don't start session here - let auth.php handle it conditionally
    }

    protected function tearDown(): void
    {
        // Clean up after each test
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_destroy();
        }
    }

    public function testUserInitialization()
    {
        // Test that init_users_file creates default admin user
        $users = load_users();
        $this->assertIsArray($users);
        $this->assertCount(1, $users);
        $this->assertEquals('admin', $users[0]['username']);
        $this->assertTrue(password_verify('admin123', $users[0]['password_hash']));
        $this->assertEquals('admin', $users[0]['role']);
    }

    public function testPasswordHashing()
    {
        $password = 'testpassword123';
        $hash = password_hash($password, PASSWORD_BCRYPT);

        $this->assertTrue(password_verify($password, $hash));
        $this->assertFalse(password_verify('wrongpassword', $hash));
    }

    public function testAddUser()
    {
        $username = 'testuser';
        $password = 'testpass123';

        $result = add_user($username, $password, 'admin');
        $this->assertTrue($result);

        $users = load_users();
        $this->assertCount(2, $users); // default admin + new user

        $newUser = null;
        foreach ($users as $user) {
            if ($user['username'] === $username) {
                $newUser = $user;
                break;
            }
        }

        $this->assertNotNull($newUser);
        $this->assertEquals('admin', $newUser['role']);
        $this->assertTrue(password_verify($password, $newUser['password_hash']));
    }

    public function testAddDuplicateUser()
    {
        $username = 'admin'; // already exists
        $password = 'newpassword123';

        $result = add_user($username, $password, 'admin');
        $this->assertFalse($result);

        $users = load_users();
        $this->assertCount(1, $users); // should still be only 1 user
    }

    public function testAuthenticateValidUser()
    {
        $username = 'admin';
        $password = 'admin123';

        $result = authenticate_user($username, $password);
        $this->assertTrue($result);
        $this->assertTrue(is_logged_in());

        $currentUser = get_logged_in_user();
        $this->assertNotNull($currentUser);
        $this->assertEquals($username, $currentUser['username']);
    }

    public function testAuthenticateInvalidUser()
    {
        $username = 'nonexistent';
        $password = 'password123';

        $result = authenticate_user($username, $password);
        $this->assertFalse($result);
        $this->assertFalse(is_logged_in());
    }

    public function testAuthenticateWrongPassword()
    {
        $username = 'admin';
        $password = 'wrongpassword';

        $result = authenticate_user($username, $password);
        $this->assertFalse($result);
        $this->assertFalse(is_logged_in());
    }

    public function testSessionPersistence()
    {
        // Login
        authenticate_user('admin', 'admin123');
        $this->assertTrue(is_logged_in());

        $user1 = get_logged_in_user();
        $this->assertEquals('admin', $user1['username']);

        // Simulate session continuation (same session ID)
        $user2 = get_logged_in_user();
        $this->assertEquals('admin', $user2['username']);
    }

    public function testLogout()
    {
        // Login first
        authenticate_user('admin', 'admin123');
        $this->assertTrue(is_logged_in());

        // Logout
        logout_user();
        $this->assertFalse(is_logged_in());

        $currentUser = get_logged_in_user();
        $this->assertNull($currentUser);
    }

    public function testChangePassword()
    {
        $username = 'admin';
        $newPassword = 'newsecurepassword123';

        $result = change_password($username, $newPassword);
        $this->assertTrue($result);

        // Verify old password no longer works
        $this->assertFalse(authenticate_user($username, 'admin123'));

        // Verify new password works
        $this->assertTrue(authenticate_user($username, $newPassword));
    }

    public function testDeleteUser()
    {
        // Add a test user first
        add_user('testuser', 'testpass', 'admin');
        $users = load_users();
        $this->assertCount(2, $users);

        // Delete the test user
        $result = delete_user('testuser');
        $this->assertTrue($result);

        $users = load_users();
        $this->assertCount(1, $users);
        $this->assertEquals('admin', $users[0]['username']);
    }

    public function testDeleteNonexistentUser()
    {
        $result = delete_user('nonexistent');
        $this->assertFalse($result);
    }

    public function testAccountLockout()
    {
        $username = 'admin';

        // Simulate multiple failed login attempts
        for ($i = 0; $i < MAX_LOGIN_ATTEMPTS; $i++) {
            authenticate_user($username, 'wrongpassword');
        }

        // Check that account is locked
        $users = load_users();
        $adminUser = $users[0];
        $this->assertGreaterThan(time(), $adminUser['locked_until']);

        // Verify login is blocked
        $result = authenticate_user($username, 'admin123');
        $this->assertFalse($result);
    }

    public function testSessionTimeout()
    {
        // Login
        authenticate_user('admin', 'admin123');
        $this->assertTrue(is_logged_in());

        // Manually set session creation time to past
        $sessions = load_sessions();
        $sessionId = test_session_id();
        $sessions[$sessionId]['created_at'] = time() - SESSION_TIMEOUT - 1;
        save_sessions($sessions);

        // Session should now be invalid
        $this->assertFalse(is_logged_in());
    }
}