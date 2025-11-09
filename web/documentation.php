<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Analytics Documentation</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .doc-section { margin-bottom: 2rem; }
        .code-block { background-color: #f8f9fa; padding: 1rem; border-radius: 5px; border-left: 4px solid #007bff; }
        .metric-badge { background-color: #e9ecef; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.875rem; margin: 0.125rem; }
        .tool-card { border: 1px solid #dee2e6; border-radius: 0.5rem; margin-bottom: 1rem; }
        .tool-header { background-color: #f8f9fa; padding: 1rem; border-bottom: 1px solid #dee2e6; border-radius: 0.5rem 0.5rem 0 0; }
        .tool-body { padding: 1rem; }
        .nav-link { color: #007bff !important; }
        .nav-link:hover { color: #0056b3 !important; }
    </style>
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <!-- Sidebar Navigation -->
            <div class="col-md-3">
                <div class="card sticky-top" style="top: 20px;">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-book"></i> Documentation</h5>
                    </div>
                    <div class="card-body">
                        <nav class="nav flex-column">
                            <a class="nav-link" href="#overview"><i class="fas fa-home"></i> Overview</a>
                            <a class="nav-link" href="#getting-started"><i class="fas fa-play"></i> Getting Started</a>
                            <a class="nav-link" href="#web-interface"><i class="fas fa-globe"></i> Web Interface</a>
                            <a class="nav-link" href="#hourly-analysis"><i class="fas fa-clock"></i> Hourly Traffic Analysis</a>
                            <a class="nav-link" href="#page-analysis"><i class="fas fa-file-alt"></i> Page Traffic Analysis</a>
                            <a class="nav-link" href="#google-ads"><i class="fas fa-ad"></i> Google Ads Performance</a>
                            <a class="nav-link" href="#google-ads-creative"><i class="fas fa-bullseye"></i> Google Ads Creative Performance</a>
                            <a class="nav-link" href="#mailchimp"><i class="fas fa-envelope"></i> Mailchimp Performance</a>
                            <a class="nav-link" href="#keywords"><i class="fas fa-search"></i> Keywords Analysis</a>
                            <a class="nav-link" href="#top-pages"><i class="fas fa-chart-line"></i> Top Pages Report</a>
                            <a class="nav-link" href="#audience"><i class="fas fa-users"></i> Audience Management</a>
                            <a class="nav-link" href="#audience-stats"><i class="fas fa-users-cog"></i> Audience Statistics</a>
                            <a class="nav-link" href="#conversion-funnel"><i class="fas fa-filter"></i> Conversion Funnel</a>
                            <a class="nav-link" href="#bounce-rate"><i class="fas fa-door-open"></i> Bounce Rate Analysis</a>
                            <a class="nav-link" href="#device-geo"><i class="fas fa-mobile-alt"></i> Device & Geo Analysis</a>
                            <a class="nav-link" href="#technical-performance"><i class="fas fa-cogs"></i> Technical Performance</a>
                            <a class="nav-link" href="#user-behavior"><i class="fas fa-route"></i> User Behavior</a>
                            <a class="nav-link" href="#content-performance"><i class="fas fa-file-alt"></i> Content Performance</a>
                            <a class="nav-link" href="#seo-analysis"><i class="fas fa-search"></i> SEO Analysis</a>
                            <a class="nav-link" href="#command-line"><i class="fas fa-terminal"></i> Command Line Usage</a>
                            <a class="nav-link" href="#data-export"><i class="fas fa-download"></i> Data Export</a>
                            <a class="nav-link" href="#api-reference"><i class="fas fa-code"></i> API Reference</a>
                        </nav>
                    </div>
                </div>
            </div>

            <!-- Main Content -->
            <div class="col-md-9">
                <!-- Header -->
                <div class="doc-section">
                    <h1 class="display-4"><i class="fas fa-chart-bar text-primary"></i> Google Analytics Platform</h1>
                    <p class="lead">Comprehensive analytics tools for Google Analytics 4, Google Ads, Mailchimp, and Google Search Console data.</p>
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> <strong>Version:</strong> 2.0 | <strong>Last Updated:</strong> November 7, 2025
                    </div>
                </div>

                <!-- Overview -->
                <div id="overview" class="doc-section">
                    <h2><i class="fas fa-home"></i> Overview</h2>
                    <p>This analytics platform provides comprehensive insights into your website and marketing performance across multiple channels:</p>
                    <div class="row">
                        <div class="col-md-6">
                            <h5><i class="fas fa-chart-line"></i> Analytics Tools</h5>
                            <ul>
                                <li><strong>Hourly Traffic Analysis</strong> - Time-of-day traffic patterns</li>
                                <li><strong>Page Traffic Analysis</strong> - Individual page performance</li>
                                <li><strong>Top Pages Report</strong> - Best performing content</li>
                                <li><strong>Keywords Analysis</strong> - Search performance insights</li>
                                <li><strong>Conversion Funnel</strong> - User conversion paths</li>
                                <li><strong>Bounce Rate Analysis</strong> - Exit page optimization</li>
                                <li><strong>Device & Geo Analysis</strong> - Platform and location insights</li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h5><i class="fas fa-bullhorn"></i> Marketing & Technical Tools</h5>
                            <ul>
                                <li><strong>Google Ads Performance</strong> - Campaign effectiveness</li>
                                <li><strong>Google Ads Creative Performance</strong> - Individual ad creative analysis</li>
                                <li><strong>Mailchimp Performance</strong> - Email marketing analytics</li>
                                <li><strong>Audience Management</strong> - GA4 audience creation</li>
                                <li><strong>Audience Statistics</strong> - GA4 audience performance metrics</li>
                                <li><strong>Technical Performance</strong> - Site performance analysis</li>
                                <li><strong>User Behavior Analysis</strong> - Navigation patterns</li>
                                <li><strong>Content Performance</strong> - Content engagement metrics</li>
                                <li><strong>SEO Analysis</strong> - Search optimization insights</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Getting Started -->
                <div id="getting-started" class="doc-section">
                    <h2><i class="fas fa-play"></i> Getting Started</h2>
                    <div class="alert alert-success">
                        <h5><i class="fas fa-check-circle"></i> Prerequisites</h5>
                        <ul class="mb-0">
                            <li>DDEV environment configured</li>
                            <li>Google Analytics 4 property access</li>
                            <li>Google Ads API credentials (optional)</li>
                            <li>Mailchimp API key (optional)</li>
                        </ul>
                    </div>

                    <h5>Quick Start</h5>
                    <ol>
                        <li>Start DDEV: <code>ddev start</code></li>
                        <li>Access the web interface: <code>https://google-stats.ddev.site</code></li>
                        <li>Run your first analysis using the web forms</li>
                        <li>Download CSV reports from the <code>reports/</code> directory</li>
                    </ol>
                </div>

                <!-- Web Interface -->
                <div id="web-interface" class="doc-section">
                    <h2><i class="fas fa-globe"></i> Web Interface</h2>
                    <p>The web interface provides an easy-to-use dashboard for running all analytics reports without command line knowledge.</p>

                    <h5>Features</h5>
                    <ul>
                        <li><strong>Interactive Forms</strong> - Point-and-click report generation</li>
                        <li><strong>Popular Pages</strong> - Quick access to high-traffic pages</li>
                        <li><strong>Real-time Output</strong> - Live report generation with progress indicators</li>
                        <li><strong>Secure Execution</strong> - Safe script running with validation</li>
                    </ul>

                    <h5>Navigation</h5>
                    <div class="code-block">
                        <strong>Main Dashboard:</strong> https://google-stats.ddev.site<br>
                        <strong>Documentation:</strong> https://google-stats.ddev.site/documentation.php
                    </div>
                </div>

                <!-- Hourly Traffic Analysis -->
                <div id="hourly-analysis" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-clock"></i> Hourly Traffic Analysis</h3>
                            <p class="mb-0">Analyze traffic patterns by hour of day with comprehensive engagement metrics</p>
                        </div>
                        <div class="tool-body">
                            <h5>Key Metrics</h5>
                            <div class="mb-3">
                                <span class="metric-badge">Users</span>
                                <span class="metric-badge">New Users</span>
                                <span class="metric-badge">Sessions</span>
                                <span class="metric-badge">Engaged Sessions</span>
                                <span class="metric-badge">Pageviews</span>
                                <span class="metric-badge">Engagement Rate</span>
                                <span class="metric-badge">Channel Groupings</span>
                                <span class="metric-badge">Campaigns</span>
                            </div>

                            <h5>Web Usage</h5>
                            <ol>
                                <li>Select "Hourly Traffic Analysis" card</li>
                                <li>Enter page URL or path (e.g., /valuations)</li>
                                <li>Choose time period (7, 30, or 90 days)</li>
                                <li>Click "Load Popular Pages" for suggestions</li>
                                <li>Click "Run Analysis"</li>
                            </ol>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/hourly_traffic_analysis.py /valuations 7</code>
                            </div>

                            <h5>Sample Output</h5>
                            <div class="code-block">
                                <pre>1. Source/Medium: google / cpc
   Total Users: 1,569 (New: 1,098)
   Total Sessions: 1,625 (Engaged: 1,625)
   Best Hour: 18:00 (186 users)
   Channel Groups: Cross-network, Display
   Hourly Traffic:
   Hour | Users | New Users | Sessions | Engaged | Pageviews
   -----|-------|-----------|----------|----------|-----------
    18:00 |   162 |       115 |      164 |      164 |         0</pre>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Page Traffic Analysis -->
                <div id="page-analysis" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-file-alt"></i> Page Traffic Analysis</h3>
                            <p class="mb-0">Detailed traffic analysis for individual pages with source attribution</p>
                        </div>
                        <div class="tool-body">
                            <h5>Key Metrics</h5>
                            <div class="mb-3">
                                <span class="metric-badge">Total Users</span>
                                <span class="metric-badge">Sessions</span>
                                <span class="metric-badge">Pageviews</span>
                                <span class="metric-badge">Avg Session Duration</span>
                                <span class="metric-badge">Bounce Rate</span>
                                <span class="metric-badge">Source/Medium</span>
                                <span class="metric-badge">Campaigns</span>
                            </div>

                            <h5>Web Usage</h5>
                            <ol>
                                <li>Select "Page Traffic Analysis" card</li>
                                <li>Enter page URL or path</li>
                                <li>Choose time period</li>
                                <li>Click "Run Analysis"</li>
                            </ol>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/page_traffic_analysis.py /valuations 30</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Google Ads Performance -->
                <div id="google-ads" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-ad"></i> Google Ads Performance</h3>
                            <p class="mb-0">Comprehensive Google Ads campaign performance analysis</p>
                        </div>
                        <div class="tool-body">
                            <h5>Features</h5>
                            <ul>
                                <li>Campaign-level performance metrics</li>
                                <li>Cost analysis and ROI tracking</li>
                                <li>Conversion tracking</li>
                                <li>Ad group performance</li>
                            </ul>

                            <h5>Web Usage</h5>
                            <p>Click "Run Report" on the Google Ads Performance card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/google_ads_performance.py</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Google Ads Creative Performance -->
                <div id="google-ads-creative" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-bullseye"></i> Google Ads Creative Performance</h3>
                            <p class="mb-0">Individual Google Ads creative performance analysis</p>
                        </div>
                        <div class="tool-body">
                            <h5>Features</h5>
                            <ul>
                                <li>Individual ad creative performance</li>
                                <li>Creative ID analysis</li>
                                <li>Network performance breakdown</li>
                                <li>Top performing creatives identification</li>
                                <li>Campaign and ad group insights</li>
                            </ul>

                            <h5>Web Usage</h5>
                            <p>Click "Run Report" on the Google Ads Creative Performance card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/google_ads_ad_performance.py</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Mailchimp Performance -->
                <div id="mailchimp" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-envelope"></i> Mailchimp Performance</h3>
                            <p class="mb-0">Email marketing campaign analytics and subscriber insights</p>
                        </div>
                        <div class="tool-body">
                            <h5>Report Types</h5>
                            <ul>
                                <li><strong>Yesterday's Report</strong> - Daily email performance</li>
                                <li><strong>Monthly Report</strong> - Monthly campaign summary</li>
                                <li><strong>Email Sources</strong> - Subscriber source analysis</li>
                            </ul>

                            <h5>Web Usage</h5>
                            <p>Select the desired report type from the Mailchimp Performance card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/mailchimp_performance.py --report-type yesterday</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Keywords Analysis -->
                <div id="keywords" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-search"></i> Keywords Analysis</h3>
                            <p class="mb-0">Combined Google Search Console and GA4 keyword performance</p>
                        </div>
                        <div class="tool-body">
                            <h5>Features</h5>
                            <ul>
                                <li>Search query analysis</li>
                                <li>Impressions and clicks tracking</li>
                                <li>Position tracking</li>
                                <li>GA4 landing page correlation</li>
                            </ul>

                            <h5>Web Usage</h5>
                            <p>Choose 30-day or 7-day report from the Keywords Analysis card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/gsc_ga_keywords.py --days 30</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Top Pages Report -->
                <div id="top-pages" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-chart-line"></i> Top Pages Report</h3>
                            <p class="mb-0">Identify your highest-performing content and pages</p>
                        </div>
                        <div class="tool-body">
                            <h5>Web Usage</h5>
                            <p>Click "Run Report" on the Top Pages Report card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/get_top_pages.py</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Audience Management -->
                <div id="audience" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-users"></i> Audience Management</h3>
                            <p class="mb-0">Create and manage Google Analytics 4 audiences</p>
                        </div>
                        <div class="tool-body">
                            <h5>Audience Types</h5>
                            <ul>
                                <li><strong>All Users</strong> - Complete user base</li>
                                <li><strong>Cart Abandoners</strong> - E-commerce abandonment tracking</li>
                                <li><strong>Custom Audiences</strong> - Flexible audience creation</li>
                            </ul>

                            <h5>Web Usage</h5>
                            <p>Select audience type from the Audience Management card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/audience_management.py --action create --type basic --name "All Users"</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Audience Statistics -->
                <div id="audience-stats" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-users-cog"></i> Audience Statistics</h3>
                            <p class="mb-0">Get performance metrics and analytics for all GA4 audiences</p>
                        </div>
                        <div class="tool-body">
                            <h5>Features</h5>
                            <ul>
                                <li>User counts and session metrics for each audience</li>
                                <li>Engagement rates and bounce rate analysis</li>
                                <li>New user percentages</li>
                                <li>Audience portfolio summary</li>
                                <li>Performance insights and recommendations</li>
                                <li>CSV export with detailed metrics</li>
                            </ul>

                            <h5>Web Usage</h5>
                            <p>Select time period from the Audience Statistics card.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/audience_stats.py --days 30</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Conversion Funnel Analysis -->
                <div id="conversion-funnel" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-filter"></i> Conversion Funnel Analysis</h3>
                            <p class="mb-0">Analyze user conversion paths and goal completion rates</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>Funnel Analysis</strong> - User journey through conversion steps</li>
                                <li><strong>Goal Completion</strong> - Track completion rates for key objectives</li>
                                <li><strong>Drop-off Points</strong> - Identify where users abandon the funnel</li>
                                <li><strong>Recommendations</strong> - Actionable optimization suggestions</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Conversion Rate</span>
                                <span class="metric-badge">Funnel Drop-off</span>
                                <span class="metric-badge">Goal Completions</span>
                                <span class="metric-badge">Path Efficiency</span>
                            </div>

                            <h5>Web Usage</h5>
                            <p>Select analysis type from the Conversion Funnel Analysis card options.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/conversion_funnel_analysis.py all 30</code><br>
                                <code>ddev exec python3 scripts/conversion_funnel_analysis.py funnel 7</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Bounce Rate Analysis -->
                <div id="bounce-rate" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-door-open"></i> Bounce Rate Analysis</h3>
                            <p class="mb-0">Identify high-bounce pages and optimization opportunities</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>Page Analysis</strong> - Individual page bounce rates</li>
                                <li><strong>Channel Analysis</strong> - Bounce rates by traffic source</li>
                                <li><strong>Threshold Alerts</strong> - Pages exceeding bounce rate limits</li>
                                <li><strong>Optimization Tips</strong> - Specific improvement recommendations</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Bounce Rate %</span>
                                <span class="metric-badge">Exit Rate %</span>
                                <span class="metric-badge">Session Duration</span>
                                <span class="metric-badge">Page Engagement</span>
                            </div>

                            <h5>Web Usage</h5>
                            <p>Select analysis type from the Bounce Rate Analysis card options.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/bounce_rate_analysis.py all 30</code><br>
                                <code>ddev exec python3 scripts/bounce_rate_analysis.py pages 7</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Device & Geographic Analysis -->
                <div id="device-geo" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-mobile-alt"></i> Device & Geographic Analysis</h3>
                            <p class="mb-0">Analyze performance by device type and geographic location</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>Device Performance</strong> - Desktop, mobile, tablet metrics</li>
                                <li><strong>Geographic Insights</strong> - Country and regional performance</li>
                                <li><strong>Cross-device Comparison</strong> - Performance differences by device</li>
                                <li><strong>Location-based Optimization</strong> - Geographic targeting recommendations</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Device Category</span>
                                <span class="metric-badge">Country</span>
                                <span class="metric-badge">Sessions by Device</span>
                                <span class="metric-badge">Conversion by Location</span>
                            </div>

                            <h5>Web Usage</h5>
                            <p>Select analysis type from the Device & Geographic Analysis card options.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/device_geo_analysis.py all 30</code><br>
                                <code>ddev exec python3 scripts/device_geo_analysis.py device 7</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Technical Performance -->
                <div id="technical-performance" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-cogs"></i> Technical Performance</h3>
                            <p class="mb-0">Analyze technical performance and custom events</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>Load Performance</strong> - Page load times and engagement</li>
                                <li><strong>Custom Events</strong> - Track custom event implementation</li>
                                <li><strong>Error Detection</strong> - Identify JavaScript errors and issues</li>
                                <li><strong>Performance Optimization</strong> - Technical improvement recommendations</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Avg Session Duration</span>
                                <span class="metric-badge">Engagement Rate</span>
                                <span class="metric-badge">Bounce Rate</span>
                                <span class="metric-badge">Event Count</span>
                            </div>

                            <h5>Web Usage</h5>
                            <p>Select analysis type from the Technical Performance card options.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/technical_performance.py all 30</code><br>
                                <code>ddev exec python3 scripts/technical_performance.py load_times 7</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- User Behavior Analysis -->
                <div id="user-behavior" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-route"></i> User Behavior Analysis</h3>
                            <p class="mb-0">Analyze user navigation patterns, engagement, and behavior flows</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>General Behavior Analysis</strong> - Overall site engagement patterns and hourly traffic</li>
                                <li><strong>Property Pages Analysis</strong> - Dedicated analysis of property-related pages with location insights</li>
                                <li><strong>User Flow Analysis</strong> - Page transition patterns from specific starting points</li>
                                <li><strong>Engagement Optimization</strong> - High/low engagement page identification</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Bounce Rate</span>
                                <span class="metric-badge">Session Duration</span>
                                <span class="metric-badge">Page Views/Session</span>
                                <span class="metric-badge">Hourly Traffic</span>
                                <span class="metric-badge">Property Performance</span>
                                <span class="metric-badge">Location Analysis</span>
                            </div>

                            <h5>Web Interface Options</h5>
                            <ul>
                                <li><strong>General Behavior (30 Days)</strong> - Comprehensive site-wide behavior analysis</li>
                                <li><strong>Property Pages Analysis</strong> - Focused analysis of property listings and performance</li>
                                <li><strong>Quick Behavior Check (7 Days)</strong> - Rapid assessment of recent user patterns</li>
                            </ul>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/user_flow_analysis.py behavior 30 100</code><br>
                                <code>ddev exec python3 scripts/user_flow_analysis.py properties 30 50</code><br>
                                <code>ddev exec python3 scripts/user_flow_analysis.py /valuations 5 30</code>
                            </div>

                            <h5>Property Analysis Insights</h5>
                            <p>The property pages analysis provides location-based insights including:</p>
                            <ul>
                                <li>Traffic distribution across Jersey parishes (St Helier, St Saviour, etc.)</li>
                                <li>Property type performance and engagement metrics</li>
                                <li>Average sessions per property by location</li>
                                <li>High/low engagement property identification</li>
                            </ul>
                        </div>
                    </div>
                </div>

                <!-- Content Performance -->
                <div id="content-performance" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-file-alt"></i> Content Performance</h3>
                            <p class="mb-0">Analyze content engagement and effectiveness</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>Content Engagement</strong> - Page-level engagement metrics</li>
                                <li><strong>Content Types</strong> - Performance by content category</li>
                                <li><strong>Content Effectiveness</strong> - Channel-specific content performance</li>
                                <li><strong>Content Optimization</strong> - Improvement recommendations</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Engagement Rate</span>
                                <span class="metric-badge">Avg Session Duration</span>
                                <span class="metric-badge">Bounce Rate</span>
                                <span class="metric-badge">Pageviews</span>
                            </div>

                            <h5>Web Usage</h5>
                            <p>Select analysis type from the Content Performance card options.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/content_performance.py all 30</code><br>
                                <code>ddev exec python3 scripts/content_performance.py engagement 7</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- SEO Analysis -->
                <div id="seo-analysis" class="doc-section">
                    <div class="tool-card">
                        <div class="tool-header">
                            <h3><i class="fas fa-search"></i> SEO Analysis</h3>
                            <p class="mb-0">Analyze search engine optimization performance</p>
                        </div>
                        <div class="tool-body">
                            <h5>Analysis Types</h5>
                            <ul>
                                <li><strong>Organic Traffic</strong> - Organic search performance</li>
                                <li><strong>Keyword Themes</strong> - Content keyword analysis</li>
                                <li><strong>SEO Health</strong> - Technical SEO indicators</li>
                                <li><strong>Search Optimization</strong> - SEO improvement recommendations</li>
                            </ul>

                            <h5>Key Metrics</h5>
                            <div>
                                <span class="metric-badge">Organic Sessions</span>
                                <span class="metric-badge">Organic Users</span>
                                <span class="metric-badge">Bounce Rate</span>
                                <span class="metric-badge">Engagement Rate</span>
                            </div>

                            <h5>Web Usage</h5>
                            <p>Select analysis type from the SEO Analysis card options.</p>

                            <h5>Command Line</h5>
                            <div class="code-block">
                                <code>ddev exec python3 scripts/seo_analysis.py all 30</code><br>
                                <code>ddev exec python3 scripts/seo_analysis.py organic 7</code>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Command Line Usage -->
                <div id="command-line" class="doc-section">
                    <h2><i class="fas fa-terminal"></i> Command Line Usage</h2>
                    <p>All scripts can be run directly from the command line using DDEV.</p>

                    <h5>General Pattern</h5>
                    <div class="code-block">
                        <code>ddev exec python3 scripts/[script_name].py [arguments]</code>
                    </div>

                    <h5>Common Arguments</h5>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Argument</th>
                                <th>Description</th>
                                <th>Example</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>url</code></td>
                                <td>Page URL or path</td>
                                <td><code>/valuations</code></td>
                            </tr>
                            <tr>
                                <td><code>days</code></td>
                                <td>Number of days to analyze</td>
                                <td><code>30</code></td>
                            </tr>
                            <tr>
                                <td><code>--report-type</code></td>
                                <td>Report type for multi-option scripts</td>
                                <td><code>--report-type yesterday</code></td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Data Export -->
                <div id="data-export" class="doc-section">
                    <h2><i class="fas fa-download"></i> Data Export</h2>
                    <p>All reports generate CSV files in the <code>reports/</code> directory for further analysis.</p>

                    <h5>Export Location</h5>
                    <div class="code-block">
                        <code>reports/[report_name]_[parameters]_[date_range].csv</code>
                    </div>

                    <h5>Example Files</h5>
                    <ul>
                        <li><code>hourly_traffic_analysis_valuations_2025-10-31_to_2025-11-06.csv</code></li>
                        <li><code>page_traffic_analysis_valuations_2025-10-31_to_2025-11-06.csv</code></li>
                        <li><code>google_ads_performance_2025-11-06.csv</code></li>
                    </ul>

                    <h5>Accessing Files</h5>
                    <div class="code-block">
                        <code>ddev exec ls reports/</code><br>
                        <code>ddev exec cat reports/filename.csv | head -10</code>
                    </div>
                </div>

                <!-- API Reference -->
                <div id="api-reference" class="doc-section">
                    <h2><i class="fas fa-code"></i> API Reference</h2>
                    <p>Technical details for developers and advanced users.</p>

                    <h5>GA4 Dimensions Used</h5>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Dimension</th>
                                <th>Description</th>
                                <th>Used In</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>pagePath</code></td>
                                <td>Page path in GA4</td>
                                <td>All page analysis scripts</td>
                            </tr>
                            <tr>
                                <td><code>hour</code></td>
                                <td>Hour of day (0-23)</td>
                                <td>Hourly traffic analysis</td>
                            </tr>
                            <tr>
                                <td><code>sessionSourceMedium</code></td>
                                <td>Source and medium combination</td>
                                <td>All traffic analysis</td>
                            </tr>
                            <tr>
                                <td><code>sessionDefaultChannelGrouping</code></td>
                                <td>GA4 channel classification</td>
                                <td>Hourly analysis</td>
                            </tr>
                        </tbody>
                    </table>

                    <h5>GA4 Metrics Used</h5>
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Metric</th>
                                <th>Description</th>
                                <th>Used In</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><code>totalUsers</code></td>
                                <td>Total unique users</td>
                                <td>All scripts</td>
                            </tr>
                            <tr>
                                <td><code>newUsers</code></td>
                                <td>New vs returning users</td>
                                <td>Hourly analysis</td>
                            </tr>
                            <tr>
                                <td><code>engagedSessions</code></td>
                                <td>Sessions with engagement</td>
                                <td>Hourly analysis</td>
                            </tr>
                            <tr>
                                <td><code>engagementRate</code></td>
                                <td>Percentage of engaged sessions</td>
                                <td>Hourly analysis</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- Footer -->
                <div class="doc-section">
                    <hr>
                    <div class="text-center text-muted">
                        <p>&copy; 2025 NDEstates Analytics Platform. Built with Google Analytics 4, Google Ads, and Mailchimp APIs.</p>
                        <p><small>For technical support or feature requests, please contact the development team.</small></p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Smooth scrolling for navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });

        // Highlight active section in navigation
        window.addEventListener('scroll', function() {
            const sections = document.querySelectorAll('.doc-section');
            const navLinks = document.querySelectorAll('.nav-link');

            let current = '';
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                if (pageYOffset >= sectionTop - 60) {
                    current = section.getAttribute('id');
                }
            });

            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {
                    link.classList.add('active');
                }
            });
        });
    </script>
</body>
</html>