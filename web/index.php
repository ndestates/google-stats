<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Analytics Reports</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .report-card { margin-bottom: 20px; }
        .output { background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; }
        .loading { display: none; }
    </style>
</head>
<body>
    <div class="container mt-5">
        <h1 class="mb-4">Google Analytics Reports</h1>

        <div class="row">
            <div class="col-md-6">
                <div class="card report-card">
                    <div class="card-header">
                        <h5>Page Traffic Analysis</h5>
                    </div>
                    <div class="card-body">
                        <p>Analyze page traffic and performance metrics</p>
                        <button class="btn btn-primary run-report" data-script="page_traffic_analysis.py">Run Report</button>
                        <div class="loading mt-2" id="loading-page_traffic_analysis">
                            <div class="spinner-border spinner-border-sm" role="status"></div>
                            Running report...
                        </div>
                        <div class="output" id="output-page_traffic_analysis"></div>
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
            const runButtons = document.querySelectorAll('.run-report');

            runButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const scriptName = this.getAttribute('data-script');
                    const scriptArgs = this.getAttribute('data-args') || '';
                    const scriptBaseName = scriptName.replace('.py', '');
                    const loadingDiv = document.getElementById('loading-' + scriptBaseName);
                    const outputDiv = document.getElementById('output-' + scriptBaseName);

                    // Show loading
                    loadingDiv.style.display = 'block';
                    outputDiv.innerHTML = '';
                    this.disabled = true;

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
                        outputDiv.innerHTML = '<pre>' + data + '</pre>';
                    })
                    .catch(error => {
                        outputDiv.innerHTML = '<div class="alert alert-danger">Error: ' + error.message + '</div>';
                    })
                    .finally(() => {
                        loadingDiv.style.display = 'none';
                        this.disabled = false;
                    });
                });
            });
        });
    </script>
</body>
</html>