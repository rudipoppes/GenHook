#!/bin/bash
# Generate PDF from GenHook deployment guide
# Requires: pandoc (brew install pandoc on macOS)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MD_FILE="$SCRIPT_DIR/GenHook_AWS_Deployment_Guide.md"
PDF_FILE="$SCRIPT_DIR/GenHook_AWS_Deployment_Guide.pdf"

echo "🔧 Generating PDF from deployment guide..."

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc is not installed"
    echo "Please install pandoc:"
    echo "  macOS: brew install pandoc"
    echo "  Ubuntu: sudo apt install pandoc"
    echo "  Windows: https://pandoc.org/installing.html"
    exit 1
fi

# Check if we have a PDF engine available
if command -v pdflatex &> /dev/null; then
    PDF_ENGINE="pdflatex"
elif command -v xelatex &> /dev/null; then
    PDF_ENGINE="xelatex"
else
    echo "⚠️  No LaTeX engine found. Installing BasicTeX..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install --cask basictex
        # Add BasicTeX to PATH
        export PATH="/usr/local/texlive/2023basic/bin/universal-darwin:$PATH"
        PDF_ENGINE="pdflatex"
    else
        echo "Please install texlive: sudo apt install texlive-latex-base texlive-fonts-recommended"
        exit 1
    fi
fi

echo "🔧 Using PDF engine: $PDF_ENGINE"

# Generate PDF with pandoc
pandoc "$MD_FILE" \
    -o "$PDF_FILE" \
    --pdf-engine="$PDF_ENGINE" \
    --variable geometry:margin=1in \
    --variable fontsize=11pt \
    --variable documentclass=article \
    --variable colorlinks=true \
    --variable linkcolor=blue \
    --variable urlcolor=blue \
    --variable toccolor=gray \
    --toc \
    --toc-depth=3 \
    --highlight-style=github \
    --number-sections

if [ -f "$PDF_FILE" ]; then
    echo "✅ PDF generated successfully: $PDF_FILE"
    echo "📄 File size: $(du -h "$PDF_FILE" | cut -f1)"
    
    # Open PDF on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "🔍 Opening PDF..."
        open "$PDF_FILE"
    fi
else
    echo "❌ Failed to generate PDF"
    exit 1
fi

echo "📋 Alternative methods if pandoc doesn't work:"
echo "  1. Use the web version: open deploy/web_to_pdf.html in browser and print to PDF"
echo "  2. Use Python script: python3 deploy/create_pdf_simple.py (requires: pip install reportlab)"
echo "  3. Copy markdown to any online markdown-to-PDF converter"