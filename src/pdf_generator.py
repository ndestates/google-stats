"""
PDF Report Generator Module
Handles PDF generation for various analytics reports
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from src.config import REPORTS_DIR, PROPERTY_NAME, PROPERTY_ADDRESS, get_company_logo_path

def add_logo_to_story(story, logo_path=None):
    """Add logo to the PDF story if logo file exists"""
    # If logo_path is provided for backward compatibility, use it
    # Otherwise, get the stored company logo
    if logo_path is None:
        logo_path = get_company_logo_path()

    if logo_path and os.path.exists(logo_path):
        try:
            # Create logo image (max width 200px, maintain aspect ratio)
            logo = Image(logo_path, width=150, height=75)  # Adjust size as needed
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 15))
        except Exception as e:
            # If logo fails to load, just continue without it
            print(f"Warning: Could not load logo {logo_path}: {e}")
            pass

def get_pdf_filename(base_name, date_info):
    """Generate PDF filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if isinstance(date_info, str) and "_to_" in date_info:
        # Date range format
        filename = f"{base_name}_{date_info}_{timestamp}.pdf"
    else:
        # Single date format
        filename = f"{base_name}_{date_info}_{timestamp}.pdf"

    return os.path.join(REPORTS_DIR, filename)

# Create styles for table content
def get_table_styles():
    """Get styles for table content with proper text wrapping"""
    styles = getSampleStyleSheet()

    # Style for table cells that need wrapping
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontSize=7,
        leading=8,
        alignment=TA_LEFT,
    )

    # Style for table headers
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontSize=8,
        fontName='Helvetica-Bold',
        alignment=TA_CENTER,
    )

    return cell_style, header_style

def create_wrapped_paragraph(text, style, max_width=None):
    """Create a paragraph that wraps properly"""
    if max_width and len(text) > max_width:
        # Truncate with ellipsis if too long
        text = text[:max_width-3] + "..."
    return Paragraph(text, style)

def create_yesterday_report_pdf(page_data, report_date, total_users, total_pages, avg_users_per_page):
    """Generate PDF for yesterday's page-source report"""

    filename = get_pdf_filename("yesterday_report", report_date)
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"YESTERDAY'S PAGE-SOURCE REPORT ({report_date})", title_style))
    story.append(Spacer(1, 12))

    # Add logo if provided
    add_logo_to_story(story)

    # Property Information (if provided)
    if PROPERTY_NAME or PROPERTY_ADDRESS:
        property_style = ParagraphStyle(
            'PropertyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_CENTER
        )

        property_info = []
        if PROPERTY_NAME:
            property_info.append(f"Property: {PROPERTY_NAME}")
        if PROPERTY_ADDRESS:
            property_info.append(f"Address: {PROPERTY_ADDRESS}")

        story.append(Paragraph(" | ".join(property_info), property_style))
        story.append(Spacer(1, 12))

    # Summary section
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )

    story.append(Paragraph("📊 SUMMARY:", styles['Heading2']))
    story.append(Paragraph(f"Date: {report_date}", summary_style))
    story.append(Paragraph(f"Total Pages: {total_pages:,}", summary_style))
    story.append(Paragraph(f"Total Users Across All Pages: {total_users:,}", summary_style))
    story.append(Paragraph(f"Average Users Per Page: {avg_users_per_page:.1f}", summary_style))
    story.append(Spacer(1, 20))

    # Sort pages by total users
    sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Create table data
    table_data = [['Page', 'Total Users', 'Top Traffic Sources']]

    cell_style, header_style = get_table_styles()

    for page_path, data in sorted_pages[:50]:  # Limit to top 50 pages for PDF readability
        total_page_users = data['total_users']

        # Get top 3 sources
        sorted_sources = sorted(data['sources'], key=lambda x: x['users'], reverse=True)[:3]
        sources_text = []
        for source in sorted_sources:
            percentage = (source['users'] / total_page_users) * 100
            sources_text.append(f"{source['source_medium']}: {source['users']:,} ({percentage:.1f}%)")

        sources_display = " | ".join(sources_text) if sources_text else "No data"

        # Truncate long page paths
        display_path = page_path[:60] + "..." if len(page_path) > 60 else page_path

        table_data.append([
            create_wrapped_paragraph(display_path, cell_style),
            create_wrapped_paragraph(f"{total_page_users:,}", cell_style),
            create_wrapped_paragraph(sources_display, cell_style)
        ])

    # Create table with proper column widths (in points, A4 width is about 595 points)
    col_widths = [200, 80, 250]  # Adjusted for A4 page

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEADING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
    return filename

def create_comprehensive_report_pdf(page_data, start_date, end_date, total_users, total_pages, avg_users_per_page):
    """Generate PDF for comprehensive page-source report"""

    filename = get_pdf_filename("comprehensive_page_source_report", f"{start_date}_to_{end_date}")
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"COMPREHENSIVE PAGE-SOURCE REPORT ({start_date} to {end_date})", title_style))
    story.append(Spacer(1, 12))

    # Add logo if provided
    add_logo_to_story(story)

    # Property Information (if provided)
    if PROPERTY_NAME or PROPERTY_ADDRESS:
        property_style = ParagraphStyle(
            'PropertyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_CENTER
        )

        property_info = []
        if PROPERTY_NAME:
            property_info.append(f"Property: {PROPERTY_NAME}")
        if PROPERTY_ADDRESS:
            property_info.append(f"Address: {PROPERTY_ADDRESS}")

        story.append(Paragraph(" | ".join(property_info), property_style))
        story.append(Spacer(1, 12))

    # Summary section
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )

    story.append(Paragraph("📊 SUMMARY:", styles['Heading2']))
    story.append(Paragraph(f"Date Range: {start_date} to {end_date}", summary_style))
    story.append(Paragraph(f"Total Pages: {total_pages:,}", summary_style))
    story.append(Paragraph(f"Total Users Across All Pages: {total_users:,}", summary_style))
    story.append(Paragraph(f"Average Users Per Page: {avg_users_per_page:.1f}", summary_style))
    story.append(Spacer(1, 20))

    # Sort pages by total users
    sorted_pages = sorted(page_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Create table data - show top 100 pages
    table_data = [['Page', 'Campaign', 'Total Users', 'Top Source']]

    cell_style, header_style = get_table_styles()

    for page_path, data in sorted_pages[:100]:
        total_page_users = data['total_users']
        campaign_name = data.get('campaign', 'Unmapped')

        # Get top source
        top_source = max(data['sources'], key=lambda x: x['users']) if data['sources'] else {'source_medium': 'None', 'users': 0}
        percentage = (top_source['users'] / total_page_users) * 100 if total_page_users > 0 else 0
        top_source_display = f"{top_source['source_medium']}: {top_source['users']:,} ({percentage:.1f}%)"

        # Truncate long page paths
        display_path = page_path[:50] + "..." if len(page_path) > 50 else page_path

        # Truncate campaign name if too long
        display_campaign = campaign_name[:25] + "..." if len(campaign_name) > 25 else campaign_name

        table_data.append([
            create_wrapped_paragraph(display_path, cell_style),
            create_wrapped_paragraph(display_campaign, cell_style),
            create_wrapped_paragraph(f"{total_page_users:,}", cell_style),
            create_wrapped_paragraph(top_source_display, cell_style)
        ])

    # Create table with proper column widths (in points, A4 width is about 595 points)
    col_widths = [150, 100, 70, 200]  # Adjusted for A4 page with campaign column

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEADING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
    return filename

def create_channel_report_pdf(channel_data, date_range, total_users, total_sessions):
    """Generate PDF for channel performance report"""

    filename = get_pdf_filename("channel_report", date_range)
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"CHANNEL PERFORMANCE REPORT ({date_range})", title_style))
    story.append(Spacer(1, 12))

    # Add logo if provided
    add_logo_to_story(story)

    # Property Information (if provided)
    if PROPERTY_NAME or PROPERTY_ADDRESS:
        property_style = ParagraphStyle(
            'PropertyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_CENTER
        )

        property_info = []
        if PROPERTY_NAME:
            property_info.append(f"Property: {PROPERTY_NAME}")
        if PROPERTY_ADDRESS:
            property_info.append(f"Address: {PROPERTY_ADDRESS}")

        story.append(Paragraph(" | ".join(property_info), property_style))
        story.append(Spacer(1, 12))

    # Summary section
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )

    story.append(Paragraph("📊 SUMMARY:", styles['Heading2']))
    story.append(Paragraph(f"Date Range: {date_range}", summary_style))
    story.append(Paragraph(f"Total Users: {total_users:,}", summary_style))
    story.append(Paragraph(f"Total Sessions: {total_sessions:,}", summary_style))
    story.append(Spacer(1, 20))

    # Create table data
    table_data = [['Channel', 'Users', 'Sessions', 'Bounce Rate', 'Avg Session Duration']]

    cell_style, header_style = get_table_styles()

    for channel, data in channel_data.items():
        table_data.append([
            create_wrapped_paragraph(channel, cell_style),
            create_wrapped_paragraph(f"{data.get('users', 0):,}", cell_style),
            create_wrapped_paragraph(f"{data.get('sessions', 0):,}", cell_style),
            create_wrapped_paragraph(f"{data.get('bounce_rate', 0):.1f}%", cell_style),
            create_wrapped_paragraph(f"{data.get('avg_session_duration', 0):.1f}s", cell_style)
        ])

    # Create table with proper column widths (in points, A4 width is about 595 points)
    col_widths = [150, 80, 80, 80, 120]  # Adjusted for A4 page

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEADING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
    return filename

def create_google_ads_report_pdf(campaign_data, hourly_data, date_range):
    """Generate PDF for Google Ads performance report"""

    filename = get_pdf_filename("google_ads_performance", date_range)
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"GOOGLE ADS PERFORMANCE REPORT ({date_range})", title_style))
    story.append(Spacer(1, 12))

    # Add logo if provided
    add_logo_to_story(story)

    # Property Information (if provided)
    if PROPERTY_NAME or PROPERTY_ADDRESS:
        property_style = ParagraphStyle(
            'PropertyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_CENTER
        )

        property_info = []
        if PROPERTY_NAME:
            property_info.append(f"Property: {PROPERTY_NAME}")
        if PROPERTY_ADDRESS:
            property_info.append(f"Address: {PROPERTY_ADDRESS}")

        story.append(Paragraph(" | ".join(property_info), property_style))
        story.append(Spacer(1, 12))

    # Campaign Performance Section
    if campaign_data:
        story.append(Paragraph("🎯 CAMPAIGN PERFORMANCE:", styles['Heading2']))
        story.append(Spacer(1, 10))

        campaign_table_data = [['Campaign', 'Users', 'Sessions', 'Conversions']]

        cell_style, header_style = get_table_styles()

        for campaign, data in campaign_data.items():
            campaign_table_data.append([
                create_wrapped_paragraph(campaign[:40] + "..." if len(campaign) > 40 else campaign, cell_style),
                create_wrapped_paragraph(f"{data.get('users', 0):,}", cell_style),
                create_wrapped_paragraph(f"{data.get('sessions', 0):,}", cell_style),
                create_wrapped_paragraph(f"{data.get('conversions', 0):,}", cell_style)
            ])

        col_widths = [200, 80, 80, 80]  # Adjusted for A4 page

        campaign_table = Table(campaign_table_data, colWidths=col_widths, repeatRows=1)
        campaign_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('LEADING', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(campaign_table)
        story.append(PageBreak())

    # Hourly Performance Section
    if hourly_data:
        story.append(Paragraph("🕐 HOURLY PERFORMANCE:", styles['Heading2']))
        story.append(Spacer(1, 10))

        hourly_table_data = [['Hour', 'Users', 'Sessions']]

        for hour, data in sorted(hourly_data.items()):
            hourly_table_data.append([
                create_wrapped_paragraph(f"{hour}:00", cell_style),
                create_wrapped_paragraph(f"{data.get('users', 0):,}", cell_style),
                create_wrapped_paragraph(f"{data.get('sessions', 0):,}", cell_style)
            ])

        col_widths = [80, 100, 100]  # Adjusted for A4 page

        hourly_table = Table(hourly_table_data, colWidths=col_widths, repeatRows=1)
        hourly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('LEADING', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        story.append(hourly_table)

    # Build PDF
    doc.build(story)
    return filename

def create_campaign_report_pdf(campaign_data, date_range, total_users, total_campaigns):
    """Generate PDF for campaign performance report"""

    filename = get_pdf_filename("campaign_performance", date_range)
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"CAMPAIGN PERFORMANCE REPORT ({date_range})", title_style))
    story.append(Spacer(1, 12))

    # Add logo if provided
    add_logo_to_story(story)

    # Property Information (if provided)
    if PROPERTY_NAME or PROPERTY_ADDRESS:
        property_style = ParagraphStyle(
            'PropertyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_CENTER
        )

        property_info = []
        if PROPERTY_NAME:
            property_info.append(f"Property: {PROPERTY_NAME}")
        if PROPERTY_ADDRESS:
            property_info.append(f"Address: {PROPERTY_ADDRESS}")

        story.append(Paragraph(" | ".join(property_info), property_style))
        story.append(Spacer(1, 12))

    # Summary section
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )

    story.append(Paragraph("📊 SUMMARY:", styles['Heading2']))
    story.append(Paragraph(f"Date Range: {date_range}", summary_style))
    story.append(Paragraph(f"Total Campaigns: {total_campaigns:,}", summary_style))
    story.append(Paragraph(f"Total Users Across All Campaigns: {total_users:,}", summary_style))
    story.append(Spacer(1, 20))

    # Sort campaigns by total users
    sorted_campaigns = sorted(campaign_data.items(), key=lambda x: x[1]['total_users'], reverse=True)

    # Create table data
    table_data = [['Campaign Name', 'Source/Medium', 'Users', 'Sessions', 'Pageviews']]

    cell_style, header_style = get_table_styles()

    for campaign_name, data in sorted_campaigns[:30]:  # Limit to top 30 campaigns for PDF readability
        table_data.append([
            create_wrapped_paragraph(campaign_name, cell_style),
            create_wrapped_paragraph(data['source_medium'], cell_style),
            create_wrapped_paragraph(f"{data['total_users']:,}", cell_style),
            create_wrapped_paragraph(f"{data['total_sessions']:,}", cell_style),
            create_wrapped_paragraph(f"{data['total_pageviews']:,}", cell_style)
        ])

    # Create table with proper column widths (in points, A4 width is about 595 points)
    col_widths = [150, 120, 70, 70, 80]  # Adjusted for A4 page

    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEADING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(table)

    # Build PDF
    doc.build(story)
    return filename

def create_24hour_campaign_report_pdf(hourly_data, campaign_data, date_info, total_users):
    """Generate PDF for 24-hour campaign performance report"""

    filename = get_pdf_filename("24hour_campaign_performance", date_info)
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=TA_CENTER
    )

    story.append(Paragraph(f"24-HOUR CAMPAIGN PERFORMANCE REPORT ({date_info})", title_style))
    story.append(Spacer(1, 12))

    # Add logo if provided
    add_logo_to_story(story)

    # Property Information (if provided)
    if PROPERTY_NAME or PROPERTY_ADDRESS:
        property_style = ParagraphStyle(
            'PropertyInfo',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=15,
            alignment=TA_CENTER
        )

        property_info = []
        if PROPERTY_NAME:
            property_info.append(f"Property: {PROPERTY_NAME}")
        if PROPERTY_ADDRESS:
            property_info.append(f"Address: {PROPERTY_ADDRESS}")

        story.append(Paragraph(" | ".join(property_info), property_style))
        story.append(Spacer(1, 12))

    # Summary section
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )

    story.append(Paragraph("📊 DAILY SUMMARY:", styles['Heading2']))
    story.append(Paragraph(f"Date: {date_info}", summary_style))
    story.append(Paragraph(f"Total Users Across All Hours: {total_users:,}", summary_style))
    story.append(Paragraph(f"Hours with Data: {len(hourly_data)}", summary_style))
    story.append(Spacer(1, 20))

    # Hourly breakdown table
    story.append(Paragraph("🕐 HOURLY PERFORMANCE BREAKDOWN:", styles['Heading2']))
    story.append(Spacer(1, 10))

    # Create hourly table data
    hourly_table_data = [['Hour', 'Users', 'Sessions', 'Pageviews', 'Top Campaign']]

    cell_style, header_style = get_table_styles()

    for hour in range(24):
        if hour in hourly_data:
            data = hourly_data[hour]
            # Get top campaign for this hour
            top_campaign = ""
            if data['campaigns']:
                sorted_campaigns = sorted(data['campaigns'].items(), key=lambda x: x[1]['users'], reverse=True)
                top_campaign_name = sorted_campaigns[0][0]
                top_campaign = f"{top_campaign_name[:25]}{'...' if len(top_campaign_name) > 25 else ''}"

            hourly_table_data.append([
                create_wrapped_paragraph(f"{hour:02d}:00-{hour+1:02d}:00", cell_style),
                create_wrapped_paragraph(f"{data['total_users']:,}", cell_style),
                create_wrapped_paragraph(f"{data['total_sessions']:,}", cell_style),
                create_wrapped_paragraph(f"{data['total_pageviews']:,}", cell_style),
                create_wrapped_paragraph(top_campaign, cell_style)
            ])
        else:
            hourly_table_data.append([
                create_wrapped_paragraph(f"{hour:02d}:00-{hour+1:02d}:00", cell_style),
                create_wrapped_paragraph("0", cell_style),
                create_wrapped_paragraph("0", cell_style),
                create_wrapped_paragraph("0", cell_style),
                create_wrapped_paragraph("-", cell_style)
            ])

    # Create table with proper column widths
    col_widths = [80, 60, 60, 70, 150]

    hourly_table = Table(hourly_table_data, colWidths=col_widths, repeatRows=1)

    # Style the table
    hourly_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEADING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(hourly_table)
    story.append(Spacer(1, 20))

    # Top campaigns section
    story.append(Paragraph("📧 TOP CAMPAIGNS OVERALL:", styles['Heading2']))
    story.append(Spacer(1, 10))

    # Sort campaigns by total users
    sorted_campaigns = sorted(campaign_data.items(), key=lambda x: x[1]['total_users'], reverse=True)[:10]

    # Create campaign table data
    campaign_table_data = [['Campaign Name', 'Source/Medium', 'Total Users', 'Hours Active']]

    for campaign_name, data in sorted_campaigns:
        hours_active = len(data['hourly_breakdown'])
        campaign_table_data.append([
            create_wrapped_paragraph(campaign_name, cell_style),
            create_wrapped_paragraph(data['source_medium'], cell_style),
            create_wrapped_paragraph(f"{data['total_users']:,}", cell_style),
            create_wrapped_paragraph(str(hours_active), cell_style)
        ])

    # Create table with proper column widths
    campaign_col_widths = [180, 120, 70, 70]

    campaign_table = Table(campaign_table_data, colWidths=campaign_col_widths, repeatRows=1)

    # Style the table
    campaign_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('LEADING', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(campaign_table)

    # Build PDF
    doc.build(story)
    return filename
