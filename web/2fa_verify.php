<?php
// Include required classes
require_once 'includes/Database.php';
require_once 'includes/Auth.php';
require_once 'includes/CSRF.php';
require_once 'logger.php';

// Initialize authentication and CSRF protection
$auth = new Auth();
$csrf = new CSRF();
$web_logger = new WebLogger();

// Check if user is in 2FA verification phase
if (!$auth->isIn2FAVerification()) {
    // Allow direct access for testing/demo purposes
    // In production, this should redirect to login
    // header('Location: login.php');
    // exit;
}

$message = '';
$error = '';

// Handle 2FA verification
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['verify_2fa'])) {
    // Verify CSRF token
    if (!$csrf->validateCSRFToken($_POST['csrf_token'] ?? '')) {
        $error = 'Invalid security token. Please try again.';
    } else {
        $code = trim($_POST['2fa_code'] ?? '');
        $ip_address = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';

        if (empty($code)) {
            $error = 'Please enter your 2FA code.';
        } elseif (!preg_match('/^[0-9]{6}$/', $code)) {
            $error = '2FA code must be 6 digits.';
        } else {
            try {
                $auth->verify2FA($code, $ip_address, $user_agent);
                $web_logger->info("2FA verification successful", ['ip' => $ip_address]);
                header('Location: index.php');
                exit;
            } catch (Exception $e) {
                $error = $e->getMessage();
                $web_logger->warning("2FA verification failed", [
                    'ip' => $ip_address,
                    'error' => $e->getMessage()
                ]);
            }
        }
    }
}

// Handle logout/cancel
if (isset($_GET['cancel'])) {
    $auth->logout();
    header('Location: login.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Two-Factor Authentication - Google Analytics Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        html, body {
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }
        body {
            background: linear-gradient(135deg, #4285F4 0%, #34A853 50%, #FBBC05 75%, #EA4335 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }
        .container {
            width: 100%;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            padding: 40px;
            width: 100%;
            max-width: 400px;
            margin: 20px;
            box-sizing: border-box;
        }
        .login-container input[type="text"],
        .login-container input[type="hidden"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        .login-container form,
        .login-container form > div {
            display: block !important;
        }
        @media (min-width: 768px) {
            .login-container {
                margin: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="login-container">
            <div class="text-center mb-4">
                <i class="fas fa-shield-alt text-primary" style="font-size: 3rem;"></i>
                <h2 class="mt-3">Two-Factor Authentication</h2>
                <p class="text-muted">Enter the 6-digit code from your authenticator app</p>
            </div>

            <?php if ($message): ?>
                <div class="alert alert-success">
                    <i class="fas fa-check-circle"></i> <?php echo htmlspecialchars($message); ?>
                </div>
            <?php endif; ?>

            <?php if ($error): ?>
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> <?php echo htmlspecialchars($error); ?>
                </div>
            <?php endif; ?>

            <form method="POST" action="" style="display: block !important;">
                <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars($csrf->generateToken()); ?>">
                <input type="hidden" name="verify_2fa" value="1">

                <div class="mb-4" style="display: block !important;">
                    <label for="2fa_code" class="form-label fw-bold" style="display: block !important;">
                        <i class="fas fa-key"></i> Authentication Code
                    </label>
                    <input type="text" class="form-control text-center border-2" id="2fa_code" name="2fa_code"
                           maxlength="6" pattern="[0-9]{6}" inputmode="numeric"
                           placeholder="000000" required style="font-size: 2rem; letter-spacing: 1rem; padding: 15px; border-width: 2px !important; display: block !important; width: 100% !important;">
                </div>

                <div class="d-grid gap-2" style="display: grid !important;">
                    <button type="submit" class="btn btn-primary btn-lg" style="display: block !important;">
                        <i class="fas fa-check"></i> Verify Code
                    </button>
                    <a href="?cancel=1" class="btn btn-outline-secondary" style="display: block !important;">
                        <i class="fas fa-arrow-left"></i> Back to Login
                    </a>
                </div>
            </form>

            <div class="text-center mt-3">
                <small class="text-muted">
                    Can't access your authenticator app?
                    <a href="#" onclick="alert('Use one of your backup codes instead of the 6-digit code.')">Use backup code</a>
                </small>
            </div>
        </div>
    </div>

    <script>
        // Auto-focus the input field
        document.getElementById('2fa_code').focus();

        // Auto-submit when 6 digits are entered
        document.getElementById('2fa_code').addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            e.target.value = value;
            if (value.length === 6) {
                e.target.form.submit();
            }
        });
    </script>
</body>
</html>
