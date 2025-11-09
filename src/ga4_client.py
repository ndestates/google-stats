"""
Google Analytics 4 Client Module
Shared functions for GA4 API interactions
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
)

from .config import get_ga4_client, GA4_PROPERTY_ID, REPORTS_DIR

def create_date_range(start_date: str, end_date: str) -> DateRange:
    """Create a DateRange object"""
    return DateRange(start_date=start_date, end_date=end_date)

def create_dimensions(dimension_names: List[str]) -> List[Dimension]:
    """Create Dimension objects from names"""
    return [Dimension(name=name) for name in dimension_names]

def create_metrics(metric_names: List[str]) -> List[Metric]:
    """Create Metric objects from names"""
    return [Metric(name=name) for name in metric_names]

def run_report(dimensions: List[str], metrics: List[str], date_ranges: List[DateRange],
               order_bys: List[OrderBy] = None, limit: int = 10000, 
               dimension_filter: Any = None) -> Any:
    """
    Run a GA4 report with the given parameters

    Args:
        dimensions: List of dimension names
        metrics: List of metric names
        date_ranges: List of DateRange objects
        order_bys: Optional list of OrderBy objects
        limit: Maximum number of rows to return
        dimension_filter: Optional FilterExpression for filtering dimensions

    Returns:
        GA4 RunReportResponse
    """
    client = get_ga4_client()

    request_params = {
        "property": f"properties/{GA4_PROPERTY_ID}",
        "dimensions": create_dimensions(dimensions),
        "metrics": create_metrics(metrics),
        "date_ranges": date_ranges,
        "order_bys": order_bys or [],
        "limit": limit,
    }
    
    if dimension_filter:
        request_params["dimension_filter"] = dimension_filter

    request = RunReportRequest(**request_params)

    return client.run_report(request)

def get_yesterday_date() -> str:
    """Get yesterday's date as string"""
    yesterday = datetime.now().date() - timedelta(days=1)
    return str(yesterday)

def get_last_30_days_range():
    """Get date range for last 30 days"""
    end_date = datetime.now().date() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=29)  # 30 days total
    return str(start_date), str(end_date)

def ensure_reports_dir():
    """Ensure the reports directory exists"""
    os.makedirs(REPORTS_DIR, exist_ok=True)

def get_report_filename(base_name: str, date_suffix: str = None) -> str:
    """Generate a report filename with optional date suffix"""
    if date_suffix:
        filename = f"{base_name}_{date_suffix}.csv"
    else:
        filename = f"{base_name}.csv"
    return os.path.join(REPORTS_DIR, filename)