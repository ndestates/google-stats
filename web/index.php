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
        .loading { display: none; }
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
                        <button class="btn btn-primary run-report" data-script="google_ads_performance.py">Run Report</button>
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
                        <h5>Mailchimp Performance</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze Mailchimp campaign performance</p>
                        <div class="btn-group-vertical w-100" role="group">
                            <button class="btn btn-primary run-report mb-1" data-script="mailchimp_performance.py" data-args="--report-type yesterday">Yesterday's Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="mailchimp_performance.py" data-args="--report-type monthly">Monthly Report</button>
                            <button class="btn btn-info run-report mb-1" data-script="mailchimp_performance.py" data-args="--report-type sources">Check Email Sources</button>
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
                            <button class="btn btn-primary run-report mb-1" data-script="gsc_ga_keywords.py" data-args="--days 30">30-Day Report</button>
                            <button class="btn btn-secondary run-report mb-1" data-script="gsc_ga_keywords.py" data-args="--days 7">7-Day Report</button>
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
                        <button class="btn btn-primary run-report" data-script="get_top_pages.py">Run Report</button>
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

            // Handle page traffic analysis form
            const pageTrafficForm = document.getElementById('page-traffic-form');
            if (pageTrafficForm) {
                pageTrafficForm.addEventListener('submit', function(e) {
                    e.preventDefault();
                    const url = document.getElementById('page-url').value.trim();
                    const days = document.getElementById('analysis-days').value;

                    if (!url) {
                        alert('Please enter a page URL or path');
                        return;
                    }

                    const scriptArgs = `"${url}" ${days}`;
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

                    if (!url) {
                        alert('Please enter a page URL or path');
                        return;
                    }

                    const scriptArgs = `"${url}" ${days}`;
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

            // Handle popular pages selection for hourly analysis
            const hourlyPopularPagesSelect = document.getElementById('hourly-popular-pages-select');
            if (hourlyPopularPagesSelect) {
                hourlyPopularPagesSelect.addEventListener('change', function() {
                    const selectedValue = this.value;
                    if (selectedValue) {
                        document.getElementById('hourly-page-url').value = selectedValue;
                    }
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
                    buttons.forEach(btn => btn.disabled = false);
                });
            }
        });
    </script>
</body>
</html>