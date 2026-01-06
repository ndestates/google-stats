#!/usr/bin/env python3
"""
Google Stats Web Application
Flask web interface for running analytics reports
"""

import os
import sys
import subprocess
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime, timedelta
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

app = Flask(__name__)
app.secret_key = 'google-stats-secret-key'

# Configuration
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), 'scripts')

# Available reports
REPORTS = {
    'yesterday_report': {
        'name': 'Yesterday Report',
        'description': 'Comprehensive daily page-source analytics',
        'script': 'yesterday_report.py',
        'icon': '📊'
    },
    'campaign_performance': {
        'name': 'Campaign Performance',
        'description': 'UTM campaign tracking and performance analysis',
        'script': 'campaign_performance.py',
        'icon': '🎯'
    },
    'gsc_ga_keywords': {
        'name': 'GSC-GA4 Keywords',
        'description': 'Combined GSC and GA4 keyword performance analysis',
        'script': 'gsc_ga_keywords.py',
        'icon': '🔍'
    },
    'page_traffic_analysis': {
        'name': 'Page Traffic Analysis',
        'description': 'URL-specific traffic source analysis',
        'script': 'page_traffic_analysis.py',
        'icon': '🌐'
    },
    'google_ads_ad_performance': {
        'name': 'Google Ads Creative Performance',
        'description': 'Individual Google Ads creative performance analysis',
        'script': 'google_ads_ad_performance.py',
        'icon': '📢'
    },
    'social_media_timing': {
        'name': 'Social Media Timing Analysis',
        'description': 'Best posting times for social media platforms based on organic traffic',
        'script': 'social_media_timing.py',
        'icon': '⏰'
    }
}

def run_script(script_name, *args):
    """Run a Python script and capture output"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    cmd = [sys.executable, script_path] + list(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=os.path.dirname(__file__)
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Script execution timed out after 5 minutes',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Error running script: {str(e)}',
            'returncode': -1
        }

def get_recent_reports():
    """Get list of recent CSV and PDF reports"""
    if not os.path.exists(REPORTS_DIR):
        return []

    reports = []
    for file in os.listdir(REPORTS_DIR):
        if file.endswith(('.csv', '.pdf')):
            filepath = os.path.join(REPORTS_DIR, file)
            mtime = os.path.getmtime(filepath)
            file_type = 'PDF' if file.endswith('.pdf') else 'CSV'
            reports.append({
                'filename': file,
                'path': filepath,
                'modified': datetime.fromtimestamp(mtime),
                'size': os.path.getsize(filepath),
                'type': file_type
            })

    # Sort by modification time, newest first
    reports.sort(key=lambda x: x['modified'], reverse=True)
    return reports[:20]  # Return top 20 most recent

def parse_csv_preview(filepath, max_rows=10):
    """Parse CSV file and return preview data"""
    try:
        df = pd.read_csv(filepath, nrows=max_rows)
        return {
            'columns': df.columns.tolist(),
            'data': df.to_dict('records'),
            'total_rows': len(df),
            'preview_rows': len(df)
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def index():
    """Homepage with available reports"""
    recent_reports = get_recent_reports()
    return render_template('index.html', reports=REPORTS, recent_reports=recent_reports)

@app.route('/run/<report_id>', methods=['GET', 'POST'])
def run_report(report_id):
    """Run a specific report"""
    if report_id not in REPORTS:
        flash('Report not found', 'error')
        return redirect(url_for('index'))

    report = REPORTS[report_id]

    if request.method == 'POST':
        # Run the script
        flash(f'Running {report["name"]}...', 'info')

        # Handle different report types and their parameters
        args = []
        if report_id == 'page_traffic_analysis':
            url = request.form.get('url')
            if not url:
                flash('A URL is required for Page Traffic Analysis.', 'error')
                return render_template('run_report.html', report=report, report_id=report_id)
            args = ['--url', url]
        elif report_id in ['yesterday_report', 'campaign_performance', 'gsc_ga_keywords', 'google_ads_ad_performance']:
            # These scripts have interactive prompts, so we'll run them directly
            pass

        result = run_script(report['script'], *args)

        if result['success']:
            flash(f'{report["name"]} completed successfully!', 'success')
            # Refresh recent reports
            recent_reports = get_recent_reports()
            return render_template('result.html',
                                 report=report,
                                 report_id=report_id,
                                 result=result,
                                 recent_reports=recent_reports)
        else:
            flash(f'{report["name"]} failed: {result["stderr"]}', 'error')
            return render_template('result.html',
                                 report=report,
                                 report_id=report_id,
                                 result=result,
                                 recent_reports=get_recent_reports())

    # GET request - show form
    return render_template('run_report.html', report=report, report_id=report_id)

@app.route('/reports')
def list_reports():
    """List all available reports"""
    reports = get_recent_reports()
    return render_template('reports.html', reports=reports)

@app.route('/report/<filename>')
def view_report(filename):
    """View a specific CSV report"""
    filepath = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(filepath):
        flash('Report file not found', 'error')
        return redirect(url_for('list_reports'))

    preview = parse_csv_preview(filepath, max_rows=100)

    if 'error' in preview:
        flash(f'Error reading report: {preview["error"]}', 'error')
        return redirect(url_for('list_reports'))

    return render_template('view_report.html',
                         filename=filename,
                         preview=preview)


@app.route('/download/<path:filename>')
def download_file(filename):
    """Download a report file with simple path safety checks"""
    try:
        reports_dir = os.path.abspath(REPORTS_DIR)
        file_path = os.path.abspath(os.path.join(REPORTS_DIR, filename))

        # Ensure the requested file stays within the reports directory
        if not file_path.startswith(reports_dir):
            flash('Access denied', 'error')
            return redirect(url_for('list_reports'))

        if not os.path.exists(file_path):
            flash('File not found', 'error')
            return redirect(url_for('list_reports'))

        if filename.lower().endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename.lower().endswith('.csv'):
            mimetype = 'text/csv'
        else:
            mimetype = 'application/octet-stream'

        return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('list_reports'))

@app.route('/api/run/<report_id>', methods=['POST'])
def api_run_report(report_id):
    """API endpoint to run reports"""
    if report_id not in REPORTS:
        return jsonify({'error': 'Report not found'}), 404

    result = run_script(REPORTS[report_id]['script'])

    return jsonify({
        'success': result['success'],
        'stdout': result['stdout'],
        'stderr': result['stderr'],
        'returncode': result['returncode']
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'reports_dir': os.path.exists(REPORTS_DIR),
        'scripts_dir': os.path.exists(SCRIPTS_DIR)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)