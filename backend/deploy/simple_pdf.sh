#!/bin/bash
# Simple PDF generation using pandoc HTML output and system print
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MD_FILE="$SCRIPT_DIR/GenHook_AWS_Deployment_Guide.md"
HTML_FILE="$SCRIPT_DIR/deployment_guide.html"
PDF_FILE="$SCRIPT_DIR/GenHook_AWS_Deployment_Guide.pdf"

echo "🔧 Generating PDF from deployment guide..."

# Generate styled HTML with pandoc
pandoc "$MD_FILE" \
    -o "$HTML_FILE" \
    --standalone \
    --toc \
    --toc-depth=3 \
    --css=data:text/css,"\
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; } \
h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; } \
h2 { color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; margin-top: 30px; } \
h3 { color: #7f8c8d; margin-top: 25px; } \
code { background-color: #f8f9fa; padding: 2px 6px; border-radius: 3px; font-family: 'Monaco', 'Consolas', monospace; font-size: 0.9em; } \
pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; overflow-x: auto; } \
pre code { background-color: transparent; padding: 0; } \
table { border-collapse: collapse; width: 100%; margin: 15px 0; } \
th, td { border: 1px solid #ddd; padding: 12px; text-align: left; } \
th { background-color: #f2f2f2; font-weight: bold; } \
@media print { body { max-width: none; margin: 0; padding: 15px; } }" \
    --metadata title="GenHook AWS Deployment Guide"

echo "✅ HTML generated: $HTML_FILE"
echo "📋 To create PDF:"
echo "  1. Open: $HTML_FILE"
echo "  2. Press Cmd+P (macOS) or Ctrl+P (Windows/Linux)"
echo "  3. Choose 'Save as PDF'"
echo "  4. Save as: $PDF_FILE"
echo ""
echo "🌐 Opening HTML file in default browser..."

# Open HTML file in default browser
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "$HTML_FILE"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "$HTML_FILE"
elif [[ "$OSTYPE" == "msys" ]]; then
    start "$HTML_FILE"
fi

echo "✅ HTML deployment guide ready for printing to PDF"