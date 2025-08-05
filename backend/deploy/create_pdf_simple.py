#!/usr/bin/env python3
"""
Simple PDF generator for GenHook deployment guide using reportlab
Install with: pip install reportlab
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
import re
from pathlib import Path

def create_deployment_pdf():
    """Create a formatted PDF of the deployment guide"""
    
    # File paths
    script_dir = Path(__file__).parent
    md_file = script_dir / "GenHook_AWS_Deployment_Guide.md"
    pdf_file = script_dir / "GenHook_AWS_Deployment_Guide.pdf"
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        str(pdf_file),
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        spaceBefore=24,
        textColor=colors.HexColor('#2c3e50')
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=20,
        textColor=colors.HexColor('#34495e')
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=16,
        textColor=colors.HexColor('#7f8c8d')
    )
    
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=9,
        fontName='Courier',
        backColor=colors.HexColor('#f8f9fa'),
        borderColor=colors.HexColor('#3498db'),
        borderWidth=1,
        borderPadding=10,
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Build story (content)
    story = []
    
    # Parse markdown and convert to PDF elements
    lines = content.split('\n')
    in_code_block = False
    code_block_content = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Handle code blocks
        if line.startswith('```'):
            if in_code_block:
                # End of code block
                if code_block_content:
                    code_text = '\n'.join(code_block_content)
                    story.append(Paragraph(f"<pre>{code_text}</pre>", code_style))
                    story.append(Spacer(1, 12))
                code_block_content = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
        elif in_code_block:
            code_block_content.append(line)
        
        # Handle headings
        elif line.startswith('# '):
            if 'GenHook AWS Deployment Guide' in line:
                story.append(Paragraph(line[2:], title_style))
                story.append(Spacer(1, 20))
            else:
                story.append(Paragraph(line[2:], heading1_style))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], heading2_style))
        elif line.startswith('### '):
            story.append(Paragraph(line[4:], heading3_style))
        
        # Handle regular paragraphs
        elif line and not line.startswith('-') and not line.startswith('*'):
            # Clean up markdown formatting
            clean_line = re.sub(r'`([^`]+)`', r'<font name="Courier">\\1</font>', line)
            clean_line = re.sub(r'\*\*([^*]+)\*\*', r'<b>\\1</b>', clean_line)
            clean_line = re.sub(r'\*([^*]+)\*', r'<i>\\1</i>', clean_line)
            
            story.append(Paragraph(clean_line, normal_style))
        
        # Add spacing for empty lines
        elif not line:
            story.append(Spacer(1, 6))
        
        i += 1
    
    # Add table of contents at the beginning (simplified)
    toc_data = [
        ['Section', 'Description'],
        ['Prerequisites', 'AWS account, SSH setup, required knowledge'],
        ['AWS Infrastructure', 'EC2 instance, security groups, elastic IP'],
        ['Server Installation', 'Automated installation script'],
        ['Service Configuration', 'Nginx and Supervisor setup'],
        ['Production Settings', 'Configuration for production environment'],
        ['Testing & Validation', 'Health checks and webhook testing'],
        ['External Webhooks', 'GitHub, Stripe, Slack configuration'],
        ['Monitoring', 'Logging, health checks, system monitoring'],
        ['Security & Backup', 'Hardening, backup strategies'],
        ['Cost Analysis', 'AWS pricing breakdown'],
        ['Troubleshooting', 'Common issues and solutions']
    ]
    
    # Insert TOC after title
    toc_table = Table(toc_data, colWidths=[2*inch, 4*inch])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    # Create final story with TOC
    final_story = [
        Paragraph("GenHook AWS Deployment Guide", title_style),
        Paragraph("Production-Ready Webhook Processing System", heading2_style),
        Spacer(1, 30),
        Paragraph("Table of Contents", heading1_style),
        toc_table,
        PageBreak()
    ] + story
    
    # Build PDF
    try:
        doc.build(final_story)
        print(f"✅ PDF created successfully: {pdf_file}")
        return str(pdf_file)
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        print("Make sure you have reportlab installed: pip install reportlab")
        return None

if __name__ == "__main__":
    create_deployment_pdf()