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
🚀 **Phase 1**: Core System (In Progress)
- ✅ Basic FastAPI HTTP server
- 🟡 Configuration system (Planned)
- 🟡 Field extraction (Planned)
- 🟡 Template engine (Planned)
- 🟡 SL1 integration (Planned)

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