#!/bin/bash

# Generate SSL Setup Guide PDF

echo "🔒 Generating SSL Setup Guide PDF..."

# Check if pandoc is available
if ! command -v pandoc &> /dev/null; then
    echo "❌ Pandoc not found. Installing via Homebrew..."
    brew install pandoc
fi

# Generate HTML first
pandoc SSL_Setup_Guide.md -o SSL_Setup_Guide.html \
    --standalone \
    --css=https://cdn.jsdelivr.net/npm/github-markdown-css@4/github-markdown.min.css \
    --metadata title="GenHook SSL Setup Guide"

echo "✅ HTML generated: $(pwd)/SSL_Setup_Guide.html"

echo "📋 To create PDF:"
echo "  1. Open: $(pwd)/SSL_Setup_Guide.html"
echo "  2. Press Cmd+P (macOS) or Ctrl+P (Windows/Linux)"
echo "  3. Choose 'Save as PDF'"
echo "  4. Save as: $(pwd)/GenHook_SSL_Setup_Guide.pdf"

echo ""
echo "🌐 Opening HTML file in default browser..."
open SSL_Setup_Guide.html

echo "✅ SSL Setup Guide ready for printing to PDF"