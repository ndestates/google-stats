<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Analytics Reports</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
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
    <div class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1 class="mb-0">Google Analytics Reports</h1>
            <nav>
                <a href="documentation.php" class="btn btn-outline-primary">
                    <i class="fas fa-book"></i> Documentation
                </a>
            </nav>
        </div>

        <!-- Site Metrics Dashboard -->
        <div class="metrics-dashboard" id="metricsContainer">
            <div class="metrics-loading">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="mt-2">Loading site metrics...</div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Page Traffic Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze page traffic and performance metrics</p>
                        <form id="page-traffic-form" class="mb-3">
                            <div class="mb-3">
                                <label for="page-url" class="form-label">Page URL or Path:</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="page-url" placeholder="/valuations or https://www.ndestates.com/valuations" required>
                                    <button class="btn btn-outline-secondary" type="button" id="load-popular-pages">Load Popular Pages</button>
                                </div>
                                <select class="form-select mt-2" id="popular-pages-select" style="display: none;">
                                    <option value="">Select a popular page...</option>
                                </select>
                                <div class="form-text">
                                    Enter a page path (e.g., /valuations) or full URL, or load and select from popular pages above
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="analysis-days" class="form-label">Time Period:</label>
                                <select class="form-select" id="analysis-days">
                                    <option value="30">Last 30 days</option>
                                    <option value="7">Last 7 days</option>
                                    <option value="90">Last 90 days</option>
                                </select>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="property-name" class="form-label">Property Name (Optional):</label>
                                    <input type="text" class="form-control" id="property-name" placeholder="e.g., 4 Melrose Apartments">
                                    <div class="form-text">Will appear on PDF reports</div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="property-address" class="form-label">Property Address (Optional):</label>
                                    <input type="text" class="form-control" id="property-address" placeholder="e.g., St Helier">
                                    <div class="form-text">Will appear on PDF reports</div>
                                </div>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Hourly Traffic Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze hourly traffic patterns and best times by source</p>
                        <form id="hourly-traffic-form" class="mb-3">
                            <div class="mb-3">
                                <label for="hourly-page-url" class="form-label">Page URL or Path:</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="hourly-page-url" placeholder="/valuations or https://www.ndestates.com/valuations" required>
                                    <button class="btn btn-outline-secondary" type="button" id="load-hourly-popular-pages">Load Popular Pages</button>
                                </div>
                                <select class="form-select mt-2" id="hourly-popular-pages-select" style="display: none;">
                                    <option value="">Select a popular page...</option>
                                </select>
                                <div class="form-text">
                                    Enter a page path (e.g., /valuations) or full URL, or load and select from popular pages above
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="hourly-analysis-days" class="form-label">Time Period:</label>
                                <select class="form-select" id="hourly-analysis-days">
                                    <option value="30">Last 30 days</option>
                                    <option value="7">Last 7 days</option>
                                    <option value="90">Last 90 days</option>
                                </select>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="hourly-property-name" class="form-label">Property Name (Optional):</label>
                                    <input type="text" class="form-control" id="hourly-property-name" placeholder="e.g., 4 Melrose Apartments">
                                    <div class="form-text">Will appear on PDF reports</div>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="hourly-property-address" class="form-label">Property Address (Optional):</label>
                                    <input type="text" class="form-control" id="hourly-property-address" placeholder="e.g., St Helier">
                                    <div class="form-text">Will appear on PDF reports</div>
                                </div>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Google Ads Performance</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Google Ads Creative Performance</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Mailchimp Performance</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>GSC & GA4 Keywords</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Top Pages Report</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Audience Management</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Audience Statistics</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>User Behavior Analysis</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Conversion Funnel Analysis</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Bounce Rate Analysis</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Device & Geographic Analysis</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Technical Performance</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>User Behavior Analysis</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Content Performance</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>SEO Analysis</h5>
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
                </div>
            </div>

            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5><i class="fab fa-facebook-f"></i> <i class="fab fa-instagram"></i> <i class="fab fa-twitter"></i> Social Media Analytics</h5>
                    </div>
                    <div class="card-body">
                        <p>Discover optimal posting hours for social media platforms by analyzing specific page traffic</p>
                        <form id="social-media-form" class="mb-3">
                            <div class="mb-3">
                                <label for="social-page-url" class="form-label">Page URL or Path:</label>
                                <div class="input-group">
                                    <input type="text" class="form-control" id="social-page-url" placeholder="/valuations or https://www.ndestates.com/valuations" required>
                                    <button class="btn btn-outline-secondary" type="button" id="load-social-popular-pages">Load Popular Pages</button>
                                </div>
                                <select class="form-select mt-2" id="social-popular-pages-select" style="display: none;">
                                    <option value="">Select a popular page...</option>
                                </select>
                                <div class="form-text">
                                    Enter a page path (e.g., /valuations) or full URL, or load and select from popular pages above
                                </div>
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
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
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
                pageTrafficForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const url = document.getElementById('page-url').value.trim();
                    const days = document.getElementById('analysis-days').value;
                    const propertyName = document.getElementById('property-name').value.trim();
                    const propertyAddress = document.getElementById('property-address').value.trim();

                    if (!url) {
                        alert('Please enter a page URL or path');
                        return;
                    }

                    let scriptArgs = `"${url}" ${days}`;
                    if (propertyName) scriptArgs += ` --property-name "${propertyName}"`;
                    if (propertyAddress) scriptArgs += ` --property-address "${propertyAddress}"`;

                    runScript('page_traffic_analysis.py', scriptArgs);
                });
            }

            // Handle hourly traffic analysis form
            const hourlyTrafficForm = document.getElementById('hourly-traffic-form');
            if (hourlyTrafficForm) {
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

                    let scriptArgs = `"${url}" ${days}`;
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

                    const scriptArgs = `"${url}" ${days}`;
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

                // Make AJAX request
                fetch('run_report.php', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.text())
                .then(data => {
                    if (outputDiv) outputDiv.innerHTML = '<pre>' + data + '</pre>';
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
                .then(response => response.text())
                .then(data => {
                    if (outputDiv) outputDiv.innerHTML = '<pre>' + data + '</pre>';
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

                // Make AJAX request
                fetch('run_report.php', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.text())
                .then(data => {
                    // Check if it's HTML (social media dashboard) or plain text (error)
                    if (data.includes('<html>') || data.includes('<!DOCTYPE html>')) {
                        // It's HTML, open in new window
                        const newWindow = window.open('', '_blank');
                        newWindow.document.write(data);
                        newWindow.document.close();
                        if (outputDiv) outputDiv.innerHTML = '<div class="alert alert-success">Social media analytics opened in new window/tab</div>';
                    } else {
                        // It's plain text, display in output div
                        if (outputDiv) outputDiv.innerHTML = '<pre>' + data + '</pre>';
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
                </div>
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
                    </div>
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
                </div>
            `;
        }
    </script>
</body>
</html>
```