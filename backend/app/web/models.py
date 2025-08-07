"""
Pydantic models for the web interface.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class PayloadAnalysisRequest(BaseModel):
    """Request model for payload analysis."""
    
    payload: Dict[str, Any] = Field(..., description="JSON payload to analyze")
    webhook_type: Optional[str] = Field(None, description="Optional webhook type hint")


class FieldInfo(BaseModel):
    """Information about a discovered field."""
    
    path: str = Field(..., description="Field path (e.g., 'user.name')")
    pattern: str = Field(..., description="GenHook extraction pattern (e.g., 'user{name}')")
    field_type: str = Field(..., description="Field type: string, number, boolean, object, array")
    sample_value: Any = Field(None, description="Sample value from the payload")
    is_array: bool = Field(False, description="Whether this field contains array data")
    array_length: Optional[int] = Field(None, description="Array length if is_array=True")
    children: Optional[List['FieldInfo']] = Field(None, description="Child fields for objects/arrays")


class PayloadAnalysisResponse(BaseModel):
    """Response model for payload analysis."""
    
    success: bool = Field(..., description="Whether analysis was successful")
    webhook_type: Optional[str] = Field(None, description="Detected or provided webhook type")
    total_fields: int = Field(..., description="Total number of discoverable fields")
    fields: List[FieldInfo] = Field(..., description="Discovered field information")
    error_message: Optional[str] = Field(None, description="Error message if success=False")


class ConfigGenerationRequest(BaseModel):
    """Request model for generating webhook configuration."""
    
    webhook_type: str = Field(..., description="Webhook type name")
    selected_fields: List[str] = Field(..., description="Selected field patterns")
    message_template: str = Field(..., description="Message template with variables")
    
    @validator('webhook_type')
    def validate_webhook_type(cls, v):
        # Basic validation for webhook type name
        if not v or not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Webhook type must be alphanumeric with underscores or hyphens')
        return v.lower()
    
    @validator('selected_fields')
    def validate_selected_fields(cls, v):
        if not v:
            raise ValueError('At least one field must be selected')
        return v
    
    @validator('message_template')
    def validate_message_template(cls, v):
        if not v or not v.strip():
            raise ValueError('Message template cannot be empty')
        return v.strip()


class ConfigGenerationResponse(BaseModel):
    """Response model for configuration generation."""
    
    success: bool = Field(..., description="Whether generation was successful")
    webhook_type: str = Field(..., description="Webhook type name")
    config_line: str = Field(..., description="Generated configuration line")
    preview_message: str = Field(..., description="Preview of generated message")
    error_message: Optional[str] = Field(None, description="Error message if success=False")


class ConfigSaveRequest(BaseModel):
    """Request model for saving webhook configuration."""
    
    webhook_type: str = Field(..., description="Webhook type name")
    config_line: str = Field(..., description="Configuration line to save")
    create_backup: bool = Field(True, description="Whether to create backup before saving")
    restart_service: bool = Field(True, description="Whether to restart service after saving")


class ConfigSaveResponse(BaseModel):
    """Response model for saving configuration."""
    
    success: bool = Field(..., description="Whether save was successful")
    webhook_type: str = Field(..., description="Webhook type name")
    backup_file: Optional[str] = Field(None, description="Backup file path if created")
    service_restarted: bool = Field(False, description="Whether service was restarted")
    error_message: Optional[str] = Field(None, description="Error message if success=False")


class WebhookTestRequest(BaseModel):
    """Request model for testing webhook configuration."""
    
    webhook_type: str = Field(..., description="Webhook type name")
    test_payload: Dict[str, Any] = Field(..., description="Test payload to process")


class WebhookTestResponse(BaseModel):
    """Response model for webhook testing."""
    
    success: bool = Field(..., description="Whether test was successful")
    webhook_type: str = Field(..., description="Webhook type name")
    extracted_fields: Dict[str, Any] = Field(..., description="Extracted field values")
    generated_message: str = Field(..., description="Generated message")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if success=False")


class ConfigListResponse(BaseModel):
    """Response model for listing webhook configurations."""
    
    success: bool = Field(..., description="Whether listing was successful")
    configurations: Dict[str, str] = Field(..., description="Webhook type -> config line mapping")
    total_count: int = Field(..., description="Total number of configurations")
    error_message: Optional[str] = Field(None, description="Error message if success=False")


# Update forward references for recursive models
FieldInfo.model_rebuild()