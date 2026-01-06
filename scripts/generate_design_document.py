import os
import sys
from datetime import datetime
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image, ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer

# Ensure repository root is on sys.path so src imports resolve
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(CURRENT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from src.config import REPORTS_DIR, get_company_logo_path


TITLE = "ND Estates Marketing Analytics Platform"
SUBTITLE = "Design and Operations Overview"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitle",
            parent=styles["Heading2"],
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            alignment=TA_LEFT,
            spaceBefore=12,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyTextSmall",
            parent=styles["BodyText"],
            fontSize=10,
            leading=13,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    return styles


def _add_logo(story, styles):
    logo_path = "/home/nickd/projects/google-stats/assets/logo/01_nde.svg"
    if not logo_path or not os.path.exists(logo_path):
        return
    try:
        logo = Image(logo_path, width=2.6 * inch, height=1.0 * inch)
        logo.hAlign = "CENTER"
        story.append(logo)
        story.append(Spacer(1, 12))
    except Exception as exc:  # pragma: no cover - visual only
        print(f"Logo could not be added: {exc}")


def _bullets(items, styles):
    return ListFlowable(
        [ListItem(Paragraph(text, styles["BodyTextSmall"]), leftIndent=12) for text in items],
        bulletType="bullet",
        start="-",
        leftIndent=0,
        spaceBefore=0,
        spaceAfter=10,
    )


def _paragraph(story, text, styles):
    story.append(Paragraph(text, styles["BodyTextSmall"]))


def build_design_document():
    styles = _styles()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    filename = os.path.join(
        REPORTS_DIR,
        f"design_document_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf",
    )

    story = []

    # Title block
    _add_logo(story, styles)
    story.append(Paragraph(TITLE, styles["TitleCenter"]))
    story.append(Paragraph(SUBTITLE, styles["SubTitle"]))
    story.append(Paragraph(f"Generated: {now_str}", styles["Caption"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("8b Spectrum, Gloucester Street, St Helier, Jersey, Channel Islands, GB", styles["Caption"]))
    story.append(Paragraph("ND Estates is a registered business name of ND Holdings Limited, Jersey Registered Company No 103135", styles["Caption"]))
    story.append(Spacer(1, 18))

    # Purpose and scope
    story.append(Paragraph("1. Purpose and Scope", styles["Section"]))
    _paragraph(
        story,
        "This document summarizes the current design of the marketing analytics platform, including data sources, processing components, integrations, and operational practices for ND Estates.",
        styles,
    )

    # System overview
    story.append(Paragraph("2. System Overview", styles["Section"]))
    _paragraph(
        story,
        "The platform ingests analytics and marketing data, normalizes it, and produces CSV and PDF outputs that can be launched via scripts, a PHP interface, or the optional Flask app.",
        styles,
    )
    story.append(
        _bullets(
            [
                "Data sources: GA4 (primary), Google Ads, Google Search Console.",
                "Core modules: src/config.py, src/ga4_client.py, src/pdf_generator.py, logging_control.py.",
                "Interfaces: scripts/ for one-off and scheduled runs, web/ PHP UI for report execution, app.py Flask alternative.",
                "Outputs: CSVs in reports/ (date-stamped), PDFs generated via reportlab for summaries and ad-hoc docs.",
            ],
            styles,
        )
    )

    # Architecture
    story.append(Paragraph("3. Architecture", styles["Section"]))
    _paragraph(
        story,
        "Modular Python layer orchestrates API clients and processing; web layer triggers scripts through subprocess calls; storage is file-based (CSVs, PDFs, logs).",
        styles,
    )
    story.append(
        _bullets(
            [
                "Config and secrets: .env plus .ddev/keys/ for service accounts; src/config.py centralizes access.",
                "Execution: DDEV containers recommended; Docker Compose fallback; direct Python execution supported for diagnostics.",
                "Persistence: reports/ for artifacts; logs/ for operational logs; web/uploads/ for assets and settings (logo, defaults).",
                "Extensibility: new scripts follow the shared GA4 pattern (create_date_range, run_report, pandas post-processing).",
            ],
            styles,
        )
    )

    # Data flows
    story.append(Paragraph("4. Data Flows", styles["Section"]))
    story.append(
        _bullets(
            [
                "Ingress: GA4 Data API for traffic metrics; Google Ads API for campaigns and performance; GSC for search data.",
                "Processing: scripts/ modules normalize rows into pandas DataFrames, apply date filters, and compute rollups.",
                "Outputs: CSVs saved to reports/ using naming convention &lt;report&gt;_&lt;start&gt;_to_&lt;end&gt;.csv; PDFs via src/pdf_generator.py for selected summaries.",
                "Orchestration: PHP web UI and app.py invoke Python scripts; tests/run_tests.py covers unit, integration, and script harnesses.",
            ],
            styles,
        )
    )

    # Integrations
    story.append(Paragraph("5. Integrations and Access", styles["Section"]))
    story.append(
        _bullets(
            [
                "Google Ads: service account flow using developer token, login-customer-id, and target customer id; OAuth refresh tokens supported for manual flows.",
                "GA4: service account key (GA4_KEY_PATH) with property id (GA4_PROPERTY_ID).",
                "GSC: service account key (GSC_KEY_PATH) with site URL binding.",
                "Mailchimp API configured in separate mailchimp project.",
                "Logging: logs/&lt;script&gt;.log plus centralized controls via logging_control.py.",
            ],
            styles,
        )
    )

    # Security
    story.append(Paragraph("6. Security and Compliance", styles["Section"]))
    story.append(
        _bullets(
            [
                "No secrets in source control; .env is gitignored; keys stored in .ddev/keys/.",
                "Least-privilege for service accounts; remove unused permissions in Google Ads and GA4.",
                "PII avoidance: only aggregate analytics metrics are stored; no user-level identifiers in reports.",
                "Rotate OAuth tokens and service account keys on a regular cadence; update .env and settings.json paths accordingly.",
            ],
            styles,
        )
    )

    # Operations
    story.append(Paragraph("7. Operations and Deployment", styles["Section"]))
    story.append(
        _bullets(
            [
                "Preferred runtime: ddev start then ddev exec python3 &lt;script&gt;.",
                "Alternative: docker-compose exec google-stats python3 &lt;script&gt;.",
                "Direct host execution possible when Python deps are installed (see requirements.txt).",
                "Tests: python run_tests.py for full suite; python run_tests.py --script &lt;name&gt; for targeted checks.",
            ],
            styles,
        )
    )

    # Reporting and PDFs
    story.append(Paragraph("8. Reporting and PDFs", styles["Section"]))
    story.append(
        _bullets(
            [
                "CSV outputs live in reports/ with date-stamped filenames; downstream tools can pick them up for BI pipelines.",
                "PDFs are generated with reportlab via src/pdf_generator.py; logo is loaded from web/uploads/settings.json using get_company_logo_path().",
                "New PDFs can be added by extending src/pdf_generator.py or by creating task-specific generators (as in this document).",
                "Branding assets reside under web/uploads/logos/ and are referenced via settings.json for consistency across web and scripts.",
            ],
            styles,
        )
    )

    # Risks and mitigations
    story.append(Paragraph("9. Risks and Mitigations", styles["Section"]))
    story.append(
        _bullets(
            [
                "Credential expiry or missing permissions: maintain runbooks for renewing developer tokens and service account access; validate with test_google_ads_connection.py.",
                "API quota changes: monitor Google Ads and GA4 quotas; back off or batch requests in scripts that make high-volume calls.",
                "Schema drift: pin API versions where possible; add integration tests in tests/ when changing dimensions or metrics.",
                "Operational drift: document new scripts in TODO files and README; keep settings.json in sync with uploaded assets.",
            ],
            styles,
        )
    )

    # Next steps
    story.append(Paragraph("10. Suggested Next Steps", styles["Section"]))
    story.append(
        _bullets(
            [
                "Add scheduled runs (cron or DDEV task) for key reports and store artifacts with retention policy.",
                "Expand PDF coverage to include Google Ads performance and blended channel summaries.",
                "Integrate alerting on failed runs using log scanning or exit codes surfaced to the PHP UI.",
                "Publish a lightweight onboarding guide linking credential setup, run commands, and troubleshooting.",
            ],
            styles,
        )
    )

    story.append(PageBreak())
    story.append(Paragraph("Appendix: Key Paths and Commands", styles["Section"]))
    story.append(
        _bullets(
            [
                "Scripts: scripts/ (run via ddev exec python3 scripts/<name>.py).",
                "Config: src/config.py; settings.json at web/uploads/settings.json stores logo path.",
                "Logs: logs/ directory; control via logging_control.py.",
                "Tests: python run_tests.py [unit|integration|--script <name>].",
                "Outputs: reports/ for CSV and PDF artifacts.",
            ],
            styles,
        )
    )

    doc = SimpleDocTemplate(filename, pagesize=A4)
    doc.build(story)
    return filename


if __name__ == "__main__":
    output_file = build_design_document()
    print(f"Design document generated: {output_file}")
