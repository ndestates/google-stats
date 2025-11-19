<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Settings - Google Analytics Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .settings-card { margin-bottom: 20px; }
        .current-logo { max-width: 200px; max-height: 100px; border: 1px solid #ddd; padding: 5px; }
        .logo-preview { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
    </style>
</head>
<body>
    <?php
    // Start session for authentication
    session_start();

    // Include authentication functions
    require_once 'auth.php';

    // Include version information
    require_once 'version.php';

    // Check if user is logged in
    if (!is_logged_in()) {
        // Check if IP is blocked
        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        if ($web_logger->is_ip_blocked($ip)) {
            http_response_code(403);
            echo '<h1>Access Denied</h1><p>Your IP address has been blocked due to security policy.</p>';
            exit;
        }

        // Show login form
        ?>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h4 class="mb-0"><i class="fas fa-lock"></i> Admin Login</h4>
                        </div>
                        <div class="card-body">
                            <?php if (isset($_GET['error'])): ?>
                                <div class="alert alert-danger">
                                    <i class="fas fa-exclamation-triangle"></i>
                                    <?php
                                    switch ($_GET['error']) {
                                        case 'invalid':
                                            echo 'Invalid username or password.';
                                            break;
                                        case 'locked':
                                            echo 'Account is temporarily locked due to too many failed attempts.';
                                            break;
                                        default:
                                            echo 'Login failed.';
                                    }
                                    ?>
                                </div>
                            <?php endif; ?>

                            <form method="POST" action="auth.php?action=login">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary">
                                        <i class="fas fa-sign-in-alt"></i> Login
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <?php
        exit;
    }

    // User is logged in, show admin interface
    $current_user = get_logged_in_user();
    ?>

    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.php">
                <i class="fas fa-chart-line"></i> Google Analytics Platform
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="index.php">Reports</a>
                <a class="nav-link active" href="admin.php">Admin Settings</a>
                <span class="navbar-text me-3">Welcome, <?php echo htmlspecialchars($current_user['username']); ?></span>
                <a class="nav-link" href="auth.php?action=logout">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row">
            <div class="col-md-8 mx-auto">
                <h2 class="mb-4"><i class="fas fa-cog"></i> Admin Settings</h2>

                <?php
                // Load current settings
                $settings_file = __DIR__ . '/uploads/settings.json';
                $settings = [];
                if (file_exists($settings_file)) {
                    $settings_content = file_get_contents($settings_file);
                    if ($settings_content !== false) {
                        $settings = json_decode($settings_content, true) ?: [];
                    }
                } else {
                    // Initialize empty settings file
                    file_put_contents($settings_file, '{}');
                }

                // Initialize message variables
                $success_message = null;
                $error_message = null;

                // Handle form submission
                if ($_SERVER['REQUEST_METHOD'] === 'POST') {

                    // Handle logo upload
                    if (isset($_FILES['company_logo']) && $_FILES['company_logo']['error'] === UPLOAD_ERR_OK) {
                        $allowed_types = ['image/jpeg', 'image/png', 'image/gif'];
                        $file_type = $_FILES['company_logo']['type'];

                        if (in_array($file_type, $allowed_types)) {
                            $file_extension = pathinfo($_FILES['company_logo']['name'], PATHINFO_EXTENSION);
                            $logo_filename = 'company_logo_' . time() . '.' . $file_extension;
                            $logo_path = __DIR__ . '/uploads/logos/' . $logo_filename;

                            if (move_uploaded_file($_FILES['company_logo']['tmp_name'], $logo_path)) {
                                // Delete old logo if exists
                                if ($settings['company_logo'] && file_exists(__DIR__ . '/' . $settings['company_logo'])) {
                                    unlink(__DIR__ . '/' . $settings['company_logo']);
                                }

                                $settings['company_logo'] = 'uploads/logos/' . $logo_filename;
                                $success_message = 'Company logo uploaded successfully!';
                            } else {
                                $error_message = 'Failed to save logo file.';
                            }
                        } else {
                            $error_message = 'Invalid file type. Only JPG, PNG, and GIF are allowed.';
                        }
                    }

                    // Handle settings update
                    if (isset($_POST['action']) && $_POST['action'] === 'update_settings') {
                        // Handle property settings
                        $settings['default_property_name'] = $_POST['default_property_name'] ?? '';
                        $settings['default_property_address'] = $_POST['default_property_address'] ?? '';
                        $settings['updated_at'] = date('Y-m-d H:i:s');

                        // Save settings
                        if (file_put_contents($settings_file, json_encode($settings, JSON_PRETTY_PRINT))) {
                            if (!$error_message) {
                                $success_message = $success_message ?: 'Settings saved successfully!';
                            }
                        } else {
                            $error_message = 'Failed to save settings.';
                        }
                    }

                    // Handle credential import
                    if (isset($_POST['action']) && $_POST['action'] === 'import_credentials') {
                        require_once 'credentials.php';
                        $env_path = dirname(__DIR__) . '/.env';
                        if (import_from_env($env_path)) {
                            $success_message = 'Credentials imported successfully from .env file!';
                        } else {
                            $error_message = 'Failed to import credentials or no valid credentials found in .env file.';
                        }
                    }

                    // Handle credential update
                    if (isset($_POST['action']) && $_POST['action'] === 'update_credentials') {
                        require_once 'credentials.php';
                        $credential_keys = [
                            'GA4_PROPERTY_ID', 'GA4_KEY_PATH',
                            'GOOGLE_ADS_CUSTOMER_ID', 'GOOGLE_ADS_CLIENT_ID', 'GOOGLE_ADS_CLIENT_SECRET',
                            'GOOGLE_ADS_REFRESH_TOKEN', 'GOOGLE_ADS_DEVELOPER_TOKEN',
                            'GSC_SITE_URL', 'GSC_KEY_PATH'
                        ];

                        try {
                            foreach ($credential_keys as $key) {
                                if (isset($_POST[$key]) && $_POST[$key] !== '') {
                                    update_credential($key, $_POST[$key]);
                                }
                            }
                            $success_message = 'Credentials updated successfully!';
                        } catch (Exception $e) {
                            $error_message = 'Failed to save credentials: ' . $e->getMessage();
                        }
                    }
                }
                ?>

                <?php if ($success_message): ?>
                    <div class="alert alert-success">
                        <i class="fas fa-check-circle"></i> <?php echo $success_message; ?>
                    </div>
                <?php endif; ?>

                <?php if ($error_message): ?>
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> <?php echo $error_message; ?>
                    </div>
                <?php endif; ?>

                <?php
                // Handle user management messages
                if (isset($_GET['success'])) {
                    $success_messages = [
                        'user_added' => 'User added successfully!',
                        'user_deleted' => 'User deleted successfully!',
                        'password_changed' => 'Password changed successfully!'
                    ];
                    if (isset($success_messages[$_GET['success']])) {
                        echo '<div class="alert alert-success"><i class="fas fa-check-circle"></i> ' . $success_messages[$_GET['success']] . '</div>';
                    }
                }
                if (isset($_GET['error'])) {
                    $error_messages = [
                        'user_exists' => 'Username already exists.',
                        'password_mismatch' => 'Passwords do not match.',
                        'cannot_delete_self' => 'You cannot delete your own account.',
                        'wrong_current_password' => 'Current password is incorrect.'
                    ];
                    if (isset($error_messages[$_GET['error']])) {
                        echo '<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> ' . $error_messages[$_GET['error']] . '</div>';
                    }
                }
                ?>

                <form method="POST" enctype="multipart/form-data">
                    <input type="hidden" name="action" value="update_settings">
                    <!-- Company Logo Section -->
                    <div class="card settings-card">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-image"></i> Company Logo</h5>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">Upload your company logo to appear on all PDF reports. Recommended size: 300x150 pixels.</p>

                            <?php if (!empty($settings['company_logo']) && file_exists(__DIR__ . '/' . $settings['company_logo'])): ?>
                                <div class="logo-preview mb-3">
                                    <p><strong>Current Logo:</strong></p>
                                    <img src="<?php echo $settings['company_logo']; ?>" alt="Company Logo" class="current-logo">
                                </div>
                            <?php endif; ?>

                            <div class="mb-3">
                                <label for="company_logo" class="form-label">Upload New Logo</label>
                                <input type="file" class="form-control" id="company_logo" name="company_logo" accept="image/*">
                                <div class="form-text">Supported formats: JPG, PNG, GIF. Max file size: 5MB.</div>
                            </div>
                        </div>
                    </div>

                    <!-- Default Property Information -->
                    <div class="card settings-card">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-building"></i> Default Property Information</h5>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">Set default property information that will appear on all reports (users can override this when running individual reports).</p>

                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="default_property_name" class="form-label">Default Property Name</label>
                                    <input type="text" class="form-control" id="default_property_name" name="default_property_name"
                                           value="<?php echo htmlspecialchars($settings['default_property_name'] ?? ''); ?>"
                                           placeholder="e.g., Your Company Name">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="default_property_address" class="form-label">Default Property Address</label>
                                    <input type="text" class="form-control" id="default_property_address" name="default_property_address"
                                           value="<?php echo htmlspecialchars($settings['default_property_address'] ?? ''); ?>"
                                           placeholder="e.g., 123 Main Street, City, State">
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="d-grid">
                        <button type="submit" class="btn btn-primary btn-lg">
                            <i class="fas fa-save"></i> Save Settings
                        </button>
                    </div>
                </form>

                <?php if (!empty($settings['updated_at'])): ?>
                    <div class="mt-3 text-muted">
                        <small>Last updated: <?php echo $settings['updated_at']; ?></small>
                    </div>
                <?php endif; ?>

                <!-- User Management Section -->
                <div class="card settings-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-users"></i> User Management</h5>
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Manage admin users and their access to the system.</p>

                        <!-- Current Users List -->
                        <h6>Current Users</h6>
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Role</th>
                                        <th>Created</th>
                                        <th>Last Login</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <?php
                                    $users = load_users();
                                    foreach ($users as $user):
                                    ?>
                                    <tr>
                                        <td><?php echo htmlspecialchars($user['username']); ?></td>
                                        <td><?php echo htmlspecialchars($user['role']); ?></td>
                                        <td><?php echo $user['created_at']; ?></td>
                                        <td><?php echo $user['last_login'] ?: 'Never'; ?></td>
                                        <td>
                                            <?php if ($user['username'] !== $current_user['username']): ?>
                                            <form method="POST" action="auth.php?action=delete_user" class="d-inline"
                                                  onsubmit="return confirm('Are you sure you want to delete this user?')">
                                                <input type="hidden" name="delete_username" value="<?php echo htmlspecialchars($user['username']); ?>">
                                                <button type="submit" class="btn btn-sm btn-outline-danger">
                                                    <i class="fas fa-trash"></i> Delete
                                                </button>
                                            </form>
                                            <?php endif; ?>
                                        </td>
                                    </tr>
                                    <?php endforeach; ?>
                                </tbody>
                            </table>
                        </div>

                        <!-- Add New User -->
                        <h6 class="mt-4">Add New User</h6>
                        <form method="POST" action="auth.php?action=add_user">
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label for="new_username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="new_username" name="new_username" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label for="new_password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="new_password" name="new_password" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label for="confirm_password" class="form-label">Confirm Password</label>
                                    <input type="password" class="form-control" id="confirm_password" name="confirm_password" required>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-user-plus"></i> Add User
                            </button>
                        </form>

                        <!-- Change Password -->
                        <h6 class="mt-4">Change Your Password</h6>
                        <form method="POST" action="auth.php?action=change_password">
                            <div class="row">
                                <div class="col-md-4 mb-3">
                                    <label for="current_password" class="form-label">Current Password</label>
                                    <input type="password" class="form-control" id="current_password" name="current_password" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label for="new_password_change" class="form-label">New Password</label>
                                    <input type="password" class="form-control" id="new_password_change" name="new_password_change" required>
                                </div>
                                <div class="col-md-4 mb-3">
                                    <label for="confirm_password_change" class="form-label">Confirm New Password</label>
                                    <input type="password" class="form-control" id="confirm_password_change" name="confirm_password_change" required>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-warning">
                                <i class="fas fa-key"></i> Change Password
                            </button>
                        </form>
                    </div>
                </div>

                <!-- Google Credentials Management Section -->
                <div class="card settings-card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fab fa-google"></i> Google API Credentials</h5>
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Manage Google Analytics 4, Google Ads, and Search Console credentials securely.</p>

                        <?php
                        require_once 'credentials.php';
                        $credentials = load_credentials();
                        ?>

                        <!-- Current Credentials Status -->
                        <h6>Current Credentials Status</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <div class="card <?php echo validate_ga4_credentials($credentials) ? 'border-success' : 'border-warning'; ?>">
                                    <div class="card-body text-center">
                                        <i class="fab fa-google fa-2x mb-2 <?php echo validate_ga4_credentials($credentials) ? 'text-success' : 'text-warning'; ?>"></i>
                                        <h6>GA4 Analytics</h6>
                                        <small class="text-muted">
                                            <?php echo validate_ga4_credentials($credentials) ? 'Configured' : 'Not Configured'; ?>
                                        </small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card <?php echo validate_google_ads_credentials($credentials) ? 'border-success' : 'border-warning'; ?>">
                                    <div class="card-body text-center">
                                        <i class="fas fa-ad fa-2x mb-2 <?php echo validate_google_ads_credentials($credentials) ? 'text-success' : 'text-warning'; ?>"></i>
                                        <h6>Google Ads</h6>
                                        <small class="text-muted">
                                            <?php echo validate_google_ads_credentials($credentials) ? 'Configured' : 'Not Configured'; ?>
                                        </small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card border-info">
                                    <div class="card-body text-center">
                                        <i class="fab fa-google fa-2x mb-2 text-info"></i>
                                        <h6>Search Console</h6>
                                        <small class="text-muted">Check Settings</small>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Import from .env -->
                        <h6 class="mt-4">Import Credentials</h6>
                        <p class="text-muted">Import existing credentials from your .env file (one-time migration).</p>
                        <form method="POST" action="admin.php">
                            <input type="hidden" name="action" value="import_credentials">
                            <button type="submit" class="btn btn-info">
                                <i class="fas fa-upload"></i> Import from .env
                            </button>
                        </form>

                        <!-- Manual Credential Entry -->
                        <h6 class="mt-4">Manual Credential Entry</h6>
                        <form method="POST" action="admin.php">
                            <input type="hidden" name="action" value="update_credentials">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6>GA4 Analytics</h6>
                                    <div class="mb-3">
                                        <label for="ga4_property_id" class="form-label">GA4 Property ID</label>
                                        <input type="text" class="form-control" id="ga4_property_id" name="GA4_PROPERTY_ID"
                                               value="<?php echo htmlspecialchars($credentials['GA4_PROPERTY_ID'] ?? ''); ?>"
                                               placeholder="e.g., 275378361">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ga4_key_path" class="form-label">GA4 Key Path</label>
                                        <input type="text" class="form-control" id="ga4_key_path" name="GA4_KEY_PATH"
                                               value="<?php echo htmlspecialchars($credentials['GA4_KEY_PATH'] ?? ''); ?>"
                                               placeholder="e.g., /var/www/html/.ddev/keys/ga4-key.json">
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <h6>Google Ads</h6>
                                    <div class="mb-3">
                                        <label for="ads_customer_id" class="form-label">Customer ID</label>
                                        <input type="text" class="form-control" id="ads_customer_id" name="GOOGLE_ADS_CUSTOMER_ID"
                                               value="<?php echo htmlspecialchars($credentials['GOOGLE_ADS_CUSTOMER_ID'] ?? ''); ?>"
                                               placeholder="e.g., 1234567890">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ads_client_id" class="form-label">Client ID</label>
                                        <input type="text" class="form-control" id="ads_client_id" name="GOOGLE_ADS_CLIENT_ID"
                                               value="<?php echo htmlspecialchars($credentials['GOOGLE_ADS_CLIENT_ID'] ?? ''); ?>">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ads_client_secret" class="form-label">Client Secret</label>
                                        <input type="password" class="form-control" id="ads_client_secret" name="GOOGLE_ADS_CLIENT_SECRET"
                                               value="<?php echo htmlspecialchars($credentials['GOOGLE_ADS_CLIENT_SECRET'] ?? ''); ?>">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ads_refresh_token" class="form-label">Refresh Token</label>
                                        <input type="password" class="form-control" id="ads_refresh_token" name="GOOGLE_ADS_REFRESH_TOKEN"
                                               value="<?php echo htmlspecialchars($credentials['GOOGLE_ADS_REFRESH_TOKEN'] ?? ''); ?>">
                                    </div>
                                    <div class="mb-3">
                                        <label for="ads_developer_token" class="form-label">Developer Token</label>
                                        <input type="password" class="form-control" id="ads_developer_token" name="GOOGLE_ADS_DEVELOPER_TOKEN"
                                               value="<?php echo htmlspecialchars($credentials['GOOGLE_ADS_DEVELOPER_TOKEN'] ?? ''); ?>">
                                    </div>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-save"></i> Save Credentials
                            </button>
                        </form>

                        <!-- Setup Instructions -->
                        <div class="mt-4">
                            <h6>Setup Instructions</h6>
                            <div class="accordion" id="credentialsAccordion">
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#ga4-setup">
                                            GA4 Analytics Setup
                                        </button>
                                    </h2>
                                    <div id="ga4-setup" class="accordion-collapse collapse" data-bs-parent="#credentialsAccordion">
                                        <div class="accordion-body">
                                            <ol>
                                                <li>Go to <a href="https://console.cloud.google.com" target="_blank">Google Cloud Console</a></li>
                                                <li>Create a new project or select existing</li>
                                                <li>Enable Google Analytics Data API</li>
                                                <li>Create a service account and download JSON key</li>
                                                <li>Add service account to GA4 property with Viewer role</li>
                                                <li>Enter Property ID and key path above</li>
                                            </ol>
                                        </div>
                                    </div>
                                </div>
                                <div class="accordion-item">
                                    <h2 class="accordion-header">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#ads-setup">
                                            Google Ads Setup
                                        </button>
                                    </h2>
                                    <div id="ads-setup" class="accordion-collapse collapse" data-bs-parent="#credentialsAccordion">
                                        <div class="accordion-body">
                                            <ol>
                                                <li>Get your Customer ID from Google Ads</li>
                                                <li>Create OAuth 2.0 credentials in Google Cloud Console</li>
                                                <li>Apply for Developer Token</li>
                                                <li>Use OAuth Playground to get refresh token</li>
                                                <li>Enter all credentials above</li>
                                            </ol>
                                            <p><a href="README_Google_Ads_Credentials.md" target="_blank">Detailed Instructions</a></p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>

    <footer class="text-center text-muted mt-5 py-3 border-top">
        <p>&copy; <?php echo APP_COPYRIGHT; ?> | Version <?php echo APP_VERSION; ?> | Powered by Google Analytics 4</p>
    </footer>
</body>
</html>