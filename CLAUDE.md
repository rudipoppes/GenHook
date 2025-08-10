# GenHook Project Notes

## Project Overview

### System Purpose
GenHook is a configuration-driven, multi-threaded webhook receiver that:
- Accepts webhooks from multiple services (GitHub, Stripe, Slack, AWS, etc.)
- Extracts specified fields using configuration files
- Generates human-readable messages using templates
- Forwards events to SL1 monitoring system via API

### Key Features
- **Configuration-Driven**: No code changes needed for new webhook types
- **Dynamic Configuration Loading**: Configuration changes take effect immediately without service restarts
- **Multi-Threaded**: Handle thousands of concurrent webhooks
- **Template-Based Messaging**: Flexible message generation
- **SL1 Integration**: Direct API integration with default values
- **Error Handling**: Graceful failure handling and retry logic

### Architecture
- FastAPI-based HTTP server
- 7-step processing pipeline: Reception → Identification → Configuration Lookup → Field Extraction → Message Generation → SL1 API Call → Error Handling
- Configurable threading models: Thread Pool Pattern, Async Event Loop, or Hybrid Approach
- Queue management with in-memory and persistent options

## Backend Startup
Always start the backend when working on this project:
```bash
cd backend && ./start.sh
```

Or manually:
```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
python main.py
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

## Web Configuration Interface

### Overview
GenHook features a professional, responsive web-based configuration interface with a modern 2-column layout. The interface eliminates manual file editing and provides a complete webhook configuration management system with real-time testing and validation.

### Access & Layout
- **Web Interface**: http://localhost:8000/config
- **Professional 65/35 Layout**: Configuration table and wizard on the left (65%), payload sidebar on the right (35%)
- **Responsive Design**: Optimized for desktop and mobile with intelligent breakpoints
- **Sticky Sidebar**: Payload section stays visible while scrolling through configurations

### Key Features

#### 1. **Modern 2-Column Interface**
- **Left Column**: Configuration table and 3-step wizard (65% width)
- **Right Column**: Payload loading and JSON editing sidebar (35% width)
- **Hidden-by-Default Wizard**: Clean interface with "New Config" button in table header
- **Real-time Updates**: All changes take effect immediately without service restarts

#### 2. **3-Step Configuration Wizard**
- **Step 1: Basic Information** - Webhook type name and quick templates
- **Step 2: Field Selection** - Visual field selection with existing configurations displayed
- **Step 3: Template Building** - Message template creation with live preview

#### 3. **Enhanced Payload Sidebar**
- **Recent Payload Loading**: Auto-load from previous webhook executions by type
- **Auto-Loading Dropdowns**: Automatic payload loading when selections change
- **JSON Validation**: Real-time syntax validation and error reporting
- **Sticky Positioning**: Always visible during configuration workflow

#### 4. **Improved Edit Mode**
- **Shows Existing Data**: Displays current field selections and message template
- **Step 2 Start**: Begins editing in field selection to show what's currently configured
- **Modify Everything**: Change field selections, reorganize variables, edit templates
- **Visual Field Display**: Checkboxes show current selections, enable modifications

#### 5. **Configuration Management**
- **Professional Table**: Clean overview of all webhook configurations
- **Inline Actions**: Edit and delete buttons for each configuration
- **Automatic Backups**: Safe configuration updates with rollback capability
- **Dynamic Loading**: No service restarts required for configuration changes

### Quick Start Guide

#### Creating a New Webhook Configuration:
1. Navigate to http://localhost:8000/config
2. Click the **"New Config"** button in the configurations table header
3. Enter webhook type name (e.g., "github", "stripe") in Step 1
4. Use the **payload sidebar** to load a recent payload or paste JSON data
5. Click **"Analyze Payload"** to discover extractable fields (→ Step 2)
6. **Select fields** using checkboxes - see real-time field pattern generation
7. Click **"Create Template"** to proceed to Step 3
8. **Build your message template** using variables like `$field.name$`
9. Click **"Test Config"** to validate with the sidebar payload
10. Click **"Save Configuration"** (takes effect immediately)

#### Editing Existing Configurations:
1. Click the **edit button** (pencil icon) on any configuration
2. **Step 2 opens** showing current field selections with pre-checked boxes
3. **Modify field selections** - check/uncheck fields as needed
4. Use the **payload sidebar** to load recent payloads for testing
5. Click **"Create Template"** to proceed to template editing (Step 3)
6. **Edit the message template** - reorganize variables, modify text
7. Click **"Test Config"** to validate changes with sidebar payload
8. Click **"Save Configuration"** to update (takes effect immediately)

#### Using the Payload Sidebar:
1. **Select webhook type** from dropdown to load recent payloads
2. **Choose recent payload** - auto-loads when selected (no manual button)
3. **Or paste JSON directly** into the payload textarea
4. **Validate JSON** using the validation button for syntax checking
5. **Payload stays loaded** throughout the entire configuration workflow

### Configuration File Integration
- Configurations are saved to `backend/config/webhook-config.ini`
- Automatic backup creation in `backend/config/backups/`
- **Dynamic Loading**: Changes take effect immediately without service restarts
- No manual file editing required

### Web Interface Configuration
The web interface can be configured via `backend/config/web-config.ini`:

```ini
[ui]
enabled = true
max_analysis_depth = 3
timeout_seconds = 30

[features]
backup_configs = true
enable_config_validation = true
enable_live_preview = true
```

## Supported Webhook Sources

### Service Providers
- **GitHub**: Push, Pull Request, Issues, Releases
- **Stripe**: Payments, Subscriptions, Customers
- **Slack**: Messages, User Actions, App Events
- **AWS EventBridge/CloudWatch**: EC2, Lambda, S3, CloudFormation
- **Cisco Meraki**: Device Alerts, Network Events, Security Events
- **Jira**: Issue Updates, Comments, Transitions
- **Azure Event Grid**: Storage, Resource Management, Service Bus
- **Shopify**: Orders, Customers, Products, Inventory

### Configuration Format
Each webhook type is configured using INI syntax:
```ini
webhook_type: field1,field2,nested{subfield}::Message template with $variables$
```

### Field Extraction Patterns
- **Simple Field**: `field_name`
- **Nested Object**: `object{subfield}`
- **Deep Nesting**: `level1{level2{level3}}`
- **Arrays**: `array_field{item_property}`

## Technical Architecture

### Threading Models
1. **Thread Pool Pattern**: HTTP Server → Request Queue → Thread Pool → SL1 API
   - Use Case: Moderate loads (< 1000 req/sec)
   - Pros: Simple, predictable resource usage
   - Cons: Thread creation overhead

2. **Async Event Loop**: Event Loop → Async Tasks → Non-blocking I/O
   - Use Case: High concurrency, I/O bound
   - Pros: Memory efficient, handles 10k+ connections
   - Cons: Single-threaded CPU processing

3. **Hybrid Approach**: Async HTTP → Message Queue → Worker Thread Pool
   - Use Case: Mixed CPU/I/O workloads
   - Pros: Best of both worlds
   - Cons: More complex architecture

### Configuration Parameters
```ini
# Threading Configuration
max_worker_threads = 50
queue_max_size = 10000
processing_timeout = 30s
retry_max_attempts = 3
shutdown_grace_period = 60s

# Per-webhook limits
shopify_max_concurrent = 10
slack_max_concurrent = 20
aws_max_concurrent = 100
meraki_max_concurrent = 25
```

### SL1 Integration
- **API Endpoint**: `POST /api/alert`
- **Authentication**: HTTP Basic Auth (username/password)
- **Payload Format**: Simplified JSON with only `message` field populated
- **Default Values**: All other fields use SL1 defaults
- **Retry Logic**: Exponential backoff for failed API calls

### Queue Management
- **In-Memory**: Low latency, volatile
- **Persistent**: Redis/RabbitMQ for reliability
- **Priority**: Different webhook types by importance
- **Dead Letter**: Failed processing queue

## Configuration System

### Dynamic Configuration Loading

GenHook implements **dynamic configuration loading** - configuration changes take effect immediately without requiring service restarts. This provides significant operational benefits:

#### Key Benefits
- **Zero Downtime Configuration Updates**: Modify webhook configurations while the service continues processing webhooks
- **Instant Testing**: Test new webhook configurations immediately after saving
- **Simplified Operations**: No need to restart services, coordinate downtime, or use `supervisorctl restart`
- **Production-Safe**: Configurations are validated and loaded atomically to prevent partial updates

#### How It Works
1. **Configuration Read on Demand**: Each webhook request reads the latest configuration from disk
2. **Atomic File Operations**: Configuration files are updated atomically to prevent partial reads
3. **Automatic Backup**: Previous configurations are backed up before changes
4. **Real-Time Validation**: Configurations are validated before being applied

#### What This Means for Operations
- **Web Interface**: Save configurations and they take effect immediately
- **Manual Config Edits**: Direct file edits to `webhook-config.ini` are picked up on next webhook
- **Production Deployments**: Configuration updates without service interruption
- **Development Workflow**: Faster iteration when testing new webhook configurations

#### Important: What Still Requires Restart
While webhook configurations are dynamic, the following changes still require a service restart:
- **Code Changes**: Any modifications to Python files (main.py, services, etc.)
- **App Configuration**: Changes to `app-config.ini` (server settings, ports, etc.)
- **Dependencies**: Installing or updating Python packages
- **Web Configuration**: Changes to `web-config.ini` settings
- **Logging Levels**: Modifications to logging configuration

### Template Variables
- **Simple Substitution**: `$field_name$`
- **Nested Access**: `$object.subfield$`
- **Array Access**: `$array[0].property$`

### Template Examples
```ini
# GitHub Events
github: action,pull_request{title,user{login}},repository{name}::GitHub $action$ on $repository.name$: "$pull_request.title$" by $pull_request.user.login$

# Stripe Payments
stripe: type,data{object{amount,currency,status}}::Stripe $type$: Payment of $data.object.amount$ $data.object.currency$ status: $data.object.status$

# Slack Messages  
slack: event{type,user,text}::Slack $event.type$ from user $event.user$: "$event.text$"

# AWS Events
aws: detail-type,source,region,detail{instance-id,state}::AWS $detail-type$ from $source$ in $region$: Instance $detail.instance-id$ state: $detail.state$
```

### Environment Configuration
```ini
# Server Settings
server_port = 8080
server_host = 0.0.0.0
ssl_enabled = true
ssl_cert_path = /etc/ssl/webhook-receiver.crt
ssl_key_path = /etc/ssl/webhook-receiver.key

# SL1 API Settings
sl1_api_url = https://sl1.company.com/api/alert
sl1_username = your_sl1_username
sl1_password = your_sl1_password
sl1_timeout = 30s
sl1_retry_attempts = 3

# Threading Settings
max_threads = 50
queue_size = 10000
thread_timeout = 30s

# Logging
log_level = INFO
log_file = /var/log/webhook-receiver.log
log_max_size = 100MB
log_rotation = daily
```

## Development Phases

### Phase 1: Core System
- [ ] HTTP server with webhook endpoints
- [ ] Configuration file parser
- [ ] JSON field extraction engine
- [ ] Template processing system
- [ ] Basic SL1 API integration

### Phase 2: Multi-Threading
- [ ] Thread pool implementation
- [ ] Request queue system
- [ ] Error handling and retries
- [ ] Graceful shutdown handling
- [ ] Resource cleanup

### Phase 3: Production Features
- [ ] Webhook signature verification
- [ ] Rate limiting and throttling
- [ ] Comprehensive logging
- [ ] Metrics collection
- [ ] Health check endpoints

### Phase 4: Operations
- [ ] Configuration validation
- [ ] Performance monitoring
- [ ] Alerting on failures
- [ ] Documentation and runbooks
- [ ] Deployment automation

### Current Status
🚀 **Phase 1**: Core System (COMPLETED)
- ✅ FastAPI HTTP server with webhook endpoints
- ✅ Configuration file parser and management
- ✅ JSON field extraction engine with array support
- ✅ Template processing system
- ✅ SL1 API integration with retry logic
- ✅ HTTPS/SSL support for secure webhooks
- ✅ Empty payload handling with 200 responses

🎉 **Phase 5**: Web Configuration Interface (COMPLETED) 
- ✅ **Professional 2-Column Layout**: 65/35 split with responsive design and sticky sidebar
- ✅ **Enhanced 3-Step Wizard**: Hidden by default with "New Config" button in table header
- ✅ **Auto-Loading Payload Sidebar**: Recent payload loading with dropdown auto-selection
- ✅ **Improved Edit Mode**: Shows existing field selections and templates, starts at Step 2
- ✅ **Visual Field Management**: Checkbox-based field selection with real-time updates
- ✅ **Real-time Testing**: Test configurations with sidebar payloads before saving
- ✅ **Dynamic Configuration Loading**: No service restarts required for config changes
- ✅ **Professional UI/UX**: Bootstrap 5 responsive interface with modern design patterns
- ✅ **Production-Ready**: Clean codebase, error handling, and automatic backups

🔧 **Next Phases**: Multi-Threading & Production Features (PLANNED)
- 🟡 Thread pool implementation for high-volume processing
- 🟡 Advanced monitoring and metrics collection
- 🟡 Production deployment automation
- 🟡 Load balancing and scaling strategies

## Production Deployment

### Port Configuration (Configuration-Driven)

**All port configuration is handled via config files - no code changes required!**

#### Development Mode (default)
- GenHook reads `backend/config/app-config.ini`
- Default port: 8000 (HTTP)
- Access: http://localhost:8000

#### Production Mode Options

**Option 1: Direct HTTPS (Port 443)**
```ini
# Create backend/config/app-config.prod.ini
[server]
host = 0.0.0.0
port = 443
reload = false
```

**Option 2: Reverse Proxy (Recommended)**
```ini
# Keep default port 8000 in app-config.ini
# Use nginx/Apache to proxy port 443 → 8000
[server]
host = 0.0.0.0
port = 8000
reload = false
```

**Option 3: Custom Port**
```ini
# Any port you need
[server]
host = 0.0.0.0
port = 9000  # or any port
reload = false
```

#### Port Configuration Logic
1. If `app-config.prod.ini` exists → uses production config
2. Otherwise → uses `app-config.ini` (development)
3. GenHook automatically detects and uses the appropriate config
4. **No code modification ever required**

#### Endpoint Access
- **API Endpoints**: `/webhook/{service}` for webhook reception
- **Web Interface**: `/config` for configuration management
- **Health Check**: `/health` for monitoring
- **API Documentation**: `/docs` for FastAPI swagger docs

### AWS Deployment Considerations
- **Application Load Balancer**: Route traffic to GenHook instances
- **Security Groups**: Allow inbound 8000 from ALB, outbound 443 to SL1
- **Auto Scaling**: Scale based on webhook volume metrics
- **CloudWatch**: Monitor application logs and metrics
- **Secrets Manager**: Store SL1 credentials securely

### Reverse Proxy Configuration (nginx)
```nginx
server {
    listen 443 ssl;
    server_name your-genhook-domain.com;
    
    ssl_certificate /path/to/ssl/cert.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Environment Variables for Production
```bash
# Set in production environment
GENHOOK_ENV=production
SL1_API_URL=https://your-sl1-instance.com/api/alert
SL1_USERNAME=your_sl1_user
SL1_PASSWORD=your_sl1_password
WEB_INTERFACE_ENABLED=true
```

### Configuration Files for Production
- Ensure `backend/config/webhook-config.ini` contains your webhook configurations
- Configuration changes take effect immediately through dynamic loading
- Backup configurations are stored in `backend/config/backups/`

### Security Checklist
- ✅ HTTPS enabled for all webhook endpoints
- ✅ Web interface accessible only from authorized networks
- ✅ SL1 credentials stored securely (not in code)
- ✅ Webhook signature verification enabled where possible
- ✅ Rate limiting configured for webhook endpoints
- ✅ Regular backup of configuration files

## Security & Performance

### Security Considerations
- **Webhook Verification**: Validate signatures from webhook providers
- **Rate Limiting**: Prevent spam/DoS attacks
- **Input Validation**: Sanitize all webhook payloads
- **Authentication**: Secure SL1 API credentials (username/password for HTTP Basic Auth)
- **HTTPS Only**: Encrypt all webhook traffic

### Error Handling Strategy
- **Graceful Degradation**: Continue processing other webhooks
- **Retry Logic**: Exponential backoff for failed API calls
- **Dead Letter Queue**: Store unprocessable webhooks
- **Circuit Breaker**: Protect against downstream failures
- **Timeout Handling**: Prevent hung threads

### Performance Optimization
- **Connection Pooling**: Reuse HTTP connections to SL1
- **Batch Processing**: Group multiple events when possible
- **Caching**: Cache configuration and templates
- **Metrics**: Monitor processing times and throughput
- **Profiling**: Identify bottlenecks in production

### Monitoring Points
- **Webhook Ingestion Rate**: Webhooks received per second
- **Processing Latency**: Time from receipt to SL1 API call
- **Error Rates**: Failed processing percentage
- **Queue Depth**: Backlog of pending webhooks
- **Thread Utilization**: Active vs idle threads
- **SL1 API Response Times**: Downstream service health

### Key Metrics to Track
- **Webhook Reception Rate**: webhooks/second by type
- **Processing Latency**: 95th percentile processing time
- **Error Rate**: Failed webhooks percentage
- **SL1 API Success Rate**: Successful API calls percentage
- **Queue Depth**: Current backlog size
- **Thread Pool Utilization**: Active threads / total threads

## Web Configuration Interface Plan

### Overview
A comprehensive web-based interface for configuring GenHook webhooks without manual file editing.

### Key Features
- **Visual Field Selection**: Interactive tree view of JSON payload fields
- **Live Preview**: Real-time message generation preview
- **Template Builder**: Guided template creation with variable suggestions  
- **Configuration Management**: Safe config updates with backup and rollback
- **Dynamic Loading**: Configuration changes take effect immediately without service restarts

### Architecture
- **Framework**: FastAPI + Jinja2 templates + Vanilla JavaScript
- **Configuration-Driven**: All settings externalized to `web-config.ini`
- **Security**: IP-based access control and input validation
- **File Operations**: Atomic config updates with backup mechanisms

### Implementation Structure
```
backend/
├── app/
│   ├── web/                    # Web interface module
│   │   ├── routes.py          # Web UI routes
│   │   ├── services.py        # Config management logic
│   │   └── models.py          # Pydantic models
│   ├── templates/             # Jinja2 HTML templates
│   ├── static/               # CSS, JS, assets
├── config/
│   └── web-config.ini        # Web interface configuration
```

### User Workflow
1. Access web interface at `/config`
2. Paste JSON payload from webhook source
3. Select fields using interactive tree interface
4. Build message template with live preview
5. Save configuration (takes effect immediately)
6. Test with actual webhook

### Documentation
- **Full Implementation Plan**: `WEB_INTERFACE_PLAN.md`
- **Branch Strategy**: `feature/web-config-interface`
- **Status**: Ready for implementation

### Benefits
- **User-Friendly**: No technical knowledge required
- **Error Reduction**: Visual field selection prevents mistakes
- **Fast Onboarding**: Quick setup of new webhook sources
- **Safe Deployment**: Backup and rollback capabilities

#### Recent Enhancement: Super Easy Recent Payload Loading 🚀
The web interface now includes enhanced recent payload loading with:
- **Smart Dropdowns**: Auto-populated webhook types and recent payloads
- **Edit Mode Integration**: When editing configs, webhook type auto-selects and loads recent payloads
- **Visual Cards**: Green for recent payload loading, blue for manual input
- **1-Click Loading**: Load real webhook data directly into test fields
- **Both Modes**: Available in both new configuration creation and edit modes

## Webhook Payload Logging

### Overview
GenHook automatically logs all received webhook payloads for debugging and template development. Each webhook type gets its own directory with rotating log files to prevent disk space issues.

### Features
- **Automatic Directory Creation**: New webhook types automatically get log directories
- **Rotating Logs**: Prevents disk space issues (10MB per file, 5 backups)
- **JSON Format**: Easy to parse and analyze
- **Web Interface Integration**: Load recent payloads directly into config interface
- **Permission Handling**: Graceful handling of permission issues in production

### Configuration
Edit `backend/config/app-config.ini`:
```ini
[webhook_logging]
enabled = true
base_directory = logs/webhooks
max_bytes = 10485760  # 10MB per file
backup_count = 5  # Keep 5 backup files
log_file_name = payload.log
```

### Directory Structure
```
backend/logs/
├── webhooks/
│   ├── github/
│   │   ├── payload.log      # Current log
│   │   ├── payload.log.1    # First backup
│   │   └── payload.log.2    # Second backup
│   ├── stripe/
│   │   └── payload.log
│   └── [auto-created for each webhook type]/
```

### Web Interface Features
- **Load Recent Payload** section in config interface (both create and edit modes)
- **Smart Dropdowns** showing webhook types and last 10 payloads with timestamps  
- **Auto-populate functionality** in test payload fields
- **Edit Mode Integration** with auto-populated webhook type selection
- **Visual Cards** - Green for recent payloads, blue for manual input
- **API endpoints**: 
  - `GET /api/webhook-logs/{webhook_type}/recent?limit=10` - Get recent payloads
  - `GET /api/webhook-logs/types` - Get available webhook types

### Production Deployment (AWS)

#### Initial Setup (One Time)
```bash
# Switch to genhook user
sudo su - genhook
cd /opt/genhook

# Create logs directory
mkdir -p /opt/genhook/backend/logs/webhooks
chmod 755 /opt/genhook/backend/logs
chmod 755 /opt/genhook/backend/logs/webhooks

# Mark webhook-config.ini to ignore future changes
git update-index --skip-worktree backend/config/webhook-config.ini
```

#### Deploying Updates
```bash
# As genhook user
sudo su - genhook
cd /opt/genhook

# Stash local changes
git stash save "Production config - $(date +%Y%m%d_%H%M%S)"

# Pull updates
git pull origin main  # or feature branch

# Restore local changes
git stash pop

# Exit and restart
exit
sudo supervisorctl restart genhook
```

### Production Notes
- Service runs as `genhook` user via supervisor
- Logs directory: `/opt/genhook/backend/logs/webhooks/`
- Permissions: 755 for directories, 644 for log files
- Owner: genhook:genhook
- Automatic rotation prevents disk space issues

### Troubleshooting

#### Permission Issues
```bash
# Check service user
ps aux | grep genhook

# Fix log directory permissions
sudo chown -R genhook:genhook /opt/genhook/backend/logs
sudo chmod -R 755 /opt/genhook/backend/logs
```

#### Viewing Logs
```bash
# View recent payloads for a webhook type
sudo -u genhook tail -f /opt/genhook/backend/logs/webhooks/github/payload.log

# Parse JSON logs
sudo -u genhook cat /opt/genhook/backend/logs/webhooks/github/payload.log | jq '.'
```

#### Log Rotation
- Automatic rotation at 10MB
- Keeps 5 backup files (payload.log.1 through payload.log.5)
- Oldest logs are deleted automatically

### Log Format
Each log entry (one per line for easy parsing):
```json
{
  "timestamp": "2025-08-10T12:00:00Z",
  "webhook_type": "github",
  "payload": {...actual webhook payload...},
  "source_ip": "192.168.1.1",
  "user_agent": "GitHub-Hookshot/12345",
  "processing_status": "success",
  "generated_message": "GitHub push on repo...",
  "content_length": "1234"
}
```

### API Endpoints
- `GET /api/webhook-logs/{webhook_type}/recent?limit=10` - Get recent payloads
- `GET /api/webhook-logs/types` - Get list of webhook types with logs

### Benefits
- **Debugging**: See actual payloads when webhooks fail or produce unexpected output
- **Template Development**: Use real payloads to create/refine webhook configurations with 1-click loading
- **Audit Trail**: Track what webhooks were received and when with full metadata
- **Super Easy Configuration**: Load recent payloads in both create and edit modes
- **Smart Edit Mode**: Auto-populated webhook type with instant access to recent payloads  
- **Visual Interface**: Color-coded cards (green for logs, blue for manual input)
- **Disk Management**: Automatic rotation prevents runaway disk usage

### Enhanced User Workflow
1. **Creating New Config**: Select webhook type → Load recent payload → Build template
2. **Editing Existing Config**: Click edit → Webhook type auto-selected → Load recent payloads → Test changes
3. **Real-time Testing**: Load actual webhook data to test template changes instantly
4. **No Manual Copy/Paste**: Direct integration between logs and configuration interface