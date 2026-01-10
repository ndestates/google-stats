<?php
/**
 * API endpoint for fetching dropdown data
 * Returns JSON for properties, campaigns, and other entities
 */

// Set headers for performance and caching
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: private, max-age=300'); // Cache for 5 minutes
header('Connection: keep-alive');

// Include authentication
require_once 'auth.php';
require_once 'credentials.php';
load_credentials_to_env();

// Check authentication
if (!is_logged_in()) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

// Database connection with persistent connection
function get_db_connection() {
    static $pdo = null;
    
    if ($pdo !== null) {
        return $pdo;
    }
    
    $host = getenv('DB_HOST') ?: 'db';
    $db = getenv('DB_NAME') ?: 'google_stats';
    $user = getenv('DB_USERNAME') ?: 'db';
    $pass = getenv('DB_PASSWORD') ?: 'db';
    
    try {
        $pdo = new PDO(
            "mysql:host=$host;dbname=$db;charset=utf8mb4",
            $user,
            $pass,
            [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_PERSISTENT => true,
                PDO::ATTR_EMULATE_PREPARES => false,
                PDO::MYSQL_ATTR_USE_BUFFERED_QUERY => true
            ]
        );
        return $pdo;
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Database connection failed']);
        exit;
    }
}

$pdo = get_db_connection();

// Get action from query string
$action = $_GET['action'] ?? '';

switch ($action) {
    case 'properties':
        // Fetch all properties with key details
        $type = $_GET['type'] ?? ''; // buy/rent
        $status = $_GET['status'] ?? ''; // available/sold/let
        
        $sql = "SELECT 
                    reference,
                    property_name,
                    house_name,
                    url,
                    property_type,
                    price,
                    parish,
                    status,
                    type,
                    bedrooms,
                    campaign
                FROM properties 
                WHERE 1=1";
        
        $params = [];
        
        if ($type) {
            $sql .= " AND type = :type";
            $params[':type'] = $type;
        }
        
        if ($status) {
            $sql .= " AND status = :status";
            $params[':status'] = $status;
        }
        
        $sql .= " ORDER BY reference";
        
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        $properties = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Format for Select2
        $result = array_map(function($prop) {
            // Start with reference and house_name (actual address)
            $label = $prop['reference'];
            if ($prop['house_name']) {
                $label .= ' - ' . $prop['house_name'];
            }
            
            // Add key details in parentheses
            $details = [];
            if ($prop['parish']) $details[] = $prop['parish'];
            if ($prop['bedrooms']) $details[] = $prop['bedrooms'] . ' bed';
            if ($prop['price']) $details[] = '£' . number_format($prop['price'], 0);
            
            if (!empty($details)) {
                $label .= ' (' . implode(', ', $details) . ')';
            }
            
            // Create default campaign name from house_name
            $default_campaign = $prop['house_name'] ?: $prop['property_name'] ?: $prop['reference'];
            
            // Create truncated URL (remove domain, keep path)
            $truncated_url = $prop['url'];
            if (preg_match('#^https?://[^/]+(.*)$#', $prop['url'], $matches)) {
                $truncated_url = $matches[1];
            }
            
            return [
                'id' => $prop['reference'],
                'text' => $label,
                'url' => $prop['url'],
                'truncated_url' => $truncated_url,
                'house_name' => $prop['house_name'],
                'default_campaign_name' => $default_campaign,
                'type' => $prop['type'],
                'status' => $prop['status'],
                'parish' => $prop['parish'],
                'campaign' => $prop['campaign']
            ];
        }, $properties);
        
        echo json_encode($result);
        break;
        
    case 'campaigns':
        // Fetch all marketing campaigns
        $platform = $_GET['platform'] ?? '';
        
        $sql = "SELECT 
                    campaign_name,
                    platform,
                    campaign_type,
                    start_date,
                    end_date,
                    status,
                    target_references
                FROM marketing_campaigns 
                WHERE 1=1";
        
        $params = [];
        
        if ($platform) {
            $sql .= " AND platform = :platform";
            $params[':platform'] = $platform;
        }
        
        $sql .= " ORDER BY start_date DESC, campaign_name";
        
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        $campaigns = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        // Format for Select2
        $result = array_map(function($camp) {
            $label = $camp['campaign_name'] . ' (' . $camp['platform'];
            if ($camp['campaign_type']) {
                $label .= ' - ' . $camp['campaign_type'];
            }
            $label .= ')';
            
            if ($camp['status']) {
                $label .= ' [' . strtoupper($camp['status']) . ']';
            }
            
            return [
                'id' => $camp['campaign_name'],
                'text' => $label,
                'platform' => $camp['platform'],
                'type' => $camp['campaign_type'],
                'status' => $camp['status'],
                'start_date' => $camp['start_date'],
                'end_date' => $camp['end_date'],
                'targets' => $camp['target_references']
            ];
        }, $campaigns);
        
        echo json_encode($result);
        break;
        
    case 'parishes':
        // Get distinct parishes
        $stmt = $pdo->query("SELECT DISTINCT parish FROM properties WHERE parish IS NOT NULL ORDER BY parish");
        $parishes = $stmt->fetchAll(PDO::FETCH_COLUMN);
        
        $result = array_map(function($parish) {
            return ['id' => $parish, 'text' => $parish];
        }, $parishes);
        
        echo json_encode($result);
        break;
        
    case 'property_types':
        // Get distinct property types
        $stmt = $pdo->query("SELECT DISTINCT property_type FROM properties WHERE property_type IS NOT NULL ORDER BY property_type");
        $types = $stmt->fetchAll(PDO::FETCH_COLUMN);
        
        $result = array_map(function($type) {
            return ['id' => $type, 'text' => $type];
        }, $types);
        
        echo json_encode($result);
        break;
        
    case 'urls':
        // Get all property URLs for page traffic analysis
        $stmt = $pdo->query("SELECT DISTINCT url, reference, property_name, house_name FROM properties ORDER BY reference");
        $properties = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        $result = array_map(function($prop) {
            // Show reference and house_name (actual address)
            $label = $prop['reference'];
            if ($prop['house_name']) {
                $label .= ' - ' . $prop['house_name'];
            } elseif ($prop['property_name']) {
                // Fallback to property_name if no house_name
                $label .= ' - ' . $prop['property_name'];
            }
            
            // Create default campaign name from house_name
            $default_campaign = $prop['house_name'] ?: $prop['property_name'] ?: $prop['reference'];
            
            // Create truncated URL (remove domain, keep path)
            $truncated_url = $prop['url'];
            if (preg_match('#^https?://[^/]+(.*)$#', $prop['url'], $matches)) {
                $truncated_url = $matches[1];
            }
            
            return [
                'id' => $prop['url'],
                'text' => $label,
                'reference' => $prop['reference'],
                'house_name' => $prop['house_name'],
                'default_campaign_name' => $default_campaign,
                'truncated_url' => $truncated_url
            ];
        }, $properties);
        
        echo json_encode($result);
        break;
        
    case 'platforms':
        // Get available campaign platforms
        $platforms = [
            ['id' => 'facebook', 'text' => 'Facebook'],
            ['id' => 'google_ads', 'text' => 'Google Ads'],
            ['id' => 'email', 'text' => 'Email Marketing'],
            ['id' => 'linkedin', 'text' => 'LinkedIn'],
            ['id' => 'instagram', 'text' => 'Instagram'],
            ['id' => 'other', 'text' => 'Other']
        ];
        
        echo json_encode($platforms);
        break;
        
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Invalid action']);
        break;
}

// Clean up and close connection
$pdo = null;
exit;
