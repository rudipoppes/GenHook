"""
FastAPI routes for the web configuration interface.
"""
import json
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
    """Test webhook configuration with sample payload."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        from ..core.extractor import FieldExtractor
        import time
        
        # Load current config for the webhook type
        current_configs = config_manager.load_current_configs()
        if request.webhook_type not in current_configs:
            raise HTTPException(status_code=404, detail=f"Webhook type '{request.webhook_type}' not configured")
        
        config_line = current_configs[request.webhook_type]
        fields_part, template = config_line.split('::', 1)
        fields = [f.strip() for f in fields_part.split(',')]
        
        # Time the extraction
        start_time = time.time()
        
        # Extract fields
        extractor = FieldExtractor()
        extracted_data = extractor.extract_for_template(request.test_payload, fields)
        
        # Generate message
        message = template
        for key, value in extracted_data.items():
            if value is not None:
                message = message.replace(f"${key}$", str(value))
        
        processing_time = (time.time() - start_time) * 1000
        
        return WebhookTestResponse(
            success=True,
            webhook_type=request.webhook_type,
            extracted_fields=extracted_data,
            generated_message=message,
            processing_time_ms=processing_time
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


@router.post("/api/save-config", response_model=ConfigSaveResponse)
async def save_config(request: ConfigSaveRequest):
    """Save webhook configuration to file."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        # Save the configuration
        success, backup_file, error_msg = config_manager.save_config(
            request.webhook_type,
            request.config_line,
            request.create_backup
        )
        
        if not success:
            return ConfigSaveResponse(
                success=False,
                webhook_type=request.webhook_type,
                error_message=error_msg
            )
        
        # Restart service if requested
        service_restarted = False
        if request.restart_service:
            restart_success, restart_error = config_manager.restart_service()
            if restart_success:
                service_restarted = True
            else:
                # Configuration was saved but service restart failed
                return ConfigSaveResponse(
                    success=False,
                    webhook_type=request.webhook_type,
                    backup_file=backup_file,
                    service_restarted=False,
                    error_message=f"Config saved but service restart failed: {restart_error}"
                )
        
        return ConfigSaveResponse(
            success=True,
            webhook_type=request.webhook_type,
            backup_file=backup_file,
            service_restarted=service_restarted
        )
        
    except Exception as e:
        return ConfigSaveResponse(
            success=False,
            webhook_type=request.webhook_type,
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
            total_count=len(configurations)
        )
        
    except Exception as e:
        return ConfigListResponse(
            success=False,
            configurations={},
            total_count=0,
            error_message=str(e)
        )


@router.get("/api/config/{webhook_type}")
async def get_config(webhook_type: str):
    """Get configuration for a specific webhook type."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    configurations = config_manager.load_current_configs()
    
    if webhook_type not in configurations:
        raise HTTPException(status_code=404, detail=f"Webhook type '{webhook_type}' not found")
    
    config_line = configurations[webhook_type]
    fields_part, template = config_line.split('::', 1)
    fields = [f.strip() for f in fields_part.split(',')]
    
    return {
        "webhook_type": webhook_type,
        "fields": fields,
        "message_template": template,
        "config_line": config_line
    }


@router.delete("/api/config/{webhook_type}")
async def delete_config(webhook_type: str):
    """Delete a webhook configuration."""
    if not web_config.enabled:
        raise HTTPException(status_code=404, detail="Web interface disabled")
    
    try:
        from configparser import ConfigParser
        
        config_file_path = config_manager.config_file_path
        
        if not config_file_path.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")
        
        config = ConfigParser()
        config.read(str(config_file_path))
        
        if 'webhooks' not in config or webhook_type not in config['webhooks']:
            raise HTTPException(status_code=404, detail=f"Webhook type '{webhook_type}' not found")
        
        # Create backup before deletion
        if web_config.backup_configs:
            config_manager._create_backup()
        
        # Remove the webhook type
        del config['webhooks'][webhook_type]
        
        # Write back to file
        with open(config_file_path, 'w') as f:
            config.write(f)
        
        # Restart service if configured
        if web_config.auto_restart_service:
            config_manager.restart_service()
        
        return {"success": True, "message": f"Webhook type '{webhook_type}' deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))