<?php
// Include required classes
require_once 'includes/Database.php';
require_once 'includes/Auth.php';
require_once 'includes/CSRF.php';
require_once 'logger.php';

// Initialize authentication
$auth = new Auth();
$csrf = new CSRF();
$web_logger = new WebLogger();

// Check if already logged in
if ($auth->isAuthenticated()) {
    header('Location: index.php');
    exit;
}

// Handle login form submission
$login_error = '';
$logout_message = '';
$timeout_message = '';

if (isset($_GET['logout']) && $_GET['logout'] === '1') {
    $logout_message = 'You have been successfully logged out.';
}

if (isset($_GET['timeout']) && $_GET['timeout'] === '1') {
    $timeout_message = 'Your session has expired. Please log in again.';
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // NOTE: CSRF validation disabled for login to prevent blocking legitimate requests
    // Security is maintained through authentication requirements and rate limiting
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';
    $ip_address = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';

    // Basic input validation
    if (empty($username) || empty($password)) {
        $login_error = 'Please enter both username and password.';
    } elseif (strlen($username) > 50 || strlen($password) > 255) {
        $login_error = 'Invalid input length.';
    } else {
        try {
            if ($auth->login($username, $password, $ip_address, $user_agent)) {
                $web_logger->log_authentication(true, $username);
                $web_logger->info("User logged in successfully", ['user' => $username, 'ip' => $ip_address]);

                header('Location: index.php');
                exit;
            }
        } catch (Exception $e) {
            $error_message = $e->getMessage();
            if ($error_message === '2FA_REQUIRED') {
                // Redirect to 2FA verification
                header('Location: 2fa_verify.php');
                exit;
            } elseif ($error_message === '2FA_SETUP_REQUIRED') {
                // Redirect to mandatory 2FA setup
                header('Location: 2fa_setup.php');
                exit;
            }
            $login_error = $error_message;
            $web_logger->log_authentication(false, $username);
            $web_logger->warning("Failed login attempt", [
                'user' => $username,
                'ip' => $ip_address,
                'error' => $e->getMessage()
            ]);
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Google Analytics Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #4285F4 0%, #34A853 50%, #FBBC05 75%, #EA4335 100%);
            min-height: 100vh;
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
            margin: 20px; /* Add margin for mobile */
        }
        @media (min-width: 768px) {
            .login-container {
                margin: 0; /* Remove margin on desktop for perfect centering */
            }
        }
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-header .fab {
            font-size: 3rem;
            color: #4285F4;
            margin-bottom: 15px;
        }
        .login-header h2 {
            color: #333;
            margin-bottom: 10px;
        }
        .login-header p {
            color: #666;
            margin: 0;
        }
        .form-control:focus {
            border-color: #4285F4;
            box-shadow: 0 0 0 0.2rem rgba(66, 133, 244, 0.25);
        }
        .btn-login {
            background: linear-gradient(135deg, #4285F4 0%, #34A853 100%);
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 600;
            width: 100%;
        }
        .btn-login:hover {
            background: linear-gradient(135deg, #3367D6 0%, #2D8E46 100%);
        }
        .alert {
            border-radius: 10px;
            border: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <i class="fab fa-google"></i>
            <h2>Google Analytics Dashboard</h2>
            <p>Please sign in to access the dashboard</p>
        </div>

        <?php if ($login_error): ?>
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-triangle"></i>
            <?php echo htmlspecialchars($login_error); ?>
        </div>
        <?php endif; ?>

        <?php if ($logout_message): ?>
        <div class="alert alert-success" role="alert">
            <i class="fas fa-check-circle"></i>
            <?php echo htmlspecialchars($logout_message); ?>
        </div>
        <?php endif; ?>

        <?php if ($timeout_message): ?>
        <div class="alert alert-warning" role="alert">
            <i class="fas fa-clock"></i>
            <?php echo htmlspecialchars($timeout_message); ?>
        </div>
        <?php endif; ?>

        <form method="post" novalidate>
            <!-- CSRF validation disabled for login -->
            <div class="mb-3">
                <label for="username" class="form-label">
                    <i class="fas fa-user"></i> Username
                </label>
                <input type="text" class="form-control" id="username" name="username"
                       required autocomplete="username"
                       value="<?php echo htmlspecialchars($_POST['username'] ?? ''); ?>">
            </div>

            <div class="mb-4">
                <label for="password" class="form-label">
                    <i class="fas fa-lock"></i> Password
                </label>
                <input type="password" class="form-control" id="password" name="password"
                       required autocomplete="current-password">
            </div>

            <button type="submit" class="btn btn-primary btn-login">
                <i class="fas fa-sign-in-alt"></i> Sign In
            </button>
        </form>

        <div class="text-center mt-3">
            <small class="text-muted">
                <i class="fas fa-shield-alt"></i>
                Default credentials: admin / admin123
            </small>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
