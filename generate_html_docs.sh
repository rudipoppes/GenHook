#!/bin/bash
# Generate comprehensive HTML documentation for GenHook production deployment

echo "🔄 Generating GenHook Production Documentation HTML..."

# Create output directory
mkdir -p docs/html

# Generate Main Documentation HTML
echo "📄 Generating CLAUDE.md HTML..."
pandoc CLAUDE.md \
    -o docs/html/GenHook_Complete_Guide.html \
    --css=../styles.css \
    --metadata title="GenHook Complete Guide" \
    --metadata author="GenHook Development Team" \
    --metadata date="$(date +%Y-%m-%d)" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --standalone

echo "✅ GenHook_Complete_Guide.html generated"

# Generate Production Deployment Guide HTML
echo "📄 Generating Production Deployment Guide HTML..."
pandoc PRODUCTION_DEPLOYMENT.md \
    -o docs/html/GenHook_Production_Deployment.html \
    --css=../styles.css \
    --metadata title="GenHook Production Deployment Guide" \
    --metadata author="GenHook Development Team" \
    --metadata date="$(date +%Y-%m-%d)" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --standalone

echo "✅ GenHook_Production_Deployment.html generated"

# Generate AWS Deployment Guide HTML
echo "📄 Generating AWS Deployment Guide HTML..."
pandoc AWS_DEPLOYMENT_GUIDE.md \
    -o docs/html/GenHook_AWS_Deployment.html \
    --css=../styles.css \
    --metadata title="GenHook AWS Deployment Guide" \
    --metadata author="GenHook Development Team" \
    --metadata date="$(date +%Y-%m-%d)" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --standalone

echo "✅ GenHook_AWS_Deployment.html generated"

# Generate Combined HTML
echo "📄 Generating Combined Documentation HTML..."
pandoc CLAUDE.md PRODUCTION_DEPLOYMENT.md AWS_DEPLOYMENT_GUIDE.md \
    -o docs/html/GenHook_Complete_Documentation.html \
    --css=../styles.css \
    --metadata title="GenHook Complete Documentation Suite" \
    --metadata author="GenHook Development Team" \
    --metadata date="$(date +%Y-%m-%d)" \
    --toc \
    --toc-depth=3 \
    --number-sections \
    --standalone

echo "✅ GenHook_Complete_Documentation.html generated"

# Generate index page
cat > docs/html/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GenHook Documentation Suite</title>
    <link rel="stylesheet" href="../styles.css">
    <style>
        body { max-width: 900px; margin: 2rem auto; padding: 2rem; }
        .doc-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 2rem 0; }
        .doc-card { border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; background: #f9f9f9; }
        .doc-card h3 { margin-top: 0; color: #2c3e50; }
        .doc-card a { text-decoration: none; color: #3498db; font-weight: bold; }
        .doc-card a:hover { text-decoration: underline; }
        .badge { background: #3498db; color: white; padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem; }
        .updated { color: #27ae60; font-weight: bold; }
    </style>
</head>
<body>
    <header>
        <h1>🚀 GenHook Documentation Suite</h1>
        <p class="updated">Updated: $(date +"%B %d, %Y")</p>
        <p>Comprehensive documentation for GenHook webhook receiver with web configuration interface.</p>
    </header>

    <section>
        <h2>📚 Documentation Overview</h2>
        <p>GenHook is a configuration-driven, multi-threaded webhook receiver with a comprehensive web interface, secure tokenization system, and professional webhook configuration management.</p>
        
        <div class="doc-grid">
            <div class="doc-card">
                <h3>📖 Complete Guide</h3>
                <p>Main project documentation including architecture, features, and web interface usage.</p>
                <p><span class="badge">Phase 6 Complete</span></p>
                <p><a href="GenHook_Complete_Guide.html">View Complete Guide →</a></p>
            </div>

            <div class="doc-card">
                <h3>🏭 Production Deployment</h3>
                <p>Comprehensive production deployment guide with security, monitoring, and best practices.</p>
                <p><span class="badge">Production Ready</span></p>
                <p><a href="GenHook_Production_Deployment.html">View Deployment Guide →</a></p>
            </div>

            <div class="doc-card">
                <h3>☁️ AWS Deployment</h3>
                <p>Detailed AWS deployment with Application Load Balancer, Auto Scaling, and CloudWatch.</p>
                <p><span class="badge">AWS Optimized</span></p>
                <p><a href="GenHook_AWS_Deployment.html">View AWS Guide →</a></p>
            </div>

            <div class="doc-card">
                <h3>📄 All-in-One</h3>
                <p>Complete documentation suite in a single HTML file for offline reading.</p>
                <p><span class="badge">Combined</span></p>
                <p><a href="GenHook_Complete_Documentation.html">View Combined Docs →</a></p>
            </div>
        </div>
    </section>

    <section>
        <h2>🎯 Key Features</h2>
        <ul>
            <li><strong>Web Configuration Interface:</strong> http://localhost:8000/config</li>
            <li><strong>Secure Tokenization:</strong> 32-character tokens for webhook authentication</li>
            <li><strong>3-Step Wizard:</strong> Payload analysis, field selection, template building</li>
            <li><strong>Visual Field Selection:</strong> No manual pattern writing required</li>
            <li><strong>Test-Before-Save:</strong> Real-time configuration testing</li>
            <li><strong>Edit Mode:</strong> Modify existing configurations with token preservation</li>
            <li><strong>Multiple Configs:</strong> Support multiple webhook configs per service type</li>
            <li><strong>Production Ready:</strong> Clean codebase with comprehensive error handling</li>
        </ul>
    </section>

    <section>
        <h2>🔗 Quick Links</h2>
        <ul>
            <li><strong>Repository:</strong> <a href="https://github.com/rudipoppes/GenHook" target="_blank">GitHub</a></li>
            <li><strong>Web Interface:</strong> <a href="http://localhost:8000/config" target="_blank">http://localhost:8000/config</a></li>
            <li><strong>API Documentation:</strong> <a href="http://localhost:8000/docs" target="_blank">http://localhost:8000/docs</a></li>
            <li><strong>Health Check:</strong> <a href="http://localhost:8000/health" target="_blank">http://localhost:8000/health</a></li>
        </ul>
    </section>

    <footer style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #eee; color: #666;">
        <p>Generated on $(date) | GenHook Development Team</p>
    </footer>
</body>
</html>
EOF

echo "✅ index.html generated"

# Generate README
cat > docs/html/README.txt << EOF
GenHook Documentation HTML Suite
Generated on: $(date)

Files:
- index.html                          : Documentation portal and overview
- GenHook_Complete_Guide.html         : Complete project documentation from CLAUDE.md
- GenHook_Production_Deployment.html  : Production deployment guide with security & monitoring
- GenHook_AWS_Deployment.html         : Detailed AWS deployment with ALB, Auto Scaling, etc.
- GenHook_Complete_Documentation.html : Combined documentation (all in one file)

Description:
These HTML files contain comprehensive documentation for deploying and managing GenHook
in production environments, including the new web configuration interface.

To view:
Open index.html in your web browser for a complete documentation portal.

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
echo "🎉 Documentation HTML files generated successfully!"
echo "📁 Location: $(pwd)/docs/html/"
echo ""
echo "Generated files:"
ls -la docs/html/
echo ""
echo "🌐 Open docs/html/index.html in your browser to access the documentation portal."