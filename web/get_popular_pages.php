<?php
// Get popular pages endpoint
header('Content-Type: application/json');
header('Cache-Control: no-cache');

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

// Set the working directory to the project root
$project_root = dirname(__DIR__);

// Get credentials path from environment
$ga4KeyPath = getenv('GA4_KEY_PATH') ?: $project_root . '/.ddev/keys/ga4-page-analytics-cf93eb65ac26.json';

// Change to the project directory
chdir($project_root);

// Set environment variables
putenv('PYTHONPATH=' . $project_root);
putenv('GOOGLE_APPLICATION_CREDENTIALS=' . $ga4KeyPath);

// Run the get_top_pages script with JSON output
$command = "python3 scripts/get_top_pages.py --json 2>&1";
$output = [];
$return_code = 0;

exec($command, $output, $return_code);

if ($return_code !== 0) {
    echo json_encode(['error' => 'Failed to get popular pages', 'details' => implode("\n", $output)]);
    exit;
}

// The output should be JSON from the Python script
$output_str = implode("\n", $output);
$json_data = json_decode($output_str, true);

if ($json_data === null) {
    // If JSON parsing fails, fall back to some default pages
    echo json_encode(['pages' => [
        ['path' => '/valuations', 'users' => 100],
        ['path' => '/properties', 'users' => 80],
        ['path' => '/about', 'users' => 60],
        ['path' => '/contact', 'users' => 40],
        ['path' => '/services', 'users' => 30]
    ]]);
} else {
    echo $output_str;
}
?>