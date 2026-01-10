<?php
// Include required classes
require_once 'includes/Database.php';
require_once 'includes/Auth.php';
require_once 'includes/CSRF.php';
require_once 'includes/TwoFactorAuth.php';
require_once 'logger.php';

// Initialize authentication and CSRF protection
$auth = new Auth();
$csrf = new CSRF();
$tfa = new TwoFactorAuth();
$web_logger = new WebLogger();

// Check if user is in mandatory 2FA setup phase
if (!$auth->isIn2FASetup()) {
    header('Location: login.php');
    exit;
}

$message = '';
$error = '';

// Handle 2FA setup completion
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['complete_2fa_setup'])) {
    // Verify CSRF token
    if (!$csrf->validateCSRFToken($_POST['csrf_token'] ?? '')) {
        $error = 'Invalid security token. Please try again.';
    } else {
        $verification_code = trim($_POST['verification_code'] ?? '');
        $ip_address = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';

        if (empty($verification_code)) {
            $error = 'Please enter the verification code from your authenticator app.';
        } elseif (!preg_match('/^[0-9]{6}$/', $verification_code)) {
            $error = 'Verification code must be 6 digits.';
        } else {
            try {
                // Get the setup data from session
                $secret = $_SESSION['tfa_setup_secret'] ?? null;
                $backup_codes = $_SESSION['tfa_setup_codes'] ?? null;

                if (!$secret || !$backup_codes) {
                    throw new Exception("Setup session expired. Please log in again.");
                }

                // Verify the code
                if (!$tfa->verifyCode($secret, $verification_code)) {
                    $error = 'Invalid verification code. Please try again.';
                } else {
                    // Complete the setup
                    $auth->complete2FASetup($secret, $backup_codes, $ip_address, $user_agent);
                    header('Location: index.php');
                    exit;
                }
            } catch (Exception $e) {
                $error = $e->getMessage();
            }
        }
    }
}

// Generate setup data if not already done
if (!isset($_SESSION['tfa_setup_secret']) || !isset($_SESSION['tfa_setup_codes'])) {
    $_SESSION['tfa_setup_secret'] = $tfa->generateSecret();
    $_SESSION['tfa_setup_codes'] = $tfa->generateBackupCodes();
}

$secret = $_SESSION['tfa_setup_secret'];
$backup_codes = $_SESSION['tfa_setup_codes'];

if (!isset($_SESSION['temp_2fa_setup_username']) || empty($_SESSION['temp_2fa_setup_username'])) {
    $error = 'Session expired. Please log in again.';
} else {
    $qr_url = $tfa->getQRCodeUrl($_SESSION['temp_2fa_setup_username'], $secret);
}

// Handle cancel (logout)
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
    <title>Mandatory Two-Factor Setup - Google Analytics Dashboard</title>
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
        .setup-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            padding: 40px;
            width: 100%;
            max-width: 500px;
            margin: 20px;
        }
        @media (min-width: 768px) {
            .setup-container {
                margin: 0;
            }
        }
        .backup-codes {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            padding: 15px;
            font-family: monospace;
            word-break: break-all;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="setup-container">
            <div class="text-center mb-4">
                <i class="fas fa-shield-alt text-primary" style="font-size: 3rem;"></i>
                <h2 class="mt-3">Security Setup Required</h2>
                <p class="text-muted">Two-factor authentication is mandatory for all accounts.</p>
                <div class="alert alert-info">
                    <strong>Step 1:</strong> Install an authenticator app like Google Authenticator, Authy, or Microsoft Authenticator on your phone.
                </div>
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

            <div class="mb-4">
                <h5><strong>Step 2:</strong> Scan the QR code</h5>
                <p>Scan this QR code with your authenticator app:</p>
                <div class="text-center mb-3">
                    <?php if (isset($qr_url)): ?>
                        <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=<?php echo rawurlencode($qr_url); ?>" alt="QR Code" class="img-fluid border">
                    <?php else: ?>
                        <div class="alert alert-warning">QR code not available. Please refresh the page.</div>
                    <?php endif; ?>
                </div>
                <p class="text-muted small">Can't scan? Manually enter: <code><?php echo htmlspecialchars($secret ?? ''); ?></code></p>
            </div>

            <div class="mb-4">
                <h5><strong>Step 3:</strong> Save your backup codes</h5>
                <p class="text-muted">Save these backup codes in a secure place. You can use them to recover access if you lose your device.</p>
                <div class="backup-codes">
                    <?php foreach ($backup_codes as $code): ?>
                        <div><?php echo htmlspecialchars($code); ?></div>
                    <?php endforeach; ?>
                </div>
                <div class="mt-2">
                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="copyBackupCodes()">
                        <i class="fas fa-copy"></i> Copy Codes
                    </button>
                </div>
            </div>

            <form method="POST" action="">
                <input type="hidden" name="csrf_token" value="<?php echo htmlspecialchars($csrf->generateToken()); ?>">
                <input type="hidden" name="complete_2fa_setup" value="1">

                <div class="mb-3">
                    <h5><strong>Step 4:</strong> Verify setup</h5>
                    <label for="verification_code" class="form-label">Enter the 6-digit code from your app:</label>
                    <input type="text" class="form-control text-center" id="verification_code" name="verification_code"
                           maxlength="6" pattern="[0-9]{6}" placeholder="000000" required style="font-size: 1.5rem; letter-spacing: 0.5rem;">
                </div>

                <div class="d-grid gap-2">
                    <button type="submit" class="btn btn-success btn-lg">
                        <i class="fas fa-check"></i> Complete Setup & Login
                    </button>
                    <a href="?cancel=1" class="btn btn-outline-secondary">
                        <i class="fas fa-arrow-left"></i> Cancel
                    </a>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Auto-focus the input field
        document.getElementById('verification_code').focus();

        // Auto-submit when 6 digits are entered
        document.getElementById('verification_code').addEventListener('input', function(e) {
            const value = e.target.value.replace(/\D/g, '');
            e.target.value = value;
            if (value.length === 6) {
                e.target.form.submit();
            }
        });

        function copyBackupCodes() {
            const codes = <?php echo json_encode(implode('\n', $backup_codes)); ?>;
            navigator.clipboard.writeText(codes).then(function() {
                alert('Backup codes copied to clipboard!');
            }).catch(function(err) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = codes;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                alert('Backup codes copied to clipboard!');
            });
        }
    </script>
</body>
</html>
