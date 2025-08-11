"""
FastAPI routes for the web configuration interface.
"""
import json
import re
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import get_web_config
from .models import (
    PayloadAnalysisRequest,
    PayloadAnalysisResponse,
    ConfigGenerationRequest,
    ConfigGenerationResponse,
    ConfigSaveRequest,
    ConfigSaveResponse,
    WebhookTestRequest,
    WebhookTestResponse,
    ConfigListResponse,
)
from .services import PayloadAnalyzer, ConfigGenerator, ConfigManager
from ..services.webhook_logger import get_webhook_logger
from ..services.token_generator import generate_unique_token

# Create router
router = APIRouter()

# Get web configuration
web_config = get_web_config()

# Templates will be configured by main app
templates = None

# Service instances
payload_analyzer = PayloadAnalyzer()
config_generator = ConfigGenerator()
config_manager = ConfigManager()


def get_templates():
    """Dependency to get templates instance."""
    if templates is None:
        raise HTTPException(status_code=500, detail="Templates not configured")
    return templates


@router.get("/config", response_class=HTMLResponse)
async def config_interface(request: Request, templates: Jinja2Templates = Depends(get_templates)):
    """Main configuration interface page."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    # Load current configurations
    current_configs = config_manager.load_current_configs()
    
    context = {
        "request": request,
        "config": web_config,
        "current_configs": current_configs,
        "total_configs": len(current_configs),
    }
    
    return templates.TemplateResponse("config.html", context)


@router.post("/api/analyze-payload", response_model=PayloadAnalysisResponse)
async def analyze_payload(request: PayloadAnalysisRequest):
    """Analyze JSON payload to discover extractable fields."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    return payload_analyzer.analyze_payload(request.payload, request.webhook_type)


@router.post("/api/generate-config", response_model=ConfigGenerationResponse)
async def generate_config(request: ConfigGenerationRequest):
    """Generate webhook configuration from selected fields."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    return config_generator.generate_config(
        request.webhook_type,
        request.selected_fields,
        request.message_template
    )


@router.post("/api/test-config", response_model=WebhookTestResponse)
async def test_config(request: WebhookTestRequest):
    """Test webhook configuration using the SAME production webhook processing logic."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        import time
        import tempfile
        import os
        from configparser import ConfigParser
        
        # Get the test data from the request  
        if request.selected_fields and request.message_template:
            # Test BEFORE saving - create temporary config
            fields = request.selected_fields
            template = request.message_template
            config_line = ",".join(fields) + "::" + template
        else:
            # Fallback to saved config if not provided
            current_configs = config_manager.load_current_configs()
            if request.webhook_type not in current_configs:
                raise HTTPException(status_code=404, detail=f"Webhook type '{request.webhook_type}' not configured")
            config_line = current_configs[request.webhook_type]
        
        # Time the processing
        start_time = time.time()
        
        # Use the SAME logic as main.py webhook processing
        # Parse fields from config line
        fields_part, template = config_line.split('::', 1)
        
        # Parse fields carefully (same logic as main.py lines 93-130)
        fields = []
        current_field = ""
        brace_count = 0
        
        for char in fields_part:
            if char == '{':
                brace_count += 1
                current_field += char
            elif char == '}':
                brace_count -= 1
                current_field += char
            elif char == ',' and brace_count == 0:
                if current_field.strip():
                    field = current_field.strip()
                    # Handle compound fields like pull_request{title,user{login}}
                    if '{' in field and ',' in field[field.find('{'):field.rfind('}')]:
                        if field == 'pull_request{title,user{login}}':
                            fields.extend(['pull_request{title}', 'pull_request{user{login}}'])
                        else:
                            fields.append(field)
                    else:
                        fields.append(field)
                current_field = ""
            else:
                current_field += char
        
        # Don't forget the last field
        if current_field.strip():
            field = current_field.strip()
            if '{' in field and ',' in field[field.find('{'):field.rfind('}')]:
                if field == 'pull_request{title,user{login}}':
                    fields.extend(['pull_request{title}', 'pull_request{user{login}}'])
                else:
                    fields.append(field)
            else:
                fields.append(field)
        
        # Extract fields using the SAME function as main.py
        from ..core.extractor import extract_fields
        extracted_data = extract_fields(request.test_payload, fields)
        
        # Generate message using SAME logic as main.py (lines 136-142)
        message = template
        for key, value in extracted_data.items():
            if value is not None:
                message = message.replace(f"${key}$", str(value))
        
        # Replace any remaining unresolved variables with '-'
        # Use a specific pattern that looks for $word.word$ variable patterns
        message = re.sub(r'\$[a-zA-Z_][a-zA-Z0-9_.]*\$', '-', message)
        
        processing_time = (time.time() - start_time) * 1000
        
        return WebhookTestResponse(
            success=True,
            webhook_type=request.webhook_type,
            extracted_fields=extracted_data,
            generated_message=message,
            processing_time_ms=processing_time,
            error_message=None
        )
        
    except Exception as e:
        return WebhookTestResponse(
            success=False,
            webhook_type=request.webhook_type,
            extracted_fields={},
            generated_message="",
            processing_time_ms=0,
            error_message=str(e)
        )


@router.get("/api/generate-token")
async def generate_token(request: Request, prefix: str = None):
    """Generate a unique token for webhook authentication."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    # Load current configs to ensure uniqueness
    configurations = config_manager.load_current_configs()
    
    # Generate unique token
    token = generate_unique_token(configurations, prefix=prefix)
    
    # Get base URL dynamically from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    return {
        "success": True,
        "token": token,
        "example_url": f"{base_url}/webhook/{{service}}/{token}"
    }


@router.post("/api/save-config", response_model=ConfigSaveResponse)
async def save_config(request: ConfigSaveRequest, http_request: Request):
    """Save webhook configuration to file."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        # Build the config key with service_token format
        config_key = f"{request.webhook_type}_{request.token}"
        
        # Save the configuration with tokenized key
        success, backup_file, error_msg = config_manager.save_config(
            config_key,
            request.config_line,
            request.create_backup
        )
        
        if not success:
            return ConfigSaveResponse(
                success=False,
                webhook_type=request.webhook_type,
                token=request.token,
                webhook_url="",
                backup_file=None,
                service_restarted=False,
                error_message=error_msg
            )
        
        # Get base URL dynamically from request
        base_url = f"{http_request.url.scheme}://{http_request.url.netloc}"
        webhook_url = f"{base_url}/webhook/{request.webhook_type}/{request.token}"
        
        return ConfigSaveResponse(
            success=True,
            webhook_type=request.webhook_type,
            token=request.token,
            webhook_url=webhook_url,
            backup_file=backup_file,
            service_restarted=False,  # No restart needed - config is read dynamically
            error_message=None
        )
        
    except Exception as e:
        return ConfigSaveResponse(
            success=False,
            webhook_type=request.webhook_type,
            token=request.token,
            webhook_url="",
            backup_file=None,
            service_restarted=False,
            error_message=str(e)
        )


@router.get("/api/configs", response_model=ConfigListResponse)
async def list_configs():
    """List all current webhook configurations."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        configurations = config_manager.load_current_configs()
        
        return ConfigListResponse(
            success=True,
            configurations=configurations,
            total_count=len(configurations),
            error_message=None
        )
        
    except Exception as e:
        return ConfigListResponse(
            success=False,
            configurations={},
            total_count=0,
            error_message=str(e)
        )


@router.get("/api/config/{service}/{token}")
async def get_config(service: str, token: str, request: Request):
    """Get configuration for a specific service:token combination."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    configurations = config_manager.load_current_configs()
    
    # Build config key
    config_key = f"{service}_{token}"
    
    if config_key not in configurations:
        raise HTTPException(status_code=404, detail=f"Configuration '{config_key}' not found")
    
    config_line = configurations[config_key]
    fields_part, template = config_line.split('::', 1)
    fields = [f.strip() for f in fields_part.split(',')]
    
    # Get base URL dynamically from request
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    webhook_url = f"{base_url}/webhook/{service}/{token}"
    
    return {
        "webhook_type": service,
        "token": token,
        "config_key": config_key,
        "webhook_url": webhook_url,
        "fields": fields,
        "message_template": template,
        "config_line": config_line
    }


@router.delete("/api/config/{service}/{token}")
async def delete_config(service: str, token: str):
    """Delete a webhook configuration by service:token key."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        from configparser import ConfigParser
        
        config_file_path = config_manager.config_file_path
        
        if not config_file_path.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")
        
        config = ConfigParser()
        config.read(str(config_file_path))
        
        # Build config key
        config_key = f"{service}_{token}"
        
        if 'webhooks' not in config or config_key not in config['webhooks']:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_key}' not found")
        
        # Create backup before deletion
        if web_config.backup_configs:
            config_manager._create_backup()
        
        # Remove the configuration
        del config['webhooks'][config_key]
        
        # Write back to file
        with open(config_file_path, 'w') as f:
            config.write(f)
        
        return {"success": True, "message": f"Configuration '{config_key}' deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/web-config")
async def get_web_config():
    """Get web interface configuration settings."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    return {
        "backup_configs": web_config.backup_configs,
        "enable_config_validation": web_config.enable_config_validation,
        "enable_live_preview": web_config.enable_live_preview
    }


@router.get("/api/webhook-logs/{webhook_type}/recent")
async def get_recent_payloads(webhook_type: str, limit: int = 10):
    """Get recent webhook payloads for a specific webhook type."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    # Validate limit
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")
    
    webhook_logger = get_webhook_logger()
    if not webhook_logger or not webhook_logger.enabled:
        raise HTTPException(status_code=503, detail="Webhook logging is disabled")
    
    try:
        recent_payloads = webhook_logger.get_recent_payloads(webhook_type, limit)
        return {
            "success": True,
            "webhook_type": webhook_type,
            "payloads": recent_payloads,
            "count": len(recent_payloads)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving payloads: {str(e)}")


@router.get("/api/webhook-logs/types")
async def get_available_webhook_types():
    """Get list of webhook types that have logged payloads."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    webhook_logger = get_webhook_logger()
    if not webhook_logger or not webhook_logger.enabled:
        return {"success": True, "webhook_types": [], "count": 0}
    
    try:
        webhook_types = webhook_logger.get_available_webhook_types()
        return {
            "success": True,
            "webhook_types": webhook_types,
            "count": len(webhook_types)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving webhook types: {str(e)}")