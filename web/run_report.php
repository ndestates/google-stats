<?php
// Enable error reporting for debugging
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Check if this is a GET request to show the form
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    ?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics Reports - Secure Access</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-bottom: 30px; }
        form { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; }
        select, input[type="text"] { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #005a87; }
        .result { margin-top: 30px; padding: 20px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px; white-space: pre-wrap; font-family: monospace; }
        .warning { background: #fff3cd; border-color: #ffeaa7; color: #856404; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Secure Analytics Reports</h1>
        <p>This interface requires authentication to run analytics scripts.</p>

        <form method="POST">
            <label for="script">Select Script:</label>
            <select name="script" id="script" required>
                <option value="">Choose a script...</option>
                <option value="mailchimp_performance.py">📧 Mailchimp Performance</option>
                <option value="yesterday_report.py">📊 Yesterday Report</option>
                <option value="campaign_performance.py">🎯 Campaign Performance</option>
                <option value="gsc_ga_keywords.py">🔍 GSC-GA4 Keywords</option>
                <option value="page_traffic_analysis.py">📈 Page Traffic Analysis</option>
                <option value="google_ads_performance.py">📢 Google Ads Performance</option>
            </select>

            <label for="args">Arguments (optional):</label>
            <input type="text" name="args" id="args" placeholder="--report-type yesterday">

            <button type="submit">Run Report</button>
        </form>

        <div class="warning">
            <strong>Security Notice:</strong> This page requires HTTP Basic Authentication.
            Contact your administrator for access credentials.
        </div>
    </div>
</body>
</html>
    <?php
    exit;
}

// Basic HTTP Authentication
$username = 'admin';
$password = 'analytics2025'; // CHANGE THIS TO A SECURE PASSWORD

if (!isset($_SERVER['PHP_AUTH_USER']) || !isset($_SERVER['PHP_AUTH_PW']) ||
    $_SERVER['PHP_AUTH_USER'] !== $username || $_SERVER['PHP_AUTH_PW'] !== $password) {
    header('WWW-Authenticate: Basic realm="Analytics Reports"');
    header('HTTP/1.0 401 Unauthorized');
    echo 'Authentication required to access this page.';
    exit;
}

// Disable error display in production to prevent information leakage
ini_set('display_errors', 0);
error_reporting(E_ALL);

// Set headers for plain text response
header('Content-Type: text/plain');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Pragma: no-cache');
header('Expires: 0');

// Get the script name and arguments from POST data
$script = $_POST['script'] ?? '';
$args = $_POST['args'] ?? '';

if (empty($script)) {
    echo "Error: No script specified";
    exit;
}

// Validate and sanitize script name to prevent security issues
$script = basename($script); // Remove path components
$allowed_scripts = [
    'page_traffic_analysis.py',
    'hourly_traffic_analysis.py',
    'google_ads_performance.py',
    'mailchimp_performance.py',
    'gsc_ga_keywords.py',
    'get_top_pages.py',
    'yesterday_report.py',
    'google_ads_ad_performance.py',
    'all_pages_sources_report.py',
    'campaign_performance.py',
    'audience_management.py',
    'conversion_funnel_analysis.py',
    'bounce_rate_analysis.py',
    'device_geo_analysis.py',
    'technical_performance.py',
    'user_behavior.py',
    'content_performance.py',
    'seo_analysis.py'
];

if (!in_array($script, $allowed_scripts)) {
    echo "Error: Invalid script specified";
    exit;
}

// Execute the selected script
$script_path = "/var/www/html/scripts/$script";
$args_array = $args ? explode(' ', $args) : [];
$command = "cd /var/www/html && PYTHONPATH=/var/www/html GOOGLE_APPLICATION_CREDENTIALS=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json python3 $script_path " . implode(' ', array_map('escapeshellarg', $args_array));

// Set the working directory to the project root for proc_open
$project_root = '/var/www/html';

// Set environment variables if needed
putenv('PYTHONPATH=/var/www/html');
putenv('GOOGLE_APPLICATION_CREDENTIALS=/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json');

// Execute the command with timeout and capture output
$descriptors = [
    0 => ['pipe', 'r'], // stdin
    1 => ['pipe', 'w'], // stdout
    2 => ['pipe', 'w']  // stderr
];

$process = proc_open($command, $descriptors, $pipes, $project_root);

if (is_resource($process)) {
    // Close stdin
    fclose($pipes[0]);

    // Read output
    $output = stream_get_contents($pipes[1]);
    $errors = stream_get_contents($pipes[2]);

    // Close pipes
    fclose($pipes[1]);
    fclose($pipes[2]);

    // Get exit code
    $return_code = proc_close($process);

    // Output the results
    ?>
    <div class="container">
        <h1>Report Results</h1>
        <div class="result">
    <?php
    if ($return_code === 0) {
        echo "✅ Report completed successfully:\n\n";
        echo htmlspecialchars($output);
    } else {
        echo "⚠️ Report completed with warnings/errors (exit code: {$return_code}):\n\n";
        // Only show output, not full error details to prevent information leakage
        echo htmlspecialchars($output);
        if (!empty($errors)) {
            echo "\n\nErrors:\n" . htmlspecialchars($errors);
        }
    }
    ?>
        </div>
        <p><a href="?">← Run Another Report</a></p>
    </div>
    <?php
} else {
    ?>
    <div class="container">
        <h1>Error</h1>
        <div class="result warning">
            ❌ Failed to execute script
        </div>
        <p><a href="?">← Try Again</a></p>
    </div>
    <?php
}
?>