<?php
session_start();

require_once 'auth.php';
require_once 'logger.php';

$pending_user = test_session_get('pending_2fa_user');
$expires_at = test_session_get('pending_2fa_expires');
$redirect_after = test_session_get('pending_2fa_redirect') ?: 'admin.php';
$ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';

// If no pending 2FA, send to login
if (!$pending_user) {
    header('Location: admin.php');
    exit;
}

// Expired challenge
if ($expires_at && time() > $expires_at) {
    clear_pending_two_factor();
    header('Location: admin.php?error=twofa_expired');
    exit;
}

$users = load_users();
$user = find_user($pending_user, $users);
if (!$user || empty($user['two_factor_enabled']) || empty($user['two_factor_secret'])) {
    clear_pending_two_factor();
    header('Location: admin.php?error=twofa_not_configured');
    exit;
}

$error_message = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!validate_csrf_token()) {
        $error_message = 'Security validation failed. Please try again.';
    } else {
        $code = trim($_POST['two_factor_code'] ?? '');
        if (verify_totp($user['two_factor_secret'], $code)) {
            finalize_login_success($users, $user['username'], $ip);
            clear_pending_two_factor();
            generate_csrf_token();
            header('Location: ' . $redirect_after);
            exit;
        } else {
            $error_message = 'Invalid or expired code. Please try again.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Two-Factor Authentication</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header">
                        <h4 class="mb-0"><i class="fas fa-shield-alt"></i> Two-Factor Authentication</h4>
                    </div>
                    <div class="card-body">
                        <p class="text-muted">Enter the 6-digit code from your authenticator app to complete sign-in.</p>
                        <?php if ($error_message): ?>
                            <div class="alert alert-danger">
                                <i class="fas fa-exclamation-triangle"></i> <?php echo htmlspecialchars($error_message); ?>
                            </div>
                        <?php endif; ?>
                        <form method="POST">
                            <?php echo csrf_token_field(); ?>
                            <div class="mb-3">
                                <label for="two_factor_code" class="form-label">Authentication Code</label>
                                <input type="text" class="form-control" id="two_factor_code" name="two_factor_code" pattern="\d{6}" inputmode="numeric" autocomplete="one-time-code" required>
                                <div class="form-text">Codes refresh every <?php echo TWO_FACTOR_PERIOD; ?> seconds. One-time use.</div>
                            </div>
                            <div class="d-flex gap-2">
                                <button type="submit" class="btn btn-primary">
                                    <i class="fas fa-unlock"></i> Verify and Continue
                                </button>
                                <a href="auth.php?action=logout" class="btn btn-outline-secondary">Cancel</a>
                            </div>
                        </form>
                    </div>
                </div>
                <p class="text-center mt-3 text-muted small">Signed in as <?php echo htmlspecialchars($pending_user); ?></p>
            </div>
        </div>
    </div>
</body>
</html>
