#!/usr/bin/env python3
"""
Generate PDF from ARCHITECTURE.md using reportlab only
Simple and lightweight PDF generation with ND Estates branding and logo
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib import colors
from reportlab.pdfgen import canvas

def clean_markdown_formatting(text):
    """Clean up markdown formatting for better PDF display"""
    # Remove bold/italic markers but keep the text
    text = text.replace('**', '').replace('*', '')
    # Handle inline code (keep it but style differently if needed)
    text = text.replace('`', '"')
    # Clean up any double spaces
    text = ' '.join(text.split())
    return text

def generate_pdf_from_markdown():
    """Convert ARCHITECTURE.md to PDF using reportlab"""
    
    # Read the markdown file
    md_path = Path(__file__).parent / "ARCHITECTURE.md"
    
    if not md_path.exists():
        print(f"❌ File not found: {md_path}")
        return 1
    
    print(f"📖 Reading: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Output PDF path
    pdf_path = Path(__file__).parent / "ARCHITECTURE.pdf"
    
    print(f"📝 Generating PDF: {pdf_path}")
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        title="NDE-Stats-GA Architecture & Design Document"
    )
    
    # Build story (content)
    story = []
    styles = getSampleStyleSheet()
    
    # Add custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=12,
        spaceBefore=12,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=6,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    h3_style = ParagraphStyle(
        'H3Style',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#3d6db5'),
        spaceAfter=4,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6,
        alignment=4  # Justify
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        spaceAfter=4,
        leftIndent=20
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
        spaceAfter=6,
        leftIndent=20,
        fontName='Courier',
        textColor=colors.HexColor('#333333'),
        backColor=colors.HexColor('#f5f5f5')
    )
    
    # Add ND Estates logo and branding at the top
    logo_path = Path(__file__).parent / "assets" / "logo" / "stacked-colour.png"
    if logo_path.exists():
        try:
            # Add logo (centered, 1.2 inches wide for better proportion)
            logo = Image(str(logo_path), width=1.2*inch, height=1.2*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.15*inch))
        except Exception as e:
            print(f"⚠️  Could not add logo: {e}")

    # Add ND Estates branding
    brand_style = ParagraphStyle(
        'Brand',
        parent=styles['Normal'],
        fontSize=22,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=4,
        alignment=1,  # Center
        fontName='Helvetica-Bold'
    )
    tagline_style = ParagraphStyle(
        'Tagline',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=15,
        alignment=1,  # Center
        fontName='Helvetica'
    )

    story.append(Paragraph("ND ESTATES", brand_style))
    story.append(Paragraph("Advanced Analytics & Marketing Intelligence", tagline_style))
    story.append(Spacer(1, 0.25*inch))

    # Parse markdown and add to story
    lines = markdown_content.split('\n')
    in_code_block = False
    code_block_lines = []
    in_table = False
    table_data = []
    table_headers = []
    
    for i, line in enumerate(lines):
        # Handle code blocks
        if line.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_lines = []
            else:
                in_code_block = False
                # Add code block
                code_text = '\n'.join(code_block_lines)
                if code_text.strip():
                    story.append(Spacer(1, 0.08*inch))
                    story.append(Paragraph(code_text.replace('<', '&lt;').replace('>', '&gt;'), code_style))
                    story.append(Spacer(1, 0.08*inch))
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # Handle table rows
        if line.startswith('|') and line.endswith('|'):
            if not in_table:
                in_table = True
                table_data = []
                # Check if next line is separator
                if i + 1 < len(lines) and lines[i + 1].startswith('|') and '---' in lines[i + 1]:
                    # This is a header row, skip the separator
                    pass
            # Parse table row
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            table_data.append(cells)
            continue
        elif in_table and line.strip() == '':
            # End of table
            if table_data:
                from reportlab.platypus import Table, TableStyle
                # Calculate flexible column widths based on content and page width
                page_width = A4[0] - 2*inch  # Account for margins
                num_cols = len(table_data[0])
                col_width = page_width / num_cols

                # Create table with flexible widths and word wrapping
                table = Table(table_data, colWidths=[col_width] * num_cols)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('WORDWRAP', (0, 0), (-1, -1), True),  # Enable word wrapping
                ]))
                story.append(Spacer(1, 0.1*inch))
                story.append(table)
                story.append(Spacer(1, 0.15*inch))
            in_table = False
            table_data = []
            continue

        if not line.strip():
            if not in_table:
                story.append(Spacer(1, 0.06*inch))
            continue

        # Headings
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 0.12*inch))
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, h1_style))
            story.append(Spacer(1, 0.08*inch))
        elif line.startswith('### '):
            text = line[4:].strip()
            story.append(Paragraph(text, h2_style))
            story.append(Spacer(1, 0.06*inch))
        elif line.startswith('#### '):
            text = line[5:].strip()
            story.append(Paragraph(text, h3_style))
            story.append(Spacer(1, 0.04*inch))
        elif line.startswith('- ') or line.startswith('* '):
            # Bullet point (support both - and * syntax)
            if line.startswith('- '):
                text = line[2:].strip()
            else:
                text = line[2:].strip()
            # Clean up markdown formatting in bullet points
            text = clean_markdown_formatting(text)
            story.append(Paragraph('• ' + text, bullet_style))
        elif line.startswith('  - ') or line.startswith('  * ') or line.startswith('    - ') or line.startswith('    * '):
            # Nested bullet (support multiple levels and both -/* syntax)
            if '  - ' in line[:4]:
                text = line[4:].strip()
            elif '  * ' in line[:4]:
                text = line[4:].strip()
            elif '    - ' in line[:6]:
                text = line[6:].strip()
            elif '    * ' in line[:6]:
                text = line[6:].strip()
            else:
                text = line.strip()
            text = clean_markdown_formatting(text)
            story.append(Paragraph('◦ ' + text, bullet_style))
        else:
            # Regular paragraph
            if line.strip() and not line.startswith('**') and not in_table:
                # Clean up markdown formatting
                text = clean_markdown_formatting(line.strip())
                if len(text) > 1:
                    story.append(Paragraph(text, normal_style))

    # Build PDF
    try:
        doc.build(story)
        file_size = os.path.getsize(pdf_path) / 1024
        print(f"✅ PDF generated successfully!")
        print(f"📊 File: {pdf_path}")
        print(f"📈 Size: {file_size:.1f} KB")
        return 0
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(generate_pdf_from_markdown())
