<?php
/**
 * Site Metrics API Endpoint
 * Returns total pageviews, unique visitors, and properties viewed
 */

header('Content-Type: application/json');

// Run the Python script to get metrics (use absolute path)
$script_path = dirname(dirname(dirname(__FILE__))) . '/scripts/site_metrics.py';
$command = "python3 $script_path --json 2>&1";
$output = shell_exec($command);

// Find the JSON output (it's after the text output)
$lines = explode("\n", $output);
$json_output = '';
$json_started = false;

foreach ($lines as $line) {
    if ($line === '{' || $json_started) {
        $json_started = true;
        $json_output .= $line . "\n";
    }
}

// Parse and return the JSON
if (!empty($json_output)) {
    echo $json_output;
} else {
    echo json_encode(['error' => 'Failed to fetch metrics', 'output' => $output]);
}
?>