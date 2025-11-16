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
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.php">
                <i class="fas fa-chart-line"></i> Google Analytics Platform
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="index.php">Reports</a>
                <a class="nav-link active" href="admin.php">Admin Settings</a>
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
                $settings = json_decode(file_get_contents($settings_file), true);

                // Handle form submission
                if ($_SERVER['REQUEST_METHOD'] === 'POST') {
                    $success_message = null;
                    $error_message = null;

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

                <form method="POST" enctype="multipart/form-data">
                    <!-- Company Logo Section -->
                    <div class="card settings-card">
                        <div class="card-header">
                            <h5 class="mb-0"><i class="fas fa-image"></i> Company Logo</h5>
                        </div>
                        <div class="card-body">
                            <p class="text-muted">Upload your company logo to appear on all PDF reports. Recommended size: 300x150 pixels.</p>

                            <?php if ($settings['company_logo'] && file_exists(__DIR__ . '/' . $settings['company_logo'])): ?>
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

                <?php if ($settings['updated_at']): ?>
                    <div class="mt-3 text-muted">
                        <small>Last updated: <?php echo $settings['updated_at']; ?></small>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>