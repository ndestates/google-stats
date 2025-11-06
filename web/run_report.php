<?php
// Enable error reporting for debugging
ini_set('display_errors', 1);
error_reporting(E_ALL);

// Set headers for JSON response
header('Content-Type: text/plain');
header('Cache-Control: no-cache');

// Get the script name and arguments from POST data
$script = $_POST['script'] ?? '';
$args = $_POST['args'] ?? '';

if (empty($script)) {
    echo "Error: No script specified";
    exit;
}

// Validate script name to prevent security issues
$allowed_scripts = [
    'page_traffic_analysis.py',
    'google_ads_performance.py',
    'mailchimp_performance.py',
    'gsc_ga_keywords.py',
    'get_top_pages.py',
    'yesterday_report.py',
    'google_ads_ad_performance.py',
    'all_pages_sources_report.py',
    'campaign_performance.py',
    'audience_management.py'
];

if (!in_array($script, $allowed_scripts)) {
    echo "Error: Invalid script specified";
    exit;
}

// Set the working directory to the project root
$project_root = dirname(__DIR__);

// Change to the project directory
chdir($project_root);

// Set environment variables if needed
putenv('PYTHONPATH=' . $project_root);
putenv('GOOGLE_APPLICATION_CREDENTIALS=' . $project_root . '/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json');

// Build the command to run the Python script
$command = "python3 scripts/{$script}";
if (!empty($args)) {
    $command .= " {$args}";
}
$command .= " 2>&1";

// Execute the command and capture output
$output = [];
$return_code = 0;

exec($command, $output, $return_code);

// Output the results
if ($return_code === 0) {
    echo "Report completed successfully:\n\n";
} else {
    echo "Report completed with warnings/errors (exit code: {$return_code}):\n\n";
}

echo implode("\n", $output);
?>