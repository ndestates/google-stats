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
                            <a class="nav-link" href="#mailchimp"><i class="fas fa-envelope"></i> Mailchimp Performance</a>
                            <a class="nav-link" href="#keywords"><i class="fas fa-search"></i> Keywords Analysis</a>
                            <a class="nav-link" href="#top-pages"><i class="fas fa-chart-line"></i> Top Pages Report</a>
                            <a class="nav-link" href="#audience"><i class="fas fa-users"></i> Audience Management</a>
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
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h5><i class="fas fa-bullhorn"></i> Marketing Tools</h5>
                            <ul>
                                <li><strong>Google Ads Performance</strong> - Campaign effectiveness</li>
                                <li><strong>Mailchimp Performance</strong> - Email marketing analytics</li>
                                <li><strong>Audience Management</strong> - GA4 audience creation</li>
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