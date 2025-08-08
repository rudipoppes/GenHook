# GenHook Web Configuration Interface - Implementation Plan

## **Project Overview**

This plan outlines the implementation of a web-based configuration interface for GenHook, allowing users to visually configure webhook processing without editing configuration files manually.

## **Folder Structure Design:**
```
backend/
├── app/
│   ├── web/                    # New web interface module
│   │   ├── __init__.py
│   │   ├── routes.py          # Web UI routes (/config, /api/*)
│   │   ├── services.py        # Config management logic
│   │   └── models.py          # Pydantic models for web interface
│   ├── templates/             # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── config.html        # Main configuration interface
│   │   └── components/        # Reusable template components
│   ├── static/               # CSS, JS, assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── core/                 # Existing core functionality
├── config/
│   ├── web-config.ini        # NEW: Web interface configuration
│   ├── app-config.ini        # Existing app config
│   └── webhook-config.ini    # Existing webhook config
└── tests/
    └── test_web_interface.py # Web interface tests
```

## **Configuration-Driven Design**

### **New Web Interface Config (`config/web-config.ini`):**
```ini
[web]
enabled = true
host = 127.0.0.1
port = 8000
base_path = /config
static_path = /static
template_path = templates/

[security]
require_auth = false
allowed_ips = 127.0.0.1,192.168.0.0/16
max_payload_size = 10MB
session_timeout = 3600

[features]
backup_configs = true
backup_retention_days = 30
enable_config_validation = true
enable_live_preview = true
# Dynamic configuration loading enabled by default - no restart needed

[service]
config_file_path = config/webhook-config.ini
backup_directory = backups/configs/
# Configuration changes take effect immediately without service restart

[ui]
theme = default
show_sample_values = true
max_fields_display = 100
default_message_template = $service$ Alert: $summary$
```

## **Implementation Phases**

### **Phase 1: Configurable Foundation**

#### **1.1 Configuration Management System**
- Create `WebConfig` class to load `web-config.ini`
- Support environment variable overrides
- Configuration validation with schema
- Hot-reload configuration without restart

#### **1.2 Modular Web Interface**
- Conditional web interface loading based on config
- Pluggable authentication systems
- Configurable UI themes and layouts
- Dynamic route registration

#### **1.3 Flexible File Management**
- Configurable paths for all files (templates, static, configs)
- Pluggable backup strategies
- Configurable service restart mechanisms
- Support for different deployment environments

### **Phase 2: Core Web Interface**

#### **2.1 FastAPI Web Integration**
- Add Jinja2 templates and static file serving to FastAPI
- Create `/config` web endpoint with HTML interface  
- Add professional CSS styling for the configuration UI
- Add necessary dependencies to requirements.txt

#### **2.2 JSON Payload Analysis Engine**
- Create `/api/analyze-payload` POST endpoint
- Build recursive JSON field discovery that walks entire payload structure
- Detect and categorize field types (string, number, boolean, array, object)
- Handle deeply nested objects and array structures
- Return structured field tree for UI consumption

#### **2.3 Interactive Field Selection Interface**
- Create dynamic tree-view UI showing all discoverable fields
- Add checkboxes for intuitive field selection
- Show visual indicators distinguishing arrays from single values
- Display sample values from actual JSON for context
- Handle complex nested selections properly

### **Phase 3: Configuration Generation**

#### **3.1 GenHook Config String Generator**
- Convert user field selections to proper GenHook syntax
- Handle simple fields: `field_name`
- Handle nested fields: `object{subfield}`, `deep{nested{field}}`
- Handle array fields: `array{property}` with proper array support
- Validate field combinations and syntax correctness

#### **3.2 Message Template Builder**
- Provide template editing interface with variable suggestions
- Auto-complete available variables based on selected fields
- Live preview showing generated message using sample data
- Template syntax validation and error highlighting
- Support for array variable formatting (comma-separated values)

### **Phase 4: Integration & Deployment**

#### **4.1 Configuration File Management**
- Read current webhook-config.ini safely
- Update specific webhook configurations without affecting others
- Implement file locking during updates
- Create automatic backup before changes
- Validate entire config file after modifications

#### **4.2 Service Integration & Restart**
- Safe config file replacement with atomic operations
- Automatic GenHook service restart via supervisorctl
- Monitor restart success/failure with proper error handling
- Implement rollback mechanism if restart fails
- Status reporting to user interface

### **Phase 5: Enhanced Features**

#### **5.1 Multi-Configuration Management**
- Manage all webhook types in single interface
- Show current configurations with edit capabilities
- Import/export functionality for webhook configs
- Configuration templates for common webhook sources

#### **5.2 Testing & Validation Features**
- Test webhook configurations with sample payloads before saving
- Show message preview with actual field extraction
- Configuration diff viewer showing changes before applying
- Validation warnings for potential issues

## **Key Flexible Design Principles**

### **No Hardcoded Values:**
- ✅ All paths configurable via config files
- ✅ All UI settings in configuration
- ✅ All service integration points configurable
- ✅ All security settings externalized

### **Environment Agnostic:**
- ✅ Works in development, staging, production
- ✅ Supports different service managers
- ✅ Adapts to different deployment methods
- ✅ Configurable for different security requirements

### **Modular Architecture:**
- ✅ Web interface can be disabled entirely
- ✅ Components can be swapped/extended
- ✅ Different authentication methods
- ✅ Pluggable storage backends

### **Configuration Hierarchy:**
1. **Default values** in code
2. **Config file values** override defaults
3. **Environment variables** override config files
4. **Runtime settings** override everything

## **Expected User Workflow**

1. **Access Interface**: Navigate to `https://genhook.ddns.net/config`
2. **Input Payload**: Paste JSON payload from webhook documentation/testing
3. **Field Selection**: Select desired fields from visual tree interface
4. **Template Building**: Build message template with live preview feedback
5. **Configuration Review**: Review generated configuration and test with sample data
6. **Deploy**: Save and auto-deploy (service restarts automatically)
7. **Validation**: Test with actual webhook to validate configuration

## **Technical Implementation Details**

- **Framework:** FastAPI + Jinja2 templates + Vanilla JavaScript
- **Dependencies:** Minimal additions (jinja2, python-multipart)
- **Security:** IP-based access control for production safety
- **File Operations:** Secure with proper permissions and error handling
- **Branch Strategy:** Develop on `feature/web-config-interface`

## **Benefits**

- **Non-technical users** can configure webhooks easily
- **Reduced errors** through visual field selection
- **Faster onboarding** of new webhook sources
- **Live testing** prevents configuration mistakes
- **Safe deployment** with rollback capabilities
- **Environment flexibility** through configuration-driven design
- **Maintainability** through clear separation of concerns

## **Security Considerations**

- **Authentication options** configurable (none, basic, IP-based)
- **File access security** with proper permissions
- **Input validation** for all user-provided data
- **Safe service restart** mechanisms
- **Configuration backups** before changes
- **Rollback capabilities** if issues occur

## **Deployment Strategy**

1. **Development Branch**: Create `feature/web-config-interface`
2. **Local Testing**: Test all functionality locally
3. **Staging Deployment**: Deploy to test environment
4. **Production Merge**: Merge to main when stable
5. **Production Deployment**: Deploy with configuration updates

---

**Document Version**: 1.0  
**Created**: January 2025  
**Status**: Implementation Ready