<?php

use PHPUnit\Framework\TestCase;

class CredentialsTest extends TestCase
{
    protected function setUp(): void
    {
        // Clean up before each test
        $testFiles = [
            __DIR__ . '/../../web/uploads/test_credentials.enc',
            __DIR__ . '/../../web/uploads/master_key.txt'
        ];
        foreach ($testFiles as $file) {
            if (file_exists($file)) {
                unlink($file);
            }
        }

        // Set test environment variable for master key
        putenv('CREDENTIALS_MASTER_KEY=test_master_key_12345678901234567890');
    }

    protected function tearDown(): void
    {
        // Clean up after each test
        putenv('CREDENTIALS_MASTER_KEY');
    }

    public function testCredentialEncryptionDecryption()
    {
        $testData = ['key1' => 'value1', 'key2' => 'value2'];
        $key = 'test_encryption_key_12345678901234567890';

        $encrypted = encrypt_data(json_encode($testData), $key);
        $this->assertNotEmpty($encrypted);
        $this->assertNotEquals(json_encode($testData), $encrypted);

        $decrypted = decrypt_data($encrypted, $key);
        $this->assertEquals(json_encode($testData), $decrypted);

        $decoded = json_decode($decrypted, true);
        $this->assertEquals($testData, $decoded);
    }

    public function testSaveAndLoadCredentials()
    {
        $testCredentials = [
            'GA4_PROPERTY_ID' => '123456789',
            'GOOGLE_ADS_CUSTOMER_ID' => '1234567890',
            'GOOGLE_ADS_CLIENT_ID' => 'test-client-id.googleusercontent.com'
        ];

        save_credentials($testCredentials);
        $this->assertFileExists(CREDENTIALS_FILE);

        $loadedCredentials = load_credentials();
        $this->assertEquals($testCredentials, $loadedCredentials);
    }

    public function testUpdateCredential()
    {
        $initialCredentials = ['TEST_KEY' => 'initial_value'];
        save_credentials($initialCredentials);

        update_credential('TEST_KEY', 'updated_value');
        update_credential('NEW_KEY', 'new_value');

        $loadedCredentials = load_credentials();
        $expected = [
            'TEST_KEY' => 'updated_value',
            'NEW_KEY' => 'new_value'
        ];
        $this->assertEquals($expected, $loadedCredentials);
    }

    public function testGetCredential()
    {
        $testCredentials = [
            'EXISTING_KEY' => 'existing_value',
            'ANOTHER_KEY' => 'another_value'
        ];
        save_credentials($testCredentials);

        $this->assertEquals('existing_value', get_credential('EXISTING_KEY'));
        $this->assertEquals('another_value', get_credential('ANOTHER_KEY'));
        $this->assertNull(get_credential('NONEXISTENT_KEY'));
    }

    public function testValidateGa4Credentials()
    {
        // Valid GA4 credentials
        $validCredentials = [
            'GA4_PROPERTY_ID' => '123456789',
            'GA4_KEY_PATH' => '/path/to/key.json'
        ];
        $this->assertTrue(validate_ga4_credentials($validCredentials));

        // Invalid - missing property ID
        $invalidCredentials1 = [
            'GA4_KEY_PATH' => '/path/to/key.json'
        ];
        $this->assertFalse(validate_ga4_credentials($invalidCredentials1));

        // Invalid - non-numeric property ID
        $invalidCredentials2 = [
            'GA4_PROPERTY_ID' => 'not-a-number',
            'GA4_KEY_PATH' => '/path/to/key.json'
        ];
        $this->assertFalse(validate_ga4_credentials($invalidCredentials2));
    }

    public function testValidateGoogleAdsCredentials()
    {
        // Valid Google Ads credentials
        $validCredentials = [
            'GOOGLE_ADS_CUSTOMER_ID' => '1234567890',
            'GOOGLE_ADS_CLIENT_ID' => 'test-client-id.googleusercontent.com',
            'GOOGLE_ADS_CLIENT_SECRET' => 'test-secret',
            'GOOGLE_ADS_REFRESH_TOKEN' => 'test-refresh-token',
            'GOOGLE_ADS_DEVELOPER_TOKEN' => 'test-developer-token'
        ];
        $this->assertTrue(validate_google_ads_credentials($validCredentials));

        // Invalid - wrong customer ID format
        $invalidCredentials1 = array_merge($validCredentials, [
            'GOOGLE_ADS_CUSTOMER_ID' => '123-456-7890' // dashes not allowed
        ]);
        $this->assertFalse(validate_google_ads_credentials($invalidCredentials1));

        // Invalid - wrong client ID format
        $invalidCredentials2 = array_merge($validCredentials, [
            'GOOGLE_ADS_CLIENT_ID' => 'not-a-google-client-id'
        ]);
        $this->assertFalse(validate_google_ads_credentials($invalidCredentials2));

        // Invalid - missing required field
        $invalidCredentials3 = $validCredentials;
        unset($invalidCredentials3['GOOGLE_ADS_CLIENT_SECRET']);
        $this->assertFalse(validate_google_ads_credentials($invalidCredentials3));
    }

    public function testImportFromEnv()
    {
        // Create a mock .env file
        $envContent = <<<'EOD'
# Comment line
GA4_PROPERTY_ID=987654321
GOOGLE_ADS_CUSTOMER_ID=1234567890
GOOGLE_ADS_CLIENT_ID=test-client-id.googleusercontent.com
NON_GOOGLE_KEY=should_be_ignored
# Another comment
GA4_KEY_PATH=/path/to/ga4/key.json
EOD;

        $tempEnvFile = tempnam(sys_get_temp_dir(), 'test_env');
        file_put_contents($tempEnvFile, $envContent);

        try {
            $result = import_from_env($tempEnvFile);
            $this->assertTrue($result);

            $loadedCredentials = load_credentials();
            $expected = [
                'GA4_PROPERTY_ID' => '987654321',
                'GOOGLE_ADS_CUSTOMER_ID' => '1234567890',
                'GOOGLE_ADS_CLIENT_ID' => 'test-client-id.googleusercontent.com',
                'GA4_KEY_PATH' => '/path/to/ga4/key.json'
            ];
            $this->assertEquals($expected, $loadedCredentials);
        } finally {
            unlink($tempEnvFile);
        }
    }

    public function testLoadCredentialsToEnv()
    {
        $testCredentials = [
            'TEST_ENV_VAR' => 'test_value',
            'ANOTHER_VAR' => 'another_value'
        ];
        save_credentials($testCredentials);

        // Clear any existing env vars
        putenv('TEST_ENV_VAR');
        putenv('ANOTHER_VAR');

        load_credentials_to_env();

        $this->assertEquals('test_value', getenv('TEST_ENV_VAR'));
        $this->assertEquals('another_value', getenv('ANOTHER_VAR'));
    }

    public function testMasterKeyGeneration()
    {
        // Test with no environment variable set
        putenv('CREDENTIALS_MASTER_KEY');

        $key1 = get_master_key();
        $this->assertEquals(64, strlen($key1)); // 32 bytes * 2 for hex

        $key2 = get_master_key();
        $this->assertEquals($key1, $key2); // Should be consistent
    }
}