#!/bin/bash

# Generate Web Interface Plan PDF

echo "🔧 Generating Web Interface Plan PDF..."

# Check if pandoc is available
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc not found. Installing via Homebrew..."
    brew install pandoc
fi

# Navigate to project root
cd /Users/rudipoppes/Documents/VisCode/GenHook/

# Generate HTML first
pandoc WEB_INTERFACE_PLAN.md -o WEB_Interface_Plan.html \
    --standalone \
    --css=https://cdn.jsdelivr.net/npm/github-markdown-css@4/github-markdown.min.css \
    --metadata title="GenHook Web Interface Implementation Plan"

echo "✅ HTML generated: $(pwd)/WEB_Interface_Plan.html"

echo "📋 To create PDF:"
echo "  1. Open: $(pwd)/WEB_Interface_Plan.html"
echo "  2. Press Cmd+P (macOS) or Ctrl+P (Windows/Linux)"
echo "  3. Choose 'Save as PDF'"
echo "  4. Save as: $(pwd)/GenHook_Web_Interface_Plan.pdf"

echo ""
echo "🌐 Opening HTML file in default browser..."
open WEB_Interface_Plan.html

echo "✅ Web Interface Plan documentation ready for printing to PDF"