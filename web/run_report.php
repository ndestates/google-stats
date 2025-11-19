<?php
// Enable error reporting for debugging
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Load environment variables from .env file
function loadEnv($path) {
    if (!file_exists($path)) {
        return false;
    }

    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) {
            continue;
        }

        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);

        if (!array_key_exists($name, $_SERVER) && !array_key_exists($name, $_ENV)) {
            putenv(sprintf('%s=%s', $name, $value));
            $_ENV[$name] = $value;
            $_SERVER[$name] = $value;
        }
    }
    return true;
}

// Load .env file from project root
$envPath = dirname(__DIR__) . '/.env';
loadEnv($envPath);

// Get credentials path from environment
$ga4KeyPath = getenv('GA4_KEY_PATH') ?: '/var/www/html/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json';

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
                <option value="social_media_analytics">📱 Social Media Analytics</option>
            </select>

            <label for="args">Arguments (optional):</label>
            <input type="text" name="args" id="args" placeholder="--report-type yesterday">

            <label for="start_date">Start Date (optional):</label>
            <input type="date" name="start_date" id="start_date">

            <label for="end_date">End Date (optional):</label>
            <input type="date" name="end_date" id="end_date">

            <button type="submit" id="submit-btn">Run Report</button>
        </form>

        <div class="warning">
            <strong>Security Notice:</strong> This page requires HTTP Basic Authentication.
            Contact your administrator for access credentials.
        </div>

        <script>
            document.getElementById('submit-btn').addEventListener('click', function(e) {
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;

                if (startDate && endDate) {
                    if (startDate > endDate) {
                        alert('Start date cannot be after end date.');
                        e.preventDefault();
                        return false;
                    }
                }
            });
        </script>
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
$start_date = $_POST['start_date'] ?? '';
$end_date = $_POST['end_date'] ?? '';

// Validate and append date arguments
if ($start_date && $end_date) {
    if ($start_date > $end_date) {
        echo "Error: Start date cannot be after end date";
        exit;
    }
    $args .= " --start-date " . escapeshellarg($start_date) . " --end-date " . escapeshellarg($end_date);
} elseif ($start_date || $end_date) {
    echo "Error: Both start and end dates must be provided together";
    exit;
}

// Execute the script

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
    'seo_analysis.py',
    'social_media_analytics'
];

if (!in_array($script, $allowed_scripts)) {
    echo "Error: Invalid script specified";
    exit;
}

// Handle special case for social media analytics
if ($script === 'social_media_analytics') {
    $script_path = "/var/www/html/scripts/hourly_traffic_analysis.py";
    // Use home page as default for social media analytics
    $args_array = ['/'];
    $command = "cd /var/www/html && PYTHONPATH=/var/www/html GOOGLE_APPLICATION_CREDENTIALS=" . escapeshellarg($ga4KeyPath) . " python3 $script_path " . implode(' ', array_map('escapeshellarg', $args_array));
} else {
    // Execute the selected script
    $script_path = "/var/www/html/scripts/$script";
    $args_array = $args ? explode(' ', $args) : [];
    $command = "cd /var/www/html && PYTHONPATH=/var/www/html GOOGLE_APPLICATION_CREDENTIALS=" . escapeshellarg($ga4KeyPath) . " python3 $script_path " . implode(' ', array_map('escapeshellarg', $args_array));
}

// Set the working directory to the project root for proc_open
$project_root = '/var/www/html';

// Set environment variables if needed
putenv('PYTHONPATH=/var/www/html');
putenv('GOOGLE_APPLICATION_CREDENTIALS=' . $ga4KeyPath);

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

    // Handle special formatting for analytics reports
    if ($return_code === 0) {
                // Parse the output to extract social media data
                $lines = explode("\n", trim($output));
                $social_data = [];
                $in_social_section = false;
                $no_social_data = false;

                foreach ($lines as $line) {
                    if (strpos($line, 'SOCIAL ORGANIC TRAFFIC SUMMARY:') !== false) {
                        $in_social_section = true;
                        continue;
                    }

                    if ($in_social_section && strpos($line, 'No organic social media traffic detected') !== false) {
                        $no_social_data = true;
                        break;
                    }

                    if ($in_social_section && strpos($line, 'Best posting hours') !== false) {
                        continue;
                    }

                    if ($in_social_section && trim($line) === '') {
                        continue;
                    }

                    if ($in_social_section && strpos($line, ':') !== false) {
                        // Parse platform data: "Facebook: 14:00 (1,234 users) - Total: 5,678 users"
                        if (preg_match('/^\s*([A-Za-z]+):\s*(\d{2}):00\s*\(([\d,]+)\s*users\)\s*-\s*Total:\s*([\d,]+)\s*users/', $line, $matches)) {
                            $platform = strtolower($matches[1]);
                            $best_hour = (int)$matches[2];
                            $best_users = (int)str_replace(',', '', $matches[3]);
                            $total_users = (int)str_replace(',', '', $matches[4]);

                            $social_data[$platform] = [
                                'name' => ucfirst($platform),
                                'best_hour' => $best_hour,
                                'best_users' => $best_users,
                                'total_users' => $total_users
                            ];
                        }
                    }

                    // Stop parsing when we hit another section
                    if ($in_social_section && (strpos($line, '=====') !== false || strpos($line, 'ORGANIC TRAFFIC SUMMARY') !== false)) {
                        break;
                    }
                }

                // Parse page path for linking
                $page_path = '';
                if ($script === 'hourly_traffic_analysis.py' && !empty($args)) {
                    $arg_parts = explode(' ', trim($args));
                    $page_arg = $arg_parts[0];
                    if (strpos($page_arg, 'http') === 0) {
                        $parsed = parse_url($page_arg);
                        $page_path = $parsed['path'] ?? '';
                    } else {
                        $page_path = $page_arg;
                    }
                    if (!empty($page_path) && $page_path[0] !== '/') {
                        $page_path = '/' . $page_path;
                    }
                }

        // Output the formatted social media dashboard
        ?>
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Social Media Analytics Report</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    overflow: hidden;
                }
                .header {
                    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }
                .header h1 {
                    margin: 0;
                    font-size: 2.5em;
                    font-weight: 300;
                }
                .header p {
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                    font-size: 1.1em;
                }
                .content {
                    padding: 40px;
                }
                .report-section {
                    margin-bottom: 40px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    padding: 30px;
                    border-left: 4px solid #007cba;
                }
                .section-title {
                    font-size: 1.8em;
                    margin-bottom: 20px;
                    color: #333;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .platform-grid {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-top: 20px;
                }
                @media (max-width: 768px) {
                    .platform-grid {
                        grid-template-columns: 1fr;
                    }
                }
                .platform-card {
                    background: white;
                    border-radius: 8px;
                    padding: 25px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    border: 1px solid #e9ecef;
                    transition: transform 0.2s, box-shadow 0.2s;
                }
                .platform-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
                }
                .platform-name {
                    font-size: 1.4em;
                    font-weight: bold;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .metric {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                    padding: 8px 0;
                    border-bottom: 1px solid #f0f0f0;
                }
                .metric:last-child {
                    border-bottom: none;
                }
                .metric-label {
                    font-weight: 500;
                    color: #666;
                }
                .metric-value {
                    font-weight: bold;
                    color: #333;
                    font-size: 1.1em;
                }
                .best-hour {
                    background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 15px;
                    border-left: 4px solid #ff8c42;
                }
                .best-hour strong {
                    color: #e85d04;
                }
                .summary-stats {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 20px;
                    margin-top: 20px;
                }
                @media (max-width: 768px) {
                    .summary-stats {
                        grid-template-columns: 1fr;
                    }
                }
                .stat-card {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .stat-value {
                    font-size: 2em;
                    font-weight: bold;
                    color: #007cba;
                    margin-bottom: 5px;
                }
                .stat-label {
                    color: #666;
                    font-size: 0.9em;
                }
                .error {
                    background: #f8d7da;
                    color: #721c24;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #dc3545;
                    margin-bottom: 20px;
                }
                .refresh-btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                    transition: transform 0.2s;
                }
                .refresh-btn:hover {
                    transform: translateY(-1px);
                }
                @media print {
                    body {
                        background: white !important;
                        margin: 0;
                        padding: 0;
                    }
                    .container {
                        box-shadow: none;
                        margin: 0;
                        max-width: none;
                    }
                    .header {
                        background: white !important;
                        color: black !important;
                        -webkit-print-color-adjust: exact;
                        color-adjust: exact;
                    }
                    .header a {
                        color: blue !important;
                        text-decoration: underline;
                    }
                    .refresh-btn {
                        display: none;
                    }
                    .footer {
                        page-break-before: always;
                    }
                }
                .footer {
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    color: #666;
                    border-top: 1px solid #e9ecef;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏠 NDEstates - Property Analytics Report</h1>
                    <p>Comprehensive analytics insights for your website</p>
                    <?php if (!empty($page_path)): ?>
                    <p>Page: <a href="https://www.ndestates.com<?php echo htmlspecialchars($page_path); ?>" target="_blank" style="color: white; text-decoration: underline;"><?php echo htmlspecialchars($page_path); ?></a></p>
                    <?php endif; ?>
                    <button class="refresh-btn" onclick="window.print()">🖨️ Print / Download PDF</button>
                </div>

                <div class="content">
                    <?php
                $is_social_script = ($script === 'social_media_analytics' || $script === 'hourly_traffic_analysis.py');
                if ($is_social_script && empty($social_data) && !$no_social_data) {
                    echo '<div class="error">⚠️ No social media data found. The analytics script may not have detected organic social traffic in the selected time period.</div>';
                }

                if ($is_social_script) {
                    // Display summary statistics (show 0s if no data)
                    $total_social_users = $no_social_data ? 0 : array_sum(array_column($social_data, 'total_users'));
                    $active_platforms = $no_social_data ? 0 : count($social_data);
                    $avg_best_hour = $no_social_data ? 0 : round(array_sum(array_column($social_data, 'best_hour')) / count($social_data));

                    echo '<div class="report-section">';
                    echo '<h2 class="section-title">📊 Summary Statistics</h2>';
                    echo '<div class="summary-stats">';
                    echo '<div class="stat-card">';
                    echo '<div class="stat-value">' . number_format($total_social_users) . '</div>';
                    echo '<div class="stat-label">Total Organic Social Users</div>';
                    echo '</div>';
                    echo '<div class="stat-card">';
                    echo '<div class="stat-value">' . $active_platforms . '</div>';
                    echo '<div class="stat-label">Active Platforms</div>';
                    echo '</div>';
                    echo '<div class="stat-card">';
                    echo '<div class="stat-value">' . ($no_social_data ? 'N/A' : $avg_best_hour . ':00') . '</div>';
                    echo '<div class="stat-label">Average Best Hour</div>';
                    echo '</div>';
                    echo '</div>';
                    echo '</div>';

                    // Display platform-specific data
                    echo '<div class="report-section">';
                    echo '<h2 class="section-title">🎯 Platform Performance</h2>';
                    if ($no_social_data) {
                        echo '<div class="platform-grid">';
                        echo '<div class="platform-card" style="grid-column: 1 / -1; text-align: center; padding: 40px; overflow: visible;">';
                        echo '<h3 style="color: #666; margin: 0;">📱 No Social Media Data Available</h3>';
                        echo '<p style="color: #999; margin: 10px 0 0 0; word-wrap: break-word; white-space: normal;">No organic social media traffic was detected for this page in the selected time period.</p>';
                        echo '<p style="color: #999; font-size: 0.9em; margin: 10px 0 0 0; word-wrap: break-word; white-space: normal;">Try a different page or expand the date range.</p>';
                        echo '</div>';
                        echo '</div>';
                    } else {
                        echo '<div class="platform-grid">';

                        // Sort platforms by total users (descending)
                        uasort($social_data, function($a, $b) {
                            return $b['total_users'] <=> $a['total_users'];
                        });

                        foreach ($social_data as $platform => $data) {
                            $emoji = '';
                            switch ($platform) {
                                case 'facebook': $emoji = '📘'; break;
                                case 'instagram': $emoji = '📷'; break;
                                case 'twitter': $emoji = '🐦'; break;
                                case 'linkedin': $emoji = '💼'; break;
                                case 'buffer': $emoji = '🔄'; break;
                                default: $emoji = '📱';
                            }

                            echo '<div class="platform-card">';
                            echo '<div class="platform-name">' . $emoji . ' ' . $data['name'] . '</div>';
                            echo '<div class="metric">';
                            echo '<span class="metric-label">Total Organic Users</span>';
                            echo '<span class="metric-value">' . number_format($data['total_users']) . '</span>';
                            echo '</div>';
                            echo '<div class="best-hour">';
                            echo '<strong>🏆 Best Posting Hour:</strong> ' . $data['best_hour'] . ':00<br>';
                            echo '<small>(' . number_format($data['best_users']) . ' users reached)</small>';
                            echo '</div>';
                            echo '</div>';
                        }

                        echo '</div>';
                    }
                    echo '</div>';
                } else {
                    // For non-social scripts, display the raw output in a styled box
                    echo '<div class="report-section">';
                    echo '<h2 class="section-title">📄 Report Output</h2>';
                    echo '<div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef;">';
                    echo '<pre style="margin: 0; font-family: monospace; font-size: 14px; line-height: 1.4; white-space: pre-wrap; word-wrap: break-word;">' . htmlspecialchars($output) . '</pre>';
                    echo '</div>';
                    echo '</div>';
                }

                // Show raw output for debugging (collapsible) - only for social scripts
                if ($is_social_script) {
                    echo '<summary style="cursor: pointer; padding: 10px; background: #f8f9fa; border-radius: 4px;">🔧 Raw Script Output (Debug)</summary>';
                    echo '<pre style="background: #f8f9fa; padding: 20px; border-radius: 4px; margin-top: 10px; font-size: 12px; overflow-x: auto;">' . htmlspecialchars($output) . '</pre>';
                    echo '</details>';
                }
                ?>

                    <div style="text-align: center; margin-top: 30px;">
                        <a href="index.php" class="btn btn-secondary">← Back to Reports</a>
                    </div>
                </div>

                <div class="footer">
                    <p>Report generated on <?php echo date('F j, Y \a\t g:i A'); ?> | NDEstates Analytics | Powered by Google Analytics 4</p>
                </div>
            </div>
        </body>
        </html>
        <?php
    } else {
        // Output the results for regular scripts
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
    }
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