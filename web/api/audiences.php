<?php
header('Content-Type: application/json');
session_start();

require_once dirname(__DIR__) . '/auth.php';
require_once dirname(__DIR__) . '/logger.php';

if (!is_logged_in()) {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

function db_connect() {
    $dsn = 'mysql:host=db;dbname=google_stats;charset=utf8mb4';
    $user = 'db';
    $pass = 'db';
    $options = [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ];
    return new PDO($dsn, $user, $pass, $options);
}

function json_error($message, $code = 400) {
    http_response_code($code);
    echo json_encode(['error' => $message]);
    exit;
}

$action = $_GET['action'] ?? 'list';
$is_post = $_SERVER['REQUEST_METHOD'] === 'POST';

if ($is_post && !validate_csrf_token()) {
    json_error('Invalid CSRF token', 403);
}

try {
    $pdo = db_connect();

    switch ($action) {
        case 'list':
            $stmt = $pdo->query(
                "SELECT a.id, a.name, a.description, a.status, a.membership_count, a.last_synced, a.archived_at,
                        (SELECT membership_count FROM audience_membership_snapshots s WHERE s.audience_id = a.id ORDER BY snapshot_at DESC LIMIT 1) AS last_snapshot_count,
                        (SELECT snapshot_at FROM audience_membership_snapshots s WHERE s.audience_id = a.id ORDER BY snapshot_at DESC LIMIT 1) AS last_snapshot_at
                 FROM audiences a
                 WHERE a.status IN ('active', 'archived', 'deleted')
                 ORDER BY a.status = 'active' DESC, a.name ASC"
            );
            $rows = $stmt->fetchAll();
            echo json_encode(['audiences' => $rows]);
            break;

        case 'archive':
            if (!$is_post) json_error('POST required', 405);
            $id = intval($_POST['id'] ?? 0);
            if (!$id) json_error('Missing audience id');
            $stmt = $pdo->prepare("UPDATE audiences SET status = 'archived', archived_at = NOW(), updated_at = NOW() WHERE id = :id");
            $stmt->execute([':id' => $id]);
            echo json_encode(['ok' => true]);
            break;

        case 'delete':
            if (!$is_post) json_error('POST required', 405);
            $id = intval($_POST['id'] ?? 0);
            if (!$id) json_error('Missing audience id');
            $hard = filter_var($_POST['hard'] ?? false, FILTER_VALIDATE_BOOLEAN);
            if ($hard) {
                $stmt = $pdo->prepare("DELETE FROM audiences WHERE id = :id");
            } else {
                $stmt = $pdo->prepare("UPDATE audiences SET status = 'deleted', archived_at = NOW(), updated_at = NOW() WHERE id = :id");
            }
            $stmt->execute([':id' => $id]);
            echo json_encode(['ok' => true]);
            break;

        case 'snapshot':
            if (!$is_post) json_error('POST required', 405);
            $id = intval($_POST['id'] ?? 0);
            if ($id) {
                $stmt = $pdo->prepare("INSERT INTO audience_membership_snapshots (audience_id, membership_count, note) SELECT id, membership_count, 'manual snapshot' FROM audiences WHERE id = :id");
                $stmt->execute([':id' => $id]);
                echo json_encode(['ok' => true, 'snapshots' => $stmt->rowCount()]);
            } else {
                $stmt = $pdo->query("INSERT INTO audience_membership_snapshots (audience_id, membership_count, note) SELECT id, membership_count, 'manual snapshot' FROM audiences WHERE status IN ('active','archived')");
                echo json_encode(['ok' => true, 'snapshots' => $stmt->rowCount()]);
            }
            break;

        default:
            json_error('Unknown action', 400);
    }
} catch (PDOException $e) {
    json_error('Database error: ' . $e->getMessage(), 500);
}

?>
