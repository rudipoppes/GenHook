#!/bin/bash
# Generate comprehensive PDF documentation for GenHook production deployment

echo "🔄 Generating GenHook Production Documentation PDFs..."

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "❌ pandoc is not installed. Please install pandoc first:"
    echo "   macOS: brew install pandoc"
    echo "   Ubuntu: sudo apt-get install pandoc"
    echo "   Windows: Download from https://pandoc.org/installing.html"
    exit 1
fi

# Create output directory
mkdir -p docs/pdf

# Generate PDFs with basic pandoc options
echo "📄 Generating documentation PDFs..."

pandoc CLAUDE.md -o docs/pdf/GenHook_Complete_Guide.pdf --toc
echo "✅ GenHook_Complete_Guide.pdf generated"

pandoc PRODUCTION_DEPLOYMENT.md -o docs/pdf/GenHook_Production_Deployment.pdf --toc
echo "✅ GenHook_Production_Deployment.pdf generated"

pandoc AWS_DEPLOYMENT_GUIDE.md -o docs/pdf/GenHook_AWS_Deployment.pdf --toc
echo "✅ GenHook_AWS_Deployment.pdf generated"

pandoc CLAUDE.md PRODUCTION_DEPLOYMENT.md AWS_DEPLOYMENT_GUIDE.md -o docs/pdf/GenHook_Complete_Documentation.pdf --toc
echo "✅ GenHook_Complete_Documentation.pdf generated"

# Generate README
cat > docs/pdf/README.txt << EOF
GenHook Documentation PDF Suite
Generated on: $(date)

Files:
- GenHook_Complete_Guide.pdf          : Complete project documentation from CLAUDE.md
- GenHook_Production_Deployment.pdf   : Production deployment guide with security & monitoring
- GenHook_AWS_Deployment.pdf          : Detailed AWS deployment with ALB, Auto Scaling, etc.
- GenHook_Complete_Documentation.pdf  : Combined documentation (all in one file)

Description:
These PDFs contain comprehensive documentation for deploying and managing GenHook
in production environments, including the new web configuration interface.

Key Features Documented:
✅ Web Configuration Interface (http://localhost:8000/config)
✅ 3-step webhook configuration wizard
✅ Visual field selection and testing
✅ Production deployment strategies
✅ AWS infrastructure setup
✅ Security and monitoring best practices
✅ Troubleshooting and maintenance procedures

For the latest documentation, visit:
https://github.com/rudipoppes/GenHook
EOF

echo ""
echo "🎉 Documentation PDFs generated successfully!"
echo "📁 Location: $(pwd)/docs/pdf/"
echo ""
echo "Generated files:"
ls -la docs/pdf/
echo ""
echo "📖 Open the PDFs to review the complete GenHook documentation suite."