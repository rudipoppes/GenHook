#!/usr/bin/env python3
"""
Convert GenHook deployment guide to PDF
Requires: pip install markdown pdfkit
"""

import markdown
import pdfkit
import os
from pathlib import Path

def generate_pdf():
    """Convert markdown deployment guide to PDF"""
    
    # File paths
    script_dir = Path(__file__).parent
    md_file = script_dir / "GenHook_AWS_Deployment_Guide.md"
    html_file = script_dir / "deployment_guide.html"
    pdf_file = script_dir / "GenHook_AWS_Deployment_Guide.pdf"
    
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert markdown to HTML with extensions
    html_content = markdown.markdown(
        md_content, 
        extensions=['codehilite', 'tables', 'toc', 'fenced_code']
    )
    
    # Create full HTML document with styling
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>GenHook AWS Deployment Guide</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
            }}
            
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 5px;
                margin-top: 30px;
            }}
            
            h3 {{
                color: #7f8c8d;
                margin-top: 25px;
            }}
            
            code {{
                background-color: #f8f9fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 0.9em;
            }}
            
            pre {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                border-left: 4px solid #3498db;
                overflow-x: auto;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 0;
                padding: 0 15px;
                color: #7f8c8d;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            .highlight-box {{
                background-color: #e8f6ff;
                border: 1px solid #3498db;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .warning-box {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
            }}
            
            .success-box {{
                background-color: #d4edda;
                border: 1px solid #28a745;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
            }}
            
            @media print {{
                body {{
                    max-width: none;
                    margin: 0;
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Write HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    # PDF options
    options = {
        'page-size': 'A4',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'no-outline': None,
        'enable-local-file-access': None,
        'print-media-type': None,
    }
    
    try:
        # Convert HTML to PDF
        pdfkit.from_file(str(html_file), str(pdf_file), options=options)
        print(f"✅ PDF generated successfully: {pdf_file}")
        
        # Clean up HTML file
        os.remove(html_file)
        
        return str(pdf_file)
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        print("Make sure you have wkhtmltopdf installed:")
        print("  macOS: brew install wkhtmltopdf")
        print("  Ubuntu: sudo apt-get install wkhtmltopdf")
        print("  Windows: Download from https://wkhtmltopdf.org/downloads.html")
        return None

if __name__ == "__main__":
    generate_pdf()