<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Analytics Reports - ND Estates</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="icon" href="assets/design-system/nd-estates-design-system/logos/stacked-colour.svg" type="image/svg+xml">
</head>
<body>
    <header>
        <div class="logo">
            <img src="assets/design-system/nd-estates-design-system/logos/row-colour.svg" alt="ND Estates Logo">
        </div>
        <nav>
            <ul>
                <li><a href="index.php" class="active">Dashboard</a></li>
                <li><a href="documentation.php">Documentation</a></li>
                <li><a href="logout.php" class="logout-link">Logout</a></li>
            </ul>
        </nav>
    </header>

    <div class="container">
        <?php
        // Start session for authentication
        session_start();

        // Include authentication functions
        require_once 'auth.php';

        // Include version information
        require_once 'version.php';

        // Check if user is logged in
        if (!is_logged_in()) {
            $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
            if (isset($web_logger) && $web_logger->is_ip_blocked($ip)) {
                http_response_code(403);
                echo '<div class="card"><div class="alert alert-danger"><h4>Access Denied</h4><p>Your IP address has been blocked due to security policy.</p></div></div>';
                exit;
            }
            // Redirect to login page if not logged in
            header('Location: login.php');
            exit;
        }
        ?>

        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>Welcome to Google Stats</h1>
            <span class="badge bg-primary-soft text-primary">Version: <?php echo htmlspecialchars($version_info['tag'] ?? APP_VERSION ?? 'N/A'); ?></span>
        </div>

        <div class="card">
            <h2>Run a New Report</h2>
            <form action="run_report.php" method="post" target="report_output" class="form-container">
                <div class="form-group">
                    <label for="report_type">Select Report</label>
                    <select name="report_type" id="report_type" class="form-control" required>
                        <option value="">-- Please select a report --</option>
                        <?php
                        $reports = [
                            'yesterday' => 'Yesterday Report',
                            'weekly' => 'Weekly Report',
                            'monthly' => 'Monthly Report',
                            'yearly' => 'Yearly Report',
                            'comprehensive_page_source' => 'Comprehensive Page Source Report',
                            'campaign_performance' => 'Campaign Performance Report',
                            'content_performance' => 'Content Performance Report',
                            'social_media_timing' => 'Social Media Timing Report',
                            'property_channel_performance' => 'Property Channel Performance',
                            'catalog_analytics_report' => 'Catalog Analytics Report',
                            'viewing_requests_manager' => 'Viewing Requests Manager',
                            'audience_management' => 'Audience Management',
                        ];
                        foreach ($reports as $value => $label) {
                            echo "<option value=\"$value\">$label</option>";
                        }
                        ?>
                    </select>
                </div>
                <div class="form-group">
                    <label for="start_date">Start Date (Optional)</label>
                    <input type="date" name="start_date" id="start_date" class="form-control">
                </div>
                <div class="form-group">
                    <label for="end_date">End Date (Optional)</label>
                    <input type="date" name="end_date" id="end_date" class="form-control">
                </div>
                <div class="form-group">
                    <button type="submit" class="btn btn-primary w-100">Run Report</button>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>Report Output</h2>
            <iframe name="report_output" style="width: 100%; height: 400px; border: 1px solid #ccc; border-radius: 8px;"></iframe>
        </div>

    </div>
    <style>
        .report-card { margin-bottom: 20px; }
        .output { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }
        .output pre { white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; }
        .loading { display: none; }
        
        /* Site Metrics Dashboard */
        .metrics-dashboard {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            color: white;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .metrics-dashboard h2 {
            font-size: 1.8rem;
            margin-bottom: 5px;
            font-weight: 600;
        }
        .metrics-dashboard .subtitle {
            font-size: 0.9rem;
            opacity: 0.9;
            margin-bottom: 25px;
        }
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        .metric-card {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        .metric-card .metric-icon {
            font-size: 1.5rem;
            margin-bottom: 10px;
            display: inline-block;
        }
        .metric-card .metric-label {
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            opacity: 0.9;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .metric-period {
            margin-bottom: 8px;
        }
        .metric-period-label {
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-right: 8px;
            min-width: 65px;
            text-align: center;
        }
        .metric-value {
            display: inline-block;
            font-size: 1.4rem;
            font-weight: 700;
        }
        .metrics-loading {
            text-align: center;
            padding: 40px;
            font-size: 1.1rem;
        }
        .metrics-error {
            background: rgba(220, 53, 69, 0.2);
            border: 1px solid rgba(220, 53, 69, 0.4);
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
    </style>
</head>
<body>
<div class="app-shell">
  <!-- Left Sidebar Navigation -->
  <aside class="sidebar" id="sidebar">
    <div class="sidebar__brand">
      <div class="sidebar__logo">GS</div>
      <div>
        <div class="sidebar__title">Google Stats</div>
        <div class="sidebar__subtitle">Analytics Dashboard</div>
      </div>
    </div>
    <nav class="sidebar__nav">
      <a class="sidebar__link active" href="index.php">
        <i class="fas fa-chart-line"></i> Overview
      </a>
      <a class="sidebar__link" href="run_report.php">
        <i class="fas fa-play-circle"></i> Scripts
      </a>
      <a class="sidebar__link" href="documentation.php">
        <i class="fas fa-book"></i> Documentation
      </a>
      <a class="sidebar__link" href="admin.php">
        <i class="fas fa-users-cog"></i> Admin
      </a>
    </nav>
    <div class="sidebar__user">
      <div class="sidebar__user-name"><?php echo htmlspecialchars($current_user['username']); ?></div>
      <div class="sidebar__user-role">Administrator</div>
      <div class="sidebar__user-actions">
        <a class="sidebar__link--muted" href="auth.php?action=logout">
          <i class="fas fa-sign-out-alt"></i> Logout
        </a>
      </div>
    </div>
  </aside>

  <div class="main-area">
    <!-- Top Bar Header -->
    <header class="topbar">
      <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle sidebar">
        <span></span><span></span><span></span>
      </button>
      <div class="topbar__titles">
        <p class="topbar__eyebrow">Analytics Platform</p>
        <h1 class="topbar__title">Google Analytics Dashboard</h1>
      </div>
      <div class="topbar__actions">
        <a class="btn btn-primary btn-sm" href="run_report.php">
          <i class="fas fa-play"></i> Run Script
        </a>
      </div>
    </header>

    <!-- Page Content -->
    <main class="content-area">
      <!-- Hero Section -->
      <section class="page-hero">
        <div>
          <p class="eyebrow">Unified Analytics View</p>
          <h2>Real-time insights from Google Analytics 4</h2>
          <p class="text-muted">Use the report forms below to generate analytics. Metrics will display after running each report.</p>
        </div>
        <div class="hero-metrics">
          <div class="pill">Welcome, <?php echo htmlspecialchars($current_user['username']); ?></div>
      </section>

      <!-- Report Cards Grid (responsive, mobile-first) -->
      <div class="cards-grid">
                <!-- Page Traffic Analysis Card -->
                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Page Traffic Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze page traffic and performance metrics for one or multiple properties</p>
                        <form id="page-traffic-form" class="mb-3">
                            <?php echo csrf_token_field(); ?>
                            <div class="mb-3">
                                <label class="form-label">
                                    <i class="fas fa-home"></i> Select Properties:
                                </label>
                                <div class="btn-group btn-group-sm mb-2 w-100" role="group">
                                    <input type="radio" class="btn-check" name="property-mode" id="single-property-mode" checked autocomplete="off">
                                    <label class="btn btn-outline-primary" for="single-property-mode">
                                        <i class="fas fa-home"></i> Single Property
                                    </label>
                                    <input type="radio" class="btn-check" name="property-mode" id="multi-property-mode" autocomplete="off">
                                    <label class="btn btn-outline-primary" for="multi-property-mode">
                                        <i class="fas fa-th"></i> Multiple Properties
                                    </label>
                                </div>
                            <div class="mb-3" id="single-property-selector">
                                <label for="page-url" class="form-label">Page URL or Property:</label>
                                <select class="form-select property-url-select" id="page-url" required style="width: 100%;">
                                    <option value="">Select a property or type URL...</option>
                                </select>
                                <div class="form-text">
                                    <i class="fas fa-info-circle"></i> Select from property catalog or type custom URL/path
                                </div>
                            <div class="mb-3" id="multi-property-selector" style="display: none;">
                                <label for="page-urls-multi" class="form-label">Select Multiple Properties:</label>
                                <select class="form-select property-multi-select" id="page-urls-multi" multiple style="width: 100%;">
                                </select>
                                <div class="form-text">
                                    <i class="fas fa-search"></i> Select multiple properties to compare
                                </div>
                            <div class="mb-3">
                                <label for="analysis-days" class="form-label">Time Period:</label>
                                <select class="form-select" id="analysis-days">
                                    <option value="30">Last 30 days</option>
                                    <option value="7">Last 7 days</option>
                                    <option value="90">Last 90 days</option>
                                    <option value="custom">Custom Range</option>
                                </select>
                            </div>
                            <div class="mb-3" id="custom-date-range" style="display: none;">
                                <label for="start-date" class="form-label">Start Date:</label>
                                <input type="date" class="form-control" id="start-date">
                                <label for="end-date" class="form-label">End Date:</label>
                                <input type="date" class="form-control" id="end-date">
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="property-name" class="form-label">Property Name (Optional):</label>
                                    <input type="text" class="form-control" id="property-name" placeholder="e.g., 4 Melrose Apartments">
                                    <div class="form-text">Will appear on PDF reports</div>
                                <div class="col-md-6 mb-3">
                                    <label for="property-address" class="form-label">Property Address (Optional):</label>
                                    <input type="text" class="form-control" id="property-address" placeholder="e.g., St Helier">
                                    <div class="form-text">Will appear on PDF reports</div>
                            </div>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> <strong>Company Logo:</strong> Set your company logo once in the <a href="admin.php" target="_blank">Admin Settings</a> panel. It will automatically appear on all your reports.
                            </div>
                            <button type="submit" class="btn btn-primary">Run Analysis</button>
                        </form>
                        <div class="loading mt-2" id="loading-page_traffic_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-page_traffic_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Hourly Traffic Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze hourly traffic patterns and best times by source</p>
                        <form id="hourly-traffic-form" class="mb-3">
                            <?php echo csrf_token_field(); ?>
                            <div class="mb-3">
                                <label for="hourly-page-url" class="form-label">Page URL or Path:</label>
                                <select class="form-select property-url-select" id="hourly-page-url" required style="width: 100%;">
                                    <option value="">Select a property or type URL...</option>
                                </select>
                                <div class="form-text">
                                    <i class="fas fa-search"></i> Select from property catalog or type custom URL/path
                                </div>
                            <div class="mb-3">
                                <label for="hourly-analysis-days" class="form-label">Time Period:</label>
                                <select class="form-select" id="hourly-analysis-days">
                                    <option value="30">Last 30 days</option>
                                    <option value="7">Last 7 days</option>
                                    <option value="90">Last 90 days</option>
                                    <option value="custom">Custom Range</option>
                                </select>
                            </div>
                            <div class="mb-3" id="hourly-custom-date-range" style="display: none;">
                                <label for="hourly-start-date" class="form-label">Start Date:</label>
                                <input type="date" class="form-control" id="hourly-start-date">
                                <label for="hourly-end-date" class="form-label">End Date:</label>
                                <input type="date" class="form-control" id="hourly-end-date">
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="hourly-property-name" class="form-label">Property Name (Optional):</label>
                                    <input type="text" class="form-control" id="hourly-property-name" placeholder="e.g., 4 Melrose Apartments">
                                    <div class="form-text">Will appear on PDF reports</div>
                                <div class="col-md-6 mb-3">
                                    <label for="hourly-property-address" class="form-label">Property Address (Optional):</label>
                                    <input type="text" class="form-control" id="hourly-property-address" placeholder="e.g., St Helier">
                                    <div class="form-text">Will appear on PDF reports</div>
                            </div>
                            <div class="alert alert-info">
                                <i class="fas fa-info-circle"></i> <strong>Company Logo:</strong> Set your company logo once in the <a href="admin.php" target="_blank">Admin Settings</a> panel. It will automatically appear on all your reports.
                            </div>
                            <button type="submit" class="btn btn-primary">Run Analysis</button>
                        </form>
                        <div class="loading mt-2" id="loading-hourly_traffic_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-hourly_traffic_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-google"></i> Google Ads Performance</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze Google Ads campaign performance</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="google_ads_performance.py" data-args="--date yesterday">Yesterday's Report</button>
                            <button class="btn btn-success run-report mb-1" data-script="google_ads_performance.py" data-args="--date today">Today's Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="google_ads_performance.py">Last 30 Days Report</button>
                        </div>
                        <div class="loading mt-2" id="loading-google_ads_performance">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running report...
                        </div>
                        <div class="output" id="output-google_ads_performance"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Google Ads Creative Performance</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze individual Google Ads creative performance</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="google_ads_ad_performance.py" data-args="30">Last 30 Days Report</button>
                            <button class="btn btn-success run-report mb-1" data-script="google_ads_ad_performance.py" data-args="7">Last 7 Days Report</button>
                        </div>
                        <div class="loading mt-2" id="loading-google_ads_ad_performance">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running report...
                        </div>
                        <div class="output" id="output-google_ads_ad_performance"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Mailchimp Performance</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze Mailchimp campaign performance</p>
                        <div class="btn-group-vertical w-100 mb-3" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="mailchimp_performance.py" data-args="--report-type yesterday">Yesterday's Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="mailchimp_performance.py" data-args="--report-type monthly">Monthly Report</button>
                            <button class="btn btn-info run-report mb-1" data-script="mailchimp_performance.py" data-args="--report-type sources">Check Email Sources</button>
                        </div>

                        <!-- Custom Date Range Section -->
                        <div class="border-top pt-3">
                            <h6 class="mb-2"><i class="fas fa-calendar-alt"></i> Custom Date Range</h6>
                            <div class="row g-2 mb-2">
                                <div class="col-6">
                                    <label for="mailchimp-start-date" class="form-label small">Start Date</label>
                                    <input type="date" class="form-control form-control-sm" id="mailchimp-start-date" value="<?php echo date('Y-m-d', strtotime('-7 days')); ?>">
                                </div>
                                <div class="col-6">
                                    <label for="mailchimp-end-date" class="form-label small">End Date</label>
                                    <input type="date" class="form-control form-control-sm" id="mailchimp-end-date" value="<?php echo date('Y-m-d', strtotime('-1 day')); ?>">
                                </div>
                            <button class="btn btn-warning btn-sm run-custom-date-report w-100" data-script="mailchimp_performance.py" data-report-type="date-range" data-start-date-id="mailchimp-start-date" data-end-date-id="mailchimp-end-date">
                                <i class="fas fa-calendar-check"></i> Run Custom Date Range Report
                            </button>
                        </div>

                        <div class="loading mt-2" id="loading-mailchimp_performance">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running report...
                        </div>
                        <div class="output" id="output-mailchimp_performance"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> GSC & GA4 Keywords</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze keywords from Google Search Console and GA4</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="gsc_ga_keywords.py" data-args="--days 1 --date yesterday">Yesterday's Report</button>
                            <button class="btn btn-success run-report mb-1" data-script="gsc_ga_keywords.py" data-args="--days 1 --date today">Today's Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="gsc_ga_keywords.py" data-args="--days 30">30-Day Report</button>
                            <button class="btn btn-info run-report mb-1" data-script="gsc_ga_keywords.py" data-args="--days 7">7-Day Report</button>
                        </div>
                        <div class="loading mt-2" id="loading-gsc_ga_keywords">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running report...
                        </div>
                        <div class="output" id="output-gsc_ga_keywords"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-calendar-day"></i> Yesterday's Traffic Report</h5>
                    </div>
                    <div class="card-body">
                        <p>Complete traffic analysis for yesterday with source/medium breakdown by page</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary btn-lg run-report mb-1" data-script="yesterday_report.py">
                                <i class="fas fa-chart-line"></i> Generate Yesterday's Report
                            </button>
                        </div>
                        <div class="alert alert-info mt-2">
                            <i class="fas fa-info-circle"></i> Shows all pages with traffic sources and medium for yesterday
                        </div>
                        <div class="loading mt-2" id="loading-yesterday_report">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Analyzing yesterday's traffic...
                        </div>
                        <div class="output" id="output-yesterday_report"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Property Traffic Source Comparison</h5>
                    </div>
                    <div class="card-body">
                        <p>Compare traffic sources (Facebook, Google, Email, etc.) across all properties</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary btn-lg run-report mb-1" data-script="property_traffic_comparison.py" data-args="--days 1">
                                <i class="fas fa-calendar-day"></i> Yesterday's Comparison
                            </button>
                            <button class="btn btn-info btn-lg run-report mb-1" data-script="property_traffic_comparison.py" data-args="--days 7">
                                <i class="fas fa-calendar-week"></i> Last 7 Days Comparison
                            </button>
                            <button class="btn btn-secondary btn-lg run-report mb-1" data-script="property_traffic_comparison.py" data-args="--days 14">
                                <i class="fas fa-calendar"></i> Last 14 Days Comparison
                            </button>
                            <button class="btn btn-success btn-lg run-report mb-1" data-script="property_traffic_comparison.py" data-args="--days 30">
                                <i class="fas fa-calendar-alt"></i> Last 30 Days Comparison
                            </button>
                        </div>
                        <div class="alert alert-success mt-2">
                            <i class="fas fa-chart-pie"></i> Shows Facebook Paid, Google Organic, Email, Places.je, Bailiwick, LinkedIn for each property
                        </div>
                        <div class="loading mt-2" id="loading-property_traffic_comparison">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Generating comparison report...
                        </div>
                        <div class="output" id="output-property_traffic_comparison"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Property Daily Traffic Breakdown</h5>
                    </div>
                    <div class="card-body">
                        <p>View day-by-day traffic for a specific property (last 30 days)</p>
                        <div class="mb-3">
                            <label for="property-select" class="form-label">Select Property:</label>
                            <select class="form-select" id="property-select">
                                <option value="">Loading properties...</option>
                            </select>
                        </div>
                        <button class="btn btn-primary btn-lg w-100 run-daily-traffic">
                            <i class="fas fa-calendar"></i> Generate Daily Breakdown
                        </button>
                        <div class="alert alert-info mt-2">
                            <i class="fas fa-info-circle"></i> Shows daily traffic trends with interactive chart
                        </div>
                        <div class="loading mt-2" id="loading-property_daily_traffic">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Generating daily breakdown...
                        </div>
                        <div class="output" id="output-property_daily_traffic"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-file-alt"></i> Top Pages Report</h5>
                    </div>
                    <div class="card-body">
                        <p>Get top performing pages report</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="get_top_pages.py" data-args="--date yesterday">Yesterday's Report</button>
                            <button class="btn btn-success run-report mb-1" data-script="get_top_pages.py" data-args="--date today">Today's Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="get_top_pages.py">Last 30 Days Report</button>
                        </div>
                        <div class="loading mt-2" id="loading-get_top_pages">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running report...
                        </div>
                        <div class="output" id="output-get_top_pages"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Audience Management</h5>
                    </div>
                    <div class="card-body">
                        <p>Create and manage Google Analytics audiences</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="audience_management.py" data-args="--action list">List Audiences</button>
                            <button class="btn btn-info run-report mb-1" data-script="audience_management.py" data-args="--action list --include-metrics">List Audiences with Stats</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="audience_management.py" data-args="--action list --analyze-performance">Analyze Audience Performance</button>
                            <button class="btn btn-success run-report mb-1" data-script="audience_management.py" data-args="--action create --type basic --name 'All Users'">Create All Users Audience</button>
                            <button class="btn btn-warning run-report mb-1" data-script="audience_management.py" data-args="--action create --type cart-abandoners --name 'Cart Abandoners'">Create Cart Abandoners</button>
                        </div>
                        <div class="loading mt-2" id="loading-audience_management">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running audience management...
                        </div>
                        <div class="output" id="output-audience_management"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Audience Statistics</h5>
                    </div>
                    <div class="card-body">
                        <p>Get performance metrics for all GA4 audiences</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="audience_stats.py">Last 30 Days Report</button>
                            <button class="btn btn-success run-report mb-1" data-script="audience_stats.py" data-args="--days 7">Last 7 Days Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="audience_stats.py" data-args="--days 90">Last 90 Days Report</button>
                        </div>
                        <div class="loading mt-2" id="loading-audience_stats">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running audience analysis...
                        </div>
                        <div class="output" id="output-audience_stats"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> User Behavior Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze user paths, engagement patterns, and site behavior</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="user_flow_analysis.py" data-args="behavior 30 100">General Behavior (30 Days)</button>
                            <button class="btn btn-success run-report mb-1" data-script="user_flow_analysis.py" data-args="properties 30 50">Property Pages Analysis</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="user_flow_analysis.py" data-args="behavior 7 50">Quick Behavior Check (7 Days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-user_flow_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Analyzing user behavior...
                        </div>
                        <div class="output" id="output-user_flow_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Conversion Funnel Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze user conversion paths and goal completion</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="conversion_funnel_analysis.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="conversion_funnel_analysis.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="conversion_funnel_analysis.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="conversion_funnel_analysis.py" data-args="contact_form 7">Contact Forms (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="conversion_funnel_analysis.py" data-args="property_inquiry 30">Property Inquiries (30 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-conversion_funnel_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-conversion_funnel_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Bounce Rate Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Identify high-bounce pages and optimization opportunities</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="bounce_rate_analysis.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="bounce_rate_analysis.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="bounce_rate_analysis.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="bounce_rate_analysis.py" data-args="pages 7">Pages Only (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="bounce_rate_analysis.py" data-args="channels 90">Channels Only (90 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-bounce_rate_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-bounce_rate_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Device & Geographic Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze performance by device type and geographic location</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="device_geo_analysis.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="device_geo_analysis.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="device_geo_analysis.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="device_geo_analysis.py" data-args="device 7">Device Only (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="device_geo_analysis.py" data-args="geo 90">Geography Only (90 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-device_geo_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-device_geo_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Technical Performance</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze technical performance and custom events</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="technical_performance.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="technical_performance.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="technical_performance.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="technical_performance.py" data-args="load_times 7">Performance Only (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="technical_performance.py" data-args="errors 90">Events Only (90 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-technical_performance">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-technical_performance"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> User Behavior Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze user navigation patterns and behavior flows</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="user_behavior.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="user_behavior.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="user_behavior.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="user_behavior.py" data-args="flow 7">Flow Only (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="user_behavior.py" data-args="patterns 90">Patterns Only (90 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-user_behavior">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-user_behavior"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Content Performance</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze content engagement and effectiveness</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="content_performance.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="content_performance.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="content_performance.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="content_performance.py" data-args="engagement 7">Engagement Only (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="content_performance.py" data-args="effectiveness 90">Effectiveness Only (90 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-content_performance">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-content_performance"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> SEO Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze search engine optimization performance</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="seo_analysis.py" data-args="all 1 yesterday">Complete Analysis (Yesterday)</button>
                            <button class="btn btn-success run-report mb-1" data-script="seo_analysis.py" data-args="all 1 today">Complete Analysis (Today)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="seo_analysis.py" data-args="all 30">Complete Analysis (30 days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="seo_analysis.py" data-args="organic 7">Organic Only (7 days)</button>
                            <button class="btn btn-warning run-report mb-1" data-script="seo_analysis.py" data-args="health 90">Health Only (90 days)</button>
                        </div>
                        <div class="loading mt-2" id="loading-seo_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-seo_analysis"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> <i class="fab fa-facebook-f"></i> <i class="fab fa-instagram"></i> <i class="fab fa-twitter"></i> Social Media Analytics</h5>
                    </div>
                    <div class="card-body">
                        <p>Discover optimal posting hours for social media platforms by analyzing specific page traffic</p>
                        <form id="social-media-form" class="mb-3">
                            <?php echo csrf_token_field(); ?>
                            <div class="mb-3">
                                <label for="social-page-url" class="form-label">Page URL or Path:</label>
                                <select class="form-select property-url-select" id="social-page-url" required style="width: 100%;">
                                    <option value="">Select a property or type URL...</option>
                                </select>
                                <div class="form-text">
                                    <i class="fas fa-search"></i> Select from property catalog or type custom URL/path
                                </div>
                            <div class="mb-3">
                                <label for="social-analysis-days" class="form-label">Time Period:</label>
                                <select class="form-select" id="social-analysis-days">
                                    <option value="30">Last 30 days</option>
                                    <option value="7">Last 7 days</option>
                                    <option value="90">Last 90 days</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary">Generate Social Media Report</button>
                        </form>
                        <div class="loading mt-2" id="loading-social_media_analytics">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running analysis...
                        </div>
                        <div class="output" id="output-social_media_analytics"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-line"></i> Catalog Analytics Comparison</h5>
                    </div>
                    <div class="card-body">
                        <p class="mb-3">Compare property catalog listings against analytics performance with viewing requests and campaign correlation</p>
                        
                        <!-- Multi-Property Selector -->
                        <form id="catalog-analytics-form">
                            <?php echo csrf_token_field(); ?>
                            
                            <div class="alert alert-info mb-3">
                                <i class="fas fa-info-circle"></i> <strong>Tip:</strong> Select specific properties below to analyze just those properties, or leave blank to analyze all 40 properties in your catalog.
                            </div>
                            
                            <div class="mb-3">
                                <label for="catalog-properties" class="form-label fw-bold">
                                    <i class="fas fa-home text-primary"></i> Select Properties:
                                </label>
                                <select class="form-select property-multi-select" id="catalog-properties" multiple style="width: 100%;">
                                </select>
                                <div class="form-text">
                                    <i class="fas fa-search"></i> Type to search by reference or address (e.g., "STH240092" or "Melrose"). Click to see all properties.
                                </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="catalog-days" class="form-label">Time Period:</label>
                                    <select class="form-select" id="catalog-days">
                                        <option value="7">Last 7 days</option>
                                        <option value="14">Last 14 days</option>
                                        <option value="30" selected>Last 30 days</option>
                                        <option value="60">Last 60 days</option>
                                        <option value="90">Last 90 days</option>
                                    </select>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label class="form-label">Options:</label>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="catalog-recommendations" checked>
                                        <label class="form-check-label" for="catalog-recommendations">
                                            <i class="fas fa-lightbulb text-warning"></i> Marketing recommendations
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="catalog-store-db">
                                        <label class="form-check-label" for="catalog-store-db">
                                            <i class="fas fa-database text-info"></i> Store in database
                                        </label>
                                    </div>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="catalog-export-csv">
                                        <label class="form-check-label" for="catalog-export-csv">
                                            <i class="fas fa-file-csv text-success"></i> Export to CSV
                                        </label>
                                    </div>
                            </div>
                            
                            <button type="submit" class="btn btn-primary btn-lg w-100 mb-3">
                                <i class="fas fa-chart-bar"></i> Run Catalog Analysis
                            </button>
                        </form>
                        
                        <div class="border-top pt-3 mb-3">
                            <h6 class="mb-2"><i class="fas fa-bolt"></i> Quick Actions</h6>
                            <div class="btn-group-vertical w-100" role="group">
                                <button class="btn btn-outline-secondary btn-sm run-report mb-1" data-script="catalog_analytics_report.py" data-args="--days 7">7 Days Quick Report</button>
                                <button class="btn btn-outline-info btn-sm run-report mb-1" data-script="catalog_analytics_report.py" data-args="--low-performers --days 30">Show Low Performers</button>
                            </div>
                        <div class="loading mt-2" id="loading-catalog_analytics_report">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running catalog analysis...
                        </div>
                        <div class="output" id="output-catalog_analytics_report"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-eye"></i> Viewing Requests Manager</h5>
                    </div>
                    <div class="card-body">
                        <p>Track and analyze property viewing requests and correlate with analytics</p>
                        <div class="btn-group-vertical w-100 mb-3" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="viewing_requests_manager.py" data-args="--show-history --days 30">Viewing History (30 Days)</button>
                            <button class="btn btn-success run-report mb-1" data-script="viewing_requests_manager.py" data-args="--analyze --days 30">Analyze Correlations (30 Days)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="viewing_requests_manager.py" data-args="--show-history --days 90">Viewing History (90 Days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="viewing_requests_manager.py" data-args="--top-converters --limit 10">Top 10 Converting Properties</button>
                        </div>
                        <div class="border-top pt-3">
                            <h6 class="mb-2"><i class="fas fa-plus-circle"></i> Add Viewing Request</h6>
                            <p class="small text-muted">Use CLI: --add --reference REF123 --date 2026-01-09 --notes "Details"</p>
                        </div>
                        <div class="loading mt-2" id="loading-viewing_requests_manager">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running viewing analysis...
                        </div>
                        <div class="output" id="output-viewing_requests_manager"></div>
                </div>
            </div>                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-bullhorn"></i> Campaign Manager</h5>
                    </div>
                    <div class="card-body">
                        <p>Track marketing campaigns across all platforms and correlate with viewing requests</p>
                        <div class="btn-group-vertical w-100 mb-3" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="campaign_manager.py" data-args="--list-active">List Active Campaigns</button>
                            <button class="btn btn-success run-report mb-1" data-script="campaign_manager.py" data-args="--correlate-viewings --days 30">Correlate Viewings (30 Days)</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="campaign_manager.py" data-args="--timeline --days 90">Campaign Timeline (90 Days)</button>
                            <button class="btn btn-info run-report mb-1" data-script="campaign_manager.py" data-args="--correlate-viewings --days 7">Quick Correlation (7 Days)</button>
                        </div>
                        <div class="border-top pt-3">
                            <h6 class="mb-2"><i class="fas fa-plus-circle"></i> Campaign Management</h6>
                            <p class="small text-muted mb-1"><strong>Add Campaign:</strong> --add --name "Campaign Name" --platform "Facebook Ads" --start-date 2026-01-09 --budget 500 --properties "REF1,REF2"</p>
                            <p class="small text-muted mb-1"><strong>Analyze Campaign:</strong> --analyze --campaign-id 1</p>
                            <p class="small text-muted mb-0"><strong>End Campaign:</strong> --end-campaign 1</p>
                        </div>
                        <div class="loading mt-2" id="loading-campaign_manager">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running campaign analysis...
                        </div>
                        <div class="output" id="output-campaign_manager"></div>
                </div>
        </div>

        <!-- Property Page URL Tools -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fas fa-home"></i> Property Page Campaign Tools</h5>
                        <small class="text-muted">St Helier Two Bedroom House with Patio & Garden</small>
                    </div>
                    <div class="card-body">
                        <div class="row">                                <h6>Page Preview</h6>
                                <div class="property-preview mb-3">
                                    <div class="preview-image">
                                        <div style="width: 100%; height: 200px; background: linear-gradient(135deg, #007cba 0%, #005a87 100%); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px; font-weight: bold;">
                                            🏠 Property Image
                                        </div>
                                    <div class="preview-details mt-2">
                                        <h6 class="mb-1">St Helier Two Bedroom House with Patio & Garden</h6>
                                        <p class="text-muted small mb-1">Beautiful two bedroom property in St Helier with patio and garden</p>
                                        <p class="text-primary mb-0"><strong>Page:</strong> /properties/st-helier-two-bedroom-house-with-patio-garden</p>
                                        <a href="#" id="preview-link" class="btn btn-sm btn-outline-primary mt-2" target="_blank">
                                            <i class="fas fa-external-link-alt"></i> View Full Page
                                        </a>
                                    </div>
                            </div>                                <h6>Campaign URL Builder</h6>
                                <form id="campaign-url-form">
                                    <div class="mb-3">
                                        <label for="base-url" class="form-label">Base URL:</label>
                                        <input type="text" class="form-control" id="base-url" 
                                               value="https://www.ndestates.com/properties/st-helier-two-bedroom-house-with-patio-garden" readonly>
                                        <div class="form-text">Property page URL (read-only)</div>
                                    <div class="mb-3">
                                        <label for="url-prepend" class="form-label">URL Prepend (Optional):</label>
                                        <input type="text" class="form-control" id="url-prepend" 
                                               placeholder="e.g., /featured or /special-offer">
                                        <div class="form-text">Add a path prefix to the URL (e.g., for campaign tracking)</div>
                                    <div class="mb-3">
                                        <label for="utm-source" class="form-label">UTM Source:</label>
                                        <input type="text" class="form-control" id="utm-source" placeholder="e.g., facebook, google, email">
                                    </div>
                                    <div class="mb-3">
                                        <label for="utm-medium" class="form-label">UTM Medium:</label>
                                        <input type="text" class="form-control" id="utm-medium" placeholder="e.g., cpc, social, email">
                                    </div>
                                    <div class="mb-3">
                                        <label for="utm-campaign" class="form-label">UTM Campaign:</label>
                                        <input type="text" class="form-control" id="utm-campaign" placeholder="e.g., spring-promo-2025">
                                    </div>
                                    <div class="mb-3">
                                        <label for="generated-url" class="form-label">Generated Campaign URL:</label>
                                        <div class="input-group">
                                            <input type="text" class="form-control" id="generated-url" readonly>
                                            <button class="btn btn-outline-secondary" type="button" id="copy-url-btn">
                                                <i class="fas fa-copy"></i> Copy
                                            </button>
                                        </div>
                                        <div class="form-text">Copy this URL for your marketing campaigns</div>
                                    <div class="d-grid">
                                        <button type="button" class="btn btn-primary" id="generate-url-btn">
                                            <i class="fas fa-magic"></i> Generate Campaign URL
                                        </button>
                                    </div>
                                </form>
                            </div>
                    </div>
            </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>
    <script>
        // Initialize Select2 dropdowns for properties/URLs
        $(document).ready(function() {
            // Initialize property/URL selector with AJAX
            $('.property-url-select').select2({
                theme: 'bootstrap-5',
                placeholder: 'Select a property or type URL...',
                allowClear: true,
                tags: true, // Allow custom URLs
                ajax: {
                    url: 'api_dropdowns.php?action=urls',
                    dataType: 'json',
                    delay: 250,
                    processResults: function(data) {
                        return { results: data };
                    },
                    cache: true
                },
                minimumInputLength: 0
            });

            // Initialize campaign selector
            $('.campaign-select').select2({
                theme: 'bootstrap-5',
                placeholder: 'Select campaign(s)...',
                allowClear: true,
                multiple: true,
                ajax: {
                    url: 'api_dropdowns.php?action=campaigns',
                    dataType: 'json',
                    delay: 250,
                    processResults: function(data) {
                        return { results: data };
                    },
                    cache: true
                }
            });

            // Initialize property selector (multi-select)
            $('.property-multi-select').select2({
                theme: 'bootstrap-5',
                placeholder: 'Select properties...',
                allowClear: true,
                multiple: true,
                ajax: {
                    url: 'api_dropdowns.php?action=properties',
                    dataType: 'json',
                    delay: 250,
                    processResults: function(data) {
                        return { results: data };
                    },
                    cache: true
                }
            });
        });

        // Request queue to prevent race conditions
        const requestQueue = [];
        let isProcessingQueue = false;

        function queueRequest(fn) {
            return new Promise((resolve, reject) => {
                requestQueue.push({ fn, resolve, reject });
                processQueue();
            });
        }

        async function processQueue() {
            if (isProcessingQueue || requestQueue.length === 0) return;
            
            isProcessingQueue = true;
            const { fn, resolve, reject } = requestQueue.shift();
            
            try {
                const result = await fn();
                resolve(result);
            } catch (error) {
                reject(error);
            } finally {
                isProcessingQueue = false;
                // Process next item after delay
                if (requestQueue.length > 0) {
                    setTimeout(processQueue, 500);
                }
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            // Handle regular run buttons
            const runButtons = document.querySelectorAll('.run-report');

            runButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const scriptName = this.getAttribute('data-script');
                    const scriptArgs = this.getAttribute('data-args') || '';
                    runScript(scriptName, scriptArgs);
                });
            });

            // Handle social media analytics button
            const socialButtons = document.querySelectorAll('.run-report-social');

            socialButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const scriptName = this.getAttribute('data-script');
                    runSocialScript(scriptName);
                });
            });

            // Handle page traffic analysis form
            const pageTrafficForm = document.getElementById('page-traffic-form');
            if (pageTrafficForm) {
                // Handle time period selection
                const analysisDaysSelect = document.getElementById('analysis-days');
                const customDateRange = document.getElementById('custom-date-range');
                const startDateInput = document.getElementById('start-date');
                const endDateInput = document.getElementById('end-date');
                analysisDaysSelect.addEventListener('change', function() {
                    if (this.value === 'custom') {
                        customDateRange.style.display = 'block';
                        startDateInput.setAttribute('required', 'required');
                        endDateInput.setAttribute('required', 'required');
                    } else {
                        customDateRange.style.display = 'none';
                        startDateInput.removeAttribute('required');
                        endDateInput.removeAttribute('required');
                    }
                });

                // Toggle between single and multi-property mode
                const singleModeRadio = document.getElementById('single-property-mode');
                const multiModeRadio = document.getElementById('multi-property-mode');
                const singleSelector = document.getElementById('single-property-selector');
                const multiSelector = document.getElementById('multi-property-selector');
                
                singleModeRadio.addEventListener('change', function() {
                    if (this.checked) {
                        singleSelector.style.display = 'block';
                        multiSelector.style.display = 'none';
                    }
                });
                
                multiModeRadio.addEventListener('change', function() {
                    if (this.checked) {
                        singleSelector.style.display = 'none';
                        multiSelector.style.display = 'block';
                    }
                });

                pageTrafficForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    const isMultiMode = document.getElementById('multi-property-mode').checked;
                    const days = document.getElementById('analysis-days').value;
                    const propertyName = document.getElementById('property-name').value.trim();
                    const propertyAddress = document.getElementById('property-address').value.trim();

                    let urls = [];
                    if (isMultiMode) {
                        const selectedOptions = $('#page-urls-multi').select2('data');
                        urls = selectedOptions.map(opt => opt.id);
                        if (urls.length === 0) {
                            alert('Please select at least one property');
                            return;
                        }
                    } else {
                        const url = document.getElementById('page-url').value.trim();
                        if (!url) {
                            alert('Please enter a page URL or path');
                            return;
                        }
                        urls = [url];
                    }

                    // Run analysis for each URL using request queue
                    const promises = urls.map((url) => {
                        return queueRequest(() => {
                            return new Promise((resolve, reject) => {
                                let scriptArgs;
                                if (days === 'custom') {
                                    const startDate = document.getElementById('start-date').value;
                                    const endDate = document.getElementById('end-date').value;
                                    if (!startDate || !endDate) {
                                        reject(new Error('Please select both start and end dates'));
                                        return;
                                    }
                                    if (startDate > endDate) {
                                        reject(new Error('Start date cannot be after end date'));
                                        return;
                                    }
                                    scriptArgs = `${url} --start-date ${startDate} --end-date ${endDate}`;
                                } else {
                                    scriptArgs = `${url} ${days}`;
                                }
                                if (propertyName) scriptArgs += ` --property-name "${propertyName}"`;
                                if (propertyAddress) scriptArgs += ` --property-address "${propertyAddress}"`;

                                // Execute request
                                const formData = new FormData();
                                formData.append('script', 'page_traffic_analysis.py');
                                formData.append('args', scriptArgs);
                                const csrfToken = document.querySelector('input[name="csrf_token"]');
                                if (csrfToken) formData.append('csrf_token', csrfToken.value);

                                fetch('run_report.php', {
                                    method: 'POST',
                                    body: formData
                                })
                                .then(response => response.text())
                                .then(data => {
                                    const outputDiv = document.getElementById('output-page_traffic_analysis');
                                    if (outputDiv) {
                                        outputDiv.innerHTML += formatScriptOutput(data) + '<hr>';
                                    }
                                    resolve(data);
                                })
                                .catch(reject);
                            });
                        });
                    });

                    // Wait for all requests to complete
                    Promise.all(promises)
                        .then(() => {
                            console.log('All property analyses completed');
                        })
                        .catch(error => {
                            console.error('Error in property analysis:', error);
                            alert('Error: ' + error.message);
                        });
                });
            }

            // Handle hourly traffic analysis form
            const hourlyTrafficForm = document.getElementById('hourly-traffic-form');
            if (hourlyTrafficForm) {
                // Handle time period selection
                const hourlyAnalysisDaysSelect = document.getElementById('hourly-analysis-days');
                const hourlyCustomDateRange = document.getElementById('hourly-custom-date-range');
                const hourlyStartDateInput = document.getElementById('hourly-start-date');
                const hourlyEndDateInput = document.getElementById('hourly-end-date');
                hourlyAnalysisDaysSelect.addEventListener('change', function() {
                    if (this.value === 'custom') {
                        hourlyCustomDateRange.style.display = 'block';
                        hourlyStartDateInput.setAttribute('required', 'required');
                        hourlyEndDateInput.setAttribute('required', 'required');
                    } else {
                        hourlyCustomDateRange.style.display = 'none';
                        hourlyStartDateInput.removeAttribute('required');
                        hourlyEndDateInput.removeAttribute('required');
                    }
                });

                hourlyTrafficForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const url = document.getElementById('hourly-page-url').value.trim();
                    const days = document.getElementById('hourly-analysis-days').value;
                    const propertyName = document.getElementById('hourly-property-name').value.trim();
                    const propertyAddress = document.getElementById('hourly-property-address').value.trim();

                    if (!url) {
                        alert('Please enter a page URL or path');
                        return;
                    }

                    let scriptArgs;
                    if (days === 'custom') {
                        const startDate = document.getElementById('hourly-start-date').value;
                        const endDate = document.getElementById('hourly-end-date').value;
                        if (!startDate || !endDate) {
                            alert('Please select both start and end dates');
                            return;
                        }
                        if (startDate > endDate) {
                            alert('Start date cannot be after end date');
                            return;
                        }
                        scriptArgs = `${url} --start-date ${startDate} --end-date ${endDate}`;
                    } else {
                        scriptArgs = `${url} ${days}`;
                    }
                    if (propertyName) scriptArgs += ` --property-name "${propertyName}"`;
                    if (propertyAddress) scriptArgs += ` --property-address "${propertyAddress}"`;

                    runScript('hourly_traffic_analysis.py', scriptArgs);
                });
            }

            // Handle load popular pages button
            const loadPopularBtn = document.getElementById('load-popular-pages');
            if (loadPopularBtn) {
                loadPopularBtn.addEventListener('click', function() {
                    const select = document.getElementById('popular-pages-select');
                    const button = this;

                    button.disabled = true;
                    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';

                    fetch('get_popular_pages.php')
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error loading popular pages: ' + data.error);
                                return;
                            }

                            // Clear existing options except the first one
                            select.innerHTML = '<option value="">Select a popular page...</option>';

                            // Add popular pages
                            data.pages.forEach(page => {
                                const option = document.createElement('option');
                                option.value = page.path || page;
                                option.textContent = `${page.path || page} (${page.users || 'popular'})`;
                                select.appendChild(option);
                            });

                            select.style.display = 'block';
                        })
                        .catch(error => {
                            alert('Error loading popular pages: ' + error.message);
                        })
                        .finally(() => {
                            button.disabled = false;
                            button.innerHTML = 'Load Popular Pages';
                        });
                });
            }

            // Handle load popular pages button for hourly analysis
            const loadHourlyPopularBtn = document.getElementById('load-hourly-popular-pages');
            if (loadHourlyPopularBtn) {
                loadHourlyPopularBtn.addEventListener('click', function() {
                    const select = document.getElementById('hourly-popular-pages-select');
                    const button = this;

                    button.disabled = true;
                    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';

                    fetch('get_popular_pages.php')
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error loading popular pages: ' + data.error);
                                return;
                            }

                            // Clear existing options except the first one
                            select.innerHTML = '<option value="">Select a popular page...</option>';

                            // Add popular pages
                            data.pages.forEach(page => {
                                const option = document.createElement('option');
                                option.value = page.path || page;
                                option.textContent = `${page.path || page} (${page.users || 'popular'})`;
                                select.appendChild(option);
                            });

                            select.style.display = 'block';
                        })
                        .catch(error => {
                            alert('Error loading popular pages: ' + error.message);
                        })
                        .finally(() => {
                            button.disabled = false;
                            button.innerHTML = 'Load Popular Pages';
                        });
                });
            }

            // Handle popular pages selection
            const popularPagesSelect = document.getElementById('popular-pages-select');
            
            // Handle catalog analytics form
            const catalogAnalyticsForm = document.getElementById('catalog-analytics-form');
            if (catalogAnalyticsForm) {
                let isRunning = false; // Prevent duplicate submissions
                
                catalogAnalyticsForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    
                    if (isRunning) {
                        alert('Analysis is already running. Please wait...');
                        return;
                    }
                    
                    isRunning = true;
                    const submitBtn = this.querySelector('button[type="submit"]');
                    const originalBtnText = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Running...';
                    
                    const selectedProperties = $('#catalog-properties').select2('data');
                    const days = document.getElementById('catalog-days').value;
                    const recommendations = document.getElementById('catalog-recommendations').checked;
                    const storeDb = document.getElementById('catalog-store-db').checked;
                    const exportCsv = document.getElementById('catalog-export-csv').checked;
                    
                    // Build script arguments
                    let scriptArgs = `--days ${days}`;
                    if (recommendations) scriptArgs += ' --recommendations';
                    if (storeDb) scriptArgs += ' --store-db';
                    if (exportCsv) scriptArgs += ' --export-csv';
                    
                    // If specific properties selected, add them as filter
                    if (selectedProperties.length > 0) {
                        const references = selectedProperties.map(p => p.id).join(',');
                        scriptArgs += ` --properties ${references}`; // No quotes - shell escaping handled by FormData
                    }
                    
                    // Queue the request to prevent race conditions
                    queueRequest(() => {
                        return new Promise((resolve, reject) => {
                            const formData = new FormData();
                            formData.append('script', 'catalog_analytics_report.py');
                            formData.append('args', scriptArgs);
                            const csrfToken = document.querySelector('input[name="csrf_token"]');
                            if (csrfToken) formData.append('csrf_token', csrfToken.value);
                            
                            fetch('run_report.php', {
                                method: 'POST',
                                body: formData
                            })
                            .then(response => response.text())
                            .then(data => {
                                const outputDiv = document.getElementById('output-catalog_analytics_report');
                                if (outputDiv) {
                                    outputDiv.innerHTML = formatScriptOutput(data);
                                }
                                resolve(data);
                            })
                            .catch(reject);
                        });
                    })
                    .then(() => {
                        console.log('Catalog analysis completed');
                    })
                    .catch(error => {
                        console.error('Error in catalog analysis:', error);
                        alert('Error: ' + error.message);
                    })
                    .finally(() => {
                        isRunning = false;
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalBtnText;
                    });
                });
            }
            if (popularPagesSelect) {
                popularPagesSelect.addEventListener('change', function() {
                    const selectedValue = this.value;
                    if (selectedValue) {
                        document.getElementById('page-url').value = selectedValue;
                    }
                });
            }

            // Handle hourly popular pages selection
            const hourlyPopularPagesSelect = document.getElementById('hourly-popular-pages-select');
            if (hourlyPopularPagesSelect) {
                hourlyPopularPagesSelect.addEventListener('change', function() {
                    const selectedValue = this.value;
                    if (selectedValue) {
                        document.getElementById('hourly-page-url').value = selectedValue;
                    }
                });
            }

            // Handle social media analysis form
            const socialMediaForm = document.getElementById('social-media-form');
            if (socialMediaForm) {
                socialMediaForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const url = document.getElementById('social-page-url').value.trim();
                    const days = document.getElementById('social-analysis-days').value;

                    if (!url) {
                        alert('Please enter a page URL or path');
                        return;
                    }

                    const scriptArgs = `${url} ${days}`;
                    runScript('hourly_traffic_analysis.py', scriptArgs);
                });
            }

            // Handle load popular pages button for social media
            const loadSocialPopularBtn = document.getElementById('load-social-popular-pages');
            if (loadSocialPopularBtn) {
                loadSocialPopularBtn.addEventListener('click', function() {
                    const select = document.getElementById('social-popular-pages-select');
                    const button = this;

                    button.disabled = true;
                    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';

                    fetch('get_popular_pages.php')
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert('Error loading popular pages: ' + data.error);
                                return;
                            }

                            // Clear existing options except the first one
                            select.innerHTML = '<option value="">Select a popular page...</option>';

                            // Add popular pages
                            data.pages.forEach(page => {
                                const option = document.createElement('option');
                                option.value = page.path || page;
                                option.textContent = `${page.path || page} (${page.users || 'popular'})`;
                                select.appendChild(option);
                            });

                            select.style.display = 'block';
                        })
                        .catch(error => {
                            alert('Error loading popular pages: ' + error.message);
                        })
                        .finally(() => {
                            button.disabled = false;
                            button.innerHTML = 'Load Popular Pages';
                        });
                });
            }

            // Handle popular pages selection for social media
            const socialPopularPagesSelect = document.getElementById('social-popular-pages-select');
            if (socialPopularPagesSelect) {
                socialPopularPagesSelect.addEventListener('change', function() {
                    const selectedValue = this.value;
                    if (selectedValue) {
                        document.getElementById('social-page-url').value = selectedValue;
                    }
                });
            }

            // Handle mailchimp custom date range form
            const mailchimpDateRangeForm = document.getElementById('mailchimp-date-range-form');
            if (mailchimpDateRangeForm) {
                mailchimpDateRangeForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const startDate = document.getElementById('mailchimp-start-date').value;
                    const endDate = document.getElementById('mailchimp-end-date').value;

                    if (!startDate || !endDate) {
                        alert('Please select both start and end dates');
                        return;
                    }

                    const scriptArgs = `--start-date ${startDate} --end-date ${endDate}`;
                    runScript('mailchimp_performance.py', scriptArgs);
                });
            }

            function runScript(scriptName, scriptArgs) {
                const scriptBaseName = scriptName.replace('.py', '');
                const loadingDiv = document.getElementById('loading-' + scriptBaseName);
                const outputDiv = document.getElementById('output-' + scriptBaseName);

                // Show loading
                if (loadingDiv) loadingDiv.style.display = 'block';
                if (outputDiv) outputDiv.innerHTML = '';

                // Disable form/button
                const submitBtn = document.querySelector('#page-traffic-form button[type="submit"]');
                if (submitBtn) submitBtn.disabled = true;

                // Disable hourly form button
                const hourlySubmitBtn = document.querySelector('#hourly-traffic-form button[type="submit"]');
                if (hourlySubmitBtn) hourlySubmitBtn.disabled = true;

                // Disable social media form button
                const socialSubmitBtn = document.querySelector('#social-media-form button[type="submit"]');
                if (socialSubmitBtn) socialSubmitBtn.disabled = true;

                // Disable regular buttons with this script name
                const buttons = document.querySelectorAll(`[data-script="${scriptName}"]`);
                buttons.forEach(btn => btn.disabled = true);

                // Prepare form data
                const formData = new FormData();
                formData.append('script', scriptName);
                if (scriptArgs) {
                    formData.append('args', scriptArgs);
                }
                
                // Add CSRF token
                const csrfToken = document.querySelector('input[name="csrf_token"]');
                if (csrfToken) {
                    formData.append('csrf_token', csrfToken.value);
                }

                // Make AJAX request
                fetch('run_report.php', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    // Check if response is a redirect (authentication failed)
                    if (response.redirected || response.url.includes('index.php')) {
                        window.location.href = 'index.php?error=session_expired';
                        return;
                    }
                    return response.text();
                })
                .then(data => {
                    if (data) {
                        // Check if response contains login form (session expired)
                        if (data.includes('Login Required') || data.includes('csrf_token_field')) {
                            window.location.href = 'index.php?error=session_expired';
                            return;
                        }
                        if (outputDiv) outputDiv.innerHTML = formatScriptOutput(data);
                    }
                })
                .catch(error => {
                    if (outputDiv) outputDiv.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
                })
                .finally(() => {
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    if (submitBtn) submitBtn.disabled = false;
                    if (hourlySubmitBtn) hourlySubmitBtn.disabled = false;
                    if (socialSubmitBtn) socialSubmitBtn.disabled = false;
                    buttons.forEach(btn => btn.disabled = false);
                });
            }

            function runScriptWithData(endpoint, formData) {
                // Extract script name from formData for loading/output divs
                const scriptName = formData.get('script');
                const scriptBaseName = scriptName.replace('.py', '');
                const loadingDiv = document.getElementById('loading-' + scriptBaseName);
                const outputDiv = document.getElementById('output-' + scriptBaseName);

                // Show loading
                if (loadingDiv) loadingDiv.style.display = 'block';
                if (outputDiv) outputDiv.innerHTML = '';

                // Disable form/button
                const submitBtn = document.querySelector('#page-traffic-form button[type="submit"]');
                if (submitBtn) submitBtn.disabled = true;

                // Disable hourly form button
                const hourlySubmitBtn = document.querySelector('#hourly-traffic-form button[type="submit"]');
                if (hourlySubmitBtn) hourlySubmitBtn.disabled = true;

                // Disable social media form button
                const socialSubmitBtn = document.querySelector('#social-media-form button[type="submit"]');
                if (socialSubmitBtn) socialSubmitBtn.disabled = true;

                // Disable regular buttons with this script name
                const buttons = document.querySelectorAll(`[data-script="${scriptName}"]`);
                buttons.forEach(btn => btn.disabled = true);

                // Make AJAX request
                fetch(endpoint, {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    // Check if response is a redirect (authentication failed)
                    if (response.redirected || response.url.includes('index.php')) {
                        window.location.href = 'index.php?error=session_expired';
                        return;
                    }
                    return response.text();
                })
                .then(data => {
                    if (data) {
                        // Check if response contains login form (session expired)
                        if (data.includes('Login Required') || data.includes('csrf_token_field')) {
                            window.location.href = 'index.php?error=session_expired';
                            return;
                        }
                        if (outputDiv) outputDiv.innerHTML = formatScriptOutput(data);
                    }
                })
                .catch(error => {
                    if (outputDiv) outputDiv.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
                })
                .finally(() => {
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    if (submitBtn) submitBtn.disabled = false;
                    if (hourlySubmitBtn) hourlySubmitBtn.disabled = false;
                    if (socialSubmitBtn) socialSubmitBtn.disabled = false;
                    buttons.forEach(btn => btn.disabled = false);
                });
            }

            function runSocialScript(scriptName) {
                const loadingDiv = document.getElementById('loading-social_media_analytics');
                const outputDiv = document.getElementById('output-social_media_analytics');

                // Show loading
                if (loadingDiv) loadingDiv.style.display = 'block';
                if (outputDiv) outputDiv.innerHTML = '';

                // Disable social media buttons
                const buttons = document.querySelectorAll(`[data-script="${scriptName}"]`);
                buttons.forEach(btn => btn.disabled = true);

                // Prepare form data
                const formData = new FormData();
                formData.append('script', scriptName);
                
                // Add CSRF token
                const csrfToken = document.querySelector('input[name="csrf_token"]');
                if (csrfToken) {
                    formData.append('csrf_token', csrfToken.value);
                }

                // Make AJAX request
                fetch('run_report.php', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    // Check if response is a redirect (authentication failed)
                    if (response.redirected || response.url.includes('index.php')) {
                        window.location.href = 'index.php?error=session_expired';
                        return;
                    }
                    return response.text();
                })
                .then(data => {
                    if (data) {
                        // Check if response contains login form (session expired)
                        if (data.includes('Login Required') || data.includes('csrf_token_field')) {
                            window.location.href = 'index.php?error=session_expired';
                            return;
                        }
                        // Check if it's HTML (social media dashboard) or plain text (error)
                        if (data.includes('<html>') || data.includes('<!DOCTYPE html>')) {
                            // It's HTML, open in new window
                            const newWindow = window.open('', '_blank');
                            newWindow.document.write(data);
                            newWindow.document.close();
                            if (outputDiv) outputDiv.innerHTML = '<div class="alert alert-success">Social media analytics opened in new window/tab</div>';
                        } else {
                            // It's plain text, display with formatting
                            if (outputDiv) outputDiv.innerHTML = formatScriptOutput(data);
                        }
                    }
                })
                .catch(error => {
                    if (outputDiv) outputDiv.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
                })
                .finally(() => {
                    if (loadingDiv) loadingDiv.style.display = 'none';
                    buttons.forEach(btn => btn.disabled = false);
                });
            }
        });

        // Property Page Campaign URL Builder functionality
        const generateUrlBtn = document.getElementById('generate-url-btn');
        const copyUrlBtn = document.getElementById('copy-url-btn');
        const generatedUrlInput = document.getElementById('generated-url');
        const previewLink = document.getElementById('preview-link');

        if (generateUrlBtn) {
            generateUrlBtn.addEventListener('click', function() {
                const baseUrl = document.getElementById('base-url').value;
                const prepend = document.getElementById('url-prepend').value.trim();
                const utmSource = document.getElementById('utm-source').value.trim();
                const utmMedium = document.getElementById('utm-medium').value.trim();
                const utmCampaign = document.getElementById('utm-campaign').value.trim();

                let finalUrl = baseUrl;

                // Add prepend if provided
                if (prepend) {
                    // Ensure prepend starts with /
                    const cleanPrepend = prepend.startsWith('/') ? prepend : '/' + prepend;
                    // Remove trailing / from base URL if present
                    const cleanBase = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
                    finalUrl = cleanBase + cleanPrepend;
                }

                // Add UTM parameters
                const utmParams = [];
                if (utmSource) utmParams.push(`utm_source=${encodeURIComponent(utmSource)}`);
                if (utmMedium) utmParams.push(`utm_medium=${encodeURIComponent(utmMedium)}`);
                if (utmCampaign) utmParams.push(`utm_campaign=${encodeURIComponent(utmCampaign)}`);

                if (utmParams.length > 0) {
                    const separator = finalUrl.includes('?') ? '&' : '?';
                    finalUrl += separator + utmParams.join('&');
                }

                generatedUrlInput.value = finalUrl;
                
                // Update preview link
                previewLink.href = finalUrl;
                previewLink.style.display = 'inline-block';
            });
        }

        if (copyUrlBtn) {
            copyUrlBtn.addEventListener('click', function() {
                const url = generatedUrlInput.value;
                if (!url) {
                    alert('Please generate a URL first');
                    return;
                }

                navigator.clipboard.writeText(url).then(function() {
                    // Show success feedback
                    const originalText = copyUrlBtn.innerHTML;
                    copyUrlBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    copyUrlBtn.classList.remove('btn-outline-secondary');
                    copyUrlBtn.classList.add('btn-success');
                    
                    setTimeout(() => {
                        copyUrlBtn.innerHTML = originalText;
                        copyUrlBtn.classList.remove('btn-success');
                        copyUrlBtn.classList.add('btn-outline-secondary');
                    }, 2000);
                }).catch(function(err) {
                    // Fallback for older browsers
                    generatedUrlInput.select();
                    document.execCommand('copy');
                    
                    const originalText = copyUrlBtn.innerHTML;
                    copyUrlBtn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    copyUrlBtn.classList.remove('btn-outline-secondary');
                    copyUrlBtn.classList.add('btn-success');
                    
                    setTimeout(() => {
                        copyUrlBtn.innerHTML = originalText;
                        copyUrlBtn.classList.remove('btn-success');
                        copyUrlBtn.classList.add('btn-outline-secondary');
                    }, 2000);
                });
            });
        }

        // Set initial preview link
        if (previewLink) {
            previewLink.href = document.getElementById('base-url').value;
        }
    </script>
        });
    </script>
    <script>
        // Load site metrics on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadSiteMetrics();
        });

        function formatNumber(num) {
            if (num >= 1000000) {
                return (num / 1000000).toFixed(1) + 'm';
            } else if (num >= 1000) {
                return (num / 1000).toFixed(1) + 'k';
            } else {
                return num.toString();
            }
        }

        function loadSiteMetrics(forceRefresh = false) {
            const container = document.getElementById('metricsContainer');
            const refreshBtn = document.getElementById('refreshBtn');
            const cacheKey = 'siteMetrics';
            const cacheExpiry = 10 * 60 * 1000; // 10 minutes in milliseconds
            
            // Show loading state on refresh button if it exists
            if (forceRefresh && refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
                refreshBtn.disabled = true;
            }
            
            // Check for cached data if not forcing refresh
            if (!forceRefresh) {
                const cached = localStorage.getItem(cacheKey);
                if (cached) {
                    try {
                        const cacheData = JSON.parse(cached);
                        const now = Date.now();
                        
                        // Check if cache is still valid (less than 10 minutes old)
                        if (now - cacheData.timestamp < cacheExpiry) {
                            renderMetrics(cacheData.data, true); // true = from cache
                            return;
                        }
                    } catch (e) {
                        // Invalid cache, continue to fetch fresh data
                    }
                }
            }
            
            // Show loading state
            container.innerHTML = `
                <div class="metrics-loading">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="mt-2">Loading site metrics...</div>
            `;
            
            fetch('api/site_metrics.php')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        container.innerHTML = `
                            <div class="metrics-error">
                                <strong>⚠️ Error loading metrics:</strong> ${data.error}
                            </div>
                        `;
                        return;
                    }

                    // Cache the data
                    const cacheData = {
                        data: data,
                        timestamp: Date.now()
                    };
                    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
                    
                    renderMetrics(data, false); // false = fresh data
                })
                .catch(error => {
                    // Reset refresh button if it exists
                    const refreshBtn = document.getElementById('refreshBtn');
                    if (refreshBtn) {
                        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                        refreshBtn.disabled = false;
                    }
                    
                    container.innerHTML = `
                        <div class="metrics-error">
                            <strong>⚠️ Failed to load metrics:</strong> ${error.message}
                        </div>
                    `;
                });
        }

        function renderMetrics(data, fromCache = false) {
            const container = document.getElementById('metricsContainer');
            const refreshBtn = document.getElementById('refreshBtn');
            
            // Reset refresh button if it exists
            if (refreshBtn) {
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
                refreshBtn.disabled = false;
            }
            
            container.innerHTML = `
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <i class="fas fa-chart-line" style="font-size: 1.8rem; margin-right: 15px;"></i>
                    <div style="flex: 1;">
                        <h2 style="margin: 0;">Site Metrics ${fromCache ? '<small class="text-muted">(cached)</small>' : ''}</h2>
                        <div class="subtitle">Real-time analytics overview</div>
                    <button onclick="loadSiteMetrics(true)" class="btn btn-sm btn-outline-light" title="Refresh metrics" id="refreshBtn">
                        <i class="fas fa-sync-alt"></i> Refresh
                    </button>
                </div>
                <div class="metrics-row">
                    <div class="metric-card">
                        <div class="metric-icon">📄</div>
                        <div class="metric-label">Total Pages Viewed</div>
                        <div class="metric-period">
                            <span class="metric-period-label">24 Hours</span>
                            <span class="metric-value">${formatNumber(data['24_hours'].total_pageviews)}</span>
                        </div>
                        <div class="metric-period">
                            <span class="metric-period-label">30 Days</span>
                            <span class="metric-value">${formatNumber(data['30_days'].total_pageviews)}</span>
                        </div>
                        <div class="metric-period">
                            <span class="metric-period-label">Annual</span>
                            <span class="metric-value">${formatNumber(data.annual.total_pageviews)}</span>
                        </div>
                    <div class="metric-card">
                        <div class="metric-icon">👁️</div>
                        <div class="metric-label">Individual Properties Viewed</div>
                        <div class="metric-period">
                            <span class="metric-period-label">24 Hours</span>
                            <span class="metric-value">${formatNumber(data['24_hours'].unique_properties)}</span>
                        </div>
                        <div class="metric-period">
                            <span class="metric-period-label">30 Days</span>
                            <span class="metric-value">${formatNumber(data['30_days'].unique_properties)}</span>
                        </div>
                        <div class="metric-period">
                            <span class="metric-period-label">Annual</span>
                            <span class="metric-value">${formatNumber(data.annual.unique_properties)}</span>
                        </div>
                    <div class="metric-card">
                        <div class="metric-icon">👥</div>
                        <div class="metric-label">Unique Visitors</div>
                        <div class="metric-period">
                            <span class="metric-period-label">24 Hours</span>
                            <span class="metric-value">${formatNumber(data['24_hours'].total_users)}</span>
                        </div>
                        <div class="metric-period">
                            <span class="metric-period-label">30 Days</span>
                            <span class="metric-value">${formatNumber(data['30_days'].total_users)}</span>
                        </div>
                        <div class="metric-period">
                            <span class="metric-period-label">Annual</span>
                            <span class="metric-value">${formatNumber(data.annual.total_users)}</span>
                        </div>
                </div>
            `;
        }

        // Load properties into dropdown for daily traffic report
        fetch('api_dropdowns.php?action=properties')
            .then(response => response.json())
            .then(data => {
                const select = document.getElementById('property-select');
                select.innerHTML = '<option value="">Select a property...</option>';
                data.forEach(prop => {
                    const option = document.createElement('option');
                    option.value = prop.id;
                    option.textContent = prop.text;
                    select.appendChild(option);
                });
            })
            .catch(error => {
                console.error('Error loading properties:', error);
                const select = document.getElementById('property-select');
                select.innerHTML = '<option value="">Error loading properties</option>';
            });

        // Handle daily traffic report generation
        document.querySelector('.run-daily-traffic')?.addEventListener('click', function() {
            const propertySelect = document.getElementById('property-select');
            const propertyRef = propertySelect.value;
            
            if (!propertyRef) {
                alert('Please select a property');
                return;
            }
            
            const scriptName = 'property_daily_traffic.py';
            const args = `--property ${propertyRef}`;
            runScript(scriptName, args);
        });
    </script>

    <!-- UI Enhancement Functions -->
    <script src="js/ui-enhancements.js"></script>

    <!-- Sidebar Toggle Functionality -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const sidebarToggle = document.getElementById('sidebarToggle');
            const sidebar = document.getElementById('sidebar');

            if (sidebarToggle && sidebar) {
                sidebarToggle.addEventListener('click', function() {
                    sidebar.classList.toggle('open');
                });

                // Close sidebar when clicking outside on mobile
                document.addEventListener('click', function(event) {
                    if (window.innerWidth <= 1024) {
                        if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                            sidebar.classList.remove('open');
                        }
                    }
                });
            }
        });
    </script>

      </div> <!-- End cards-grid -->
    </main> <!-- End content-area -->
  </div> <!-- End main-area -->
</div> <!-- End app-shell -->

    <script src="js/filament-layout.js"></script>
</body>
</html>
```