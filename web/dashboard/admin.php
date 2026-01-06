<?php
// Legacy path shim: redirect dashboard/admin.php to main admin panel.
// 2FA and auth are handled in the main admin.php.
header('Location: ../admin.php');
exit;
