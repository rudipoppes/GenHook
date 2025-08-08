"""
Web interface business logic and services.
"""
import json
import logging
import os
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.extractor import FieldExtractor
from .config import get_web_config
from .models import FieldInfo, PayloadAnalysisResponse, ConfigGenerationResponse

logger = logging.getLogger(__name__)


class PayloadAnalyzer:
    """Analyzes JSON payloads to discover extractable fields."""
    
    def __init__(self):
        self.config = get_web_config()
    
    def analyze_payload(self, payload: Dict[str, Any], webhook_type: Optional[str] = None) -> PayloadAnalysisResponse:
        """
        Analyze a JSON payload to discover all extractable fields.
        
        Args:
            payload: JSON payload to analyze
            webhook_type: Optional webhook type hint
            
        Returns:
            PayloadAnalysisResponse with discovered fields
        """
        try:
            # Discover fields including nested ones (but limit depth)
            fields = []
            self._discover_fields_recursive(payload, fields, "", "", 0)
            
            # Limit to prevent UI overload
            fields = fields[:20]
            
            response = PayloadAnalysisResponse(
                success=True,
                webhook_type=webhook_type,
                total_fields=len(fields),
                fields=fields,
                error_message=None
            )
            return response
            
        except TimeoutError:
            return PayloadAnalysisResponse(
                success=False,
                webhook_type=webhook_type,
                total_fields=0,
                fields=[],
                error_message="Analysis timed out - payload too complex"
            )
        except Exception as e:
            return PayloadAnalysisResponse(
                success=False,
                webhook_type=webhook_type,
                total_fields=0,
                fields=[],
                error_message=str(e)
            )
    
    def _discover_fields_recursive(self, data: Any, fields_list: List[FieldInfo], path: str = "", pattern: str = "", depth: int = 0) -> None:
        """
        Recursively discover ONLY leaf node fields (fields with actual extractable values).
        Skips intermediate object containers to show only useful fields.
        """
        # Limit depth to prevent infinite recursion
        if depth > 3:
            return
            
        if isinstance(data, dict):
            for key, value in list(data.items())[:15]:  # Limit items per level
                new_path = f"{path}.{key}" if path else key
                new_pattern = f"{pattern}{{{key}}}" if pattern else key
                
                
                try:
                    # Only add leaf nodes (fields with actual values)
                    if self._is_leaf_node(value):
                        field_info = FieldInfo(
                            path=new_path,
                            pattern=new_pattern,
                            field_type=self._get_field_type(value),
                            sample_value=self._get_sample_value(value),
                            is_array=isinstance(value, list),
                            array_length=len(value) if isinstance(value, list) else None,
                            children=None
                        )
                        
                        fields_list.append(field_info)
                    
                    # Continue recursing into nested structures
                    if isinstance(value, dict) and depth < 3:
                        self._discover_fields_recursive(value, fields_list, new_path, new_pattern, depth + 1)
                    elif isinstance(value, list) and value and depth < 3:
                        # For arrays, analyze the first item to find leaf fields within
                        first_item = value[0] if value else None
                        if isinstance(first_item, dict):
                            self._discover_fields_recursive(first_item, fields_list, new_path, new_pattern, depth + 1)
                        
                except Exception as e:
                    continue
    
    def _is_leaf_node(self, value: Any) -> bool:
        """
        Determine if a field is a leaf node (contains extractable value).
        
        Leaf nodes are:
        - Primitive values: strings, numbers, booleans, null
        - Arrays of primitives
        - NOT nested objects or arrays of objects (these are containers)
        """
        if value is None:
            return True  # null values are leaf nodes
        elif isinstance(value, (str, int, float, bool)):
            return True  # Primitive values are leaf nodes
        elif isinstance(value, list):
            # Arrays are leaf nodes if they contain primitives
            if not value:  # Empty array
                return True
            first_item = value[0]
            # If first item is primitive, treat as leaf node
            return isinstance(first_item, (str, int, float, bool, type(None)))
        elif isinstance(value, dict):
            return False  # Objects are containers, not leaf nodes
        else:
            return True  # Other types (rare) are treated as leaf nodes
    
    def _get_field_type(self, value: Any) -> str:
        """Determine the type of a field value."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "number"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"
    
    def _get_sample_value(self, value: Any) -> Any:
        """Get a sample value for display, truncating if too long."""
        if value is None:
            return None
        elif isinstance(value, str):
            return value[:100] + "..." if len(value) > 100 else value
        elif isinstance(value, list):
            return f"[{len(value)} items]"
        elif isinstance(value, dict):
            return f"{{object with {len(value)} fields}}"
        else:
            return value


class ConfigGenerator:
    """Generates webhook configurations from selected fields."""
    
    def __init__(self):
        self.config = get_web_config()
        self.extractor = FieldExtractor()
    
    def generate_config(
        self, 
        webhook_type: str, 
        selected_fields: List[str], 
        message_template: str,
        test_payload: Optional[Dict[str, Any]] = None
    ) -> ConfigGenerationResponse:
        """
        Generate webhook configuration from selected fields.
        
        Args:
            webhook_type: Name of the webhook type
            selected_fields: List of field patterns to extract
            message_template: Message template with variables
            test_payload: Optional payload for preview generation
            
        Returns:
            ConfigGenerationResponse with generated config
        """
        try:
            # Build configuration line
            fields_str = ",".join(selected_fields)
            config_line = f"{fields_str}::{message_template}"
            
            # Generate preview if test payload provided
            preview_message = message_template
            if test_payload:
                preview_message = self._generate_preview(
                    test_payload, selected_fields, message_template
                )
            
            return ConfigGenerationResponse(
                success=True,
                webhook_type=webhook_type,
                config_line=config_line,
                preview_message=preview_message,
                error_message=None
            )
            
        except Exception as e:
            return ConfigGenerationResponse(
                success=False,
                webhook_type=webhook_type,
                config_line="",
                preview_message="",
                error_message=str(e)
            )
    
    def _generate_preview(
        self, 
        payload: Dict[str, Any], 
        selected_fields: List[str], 
        template: str
    ) -> str:
        """Generate a preview message using the test payload."""
        try:
            # Extract fields using the field extractor
            extracted_data = self.extractor.extract_for_template(payload, selected_fields)
            
            # Replace template variables
            message = template
            for key, value in extracted_data.items():
                if value is not None:
                    # Use both the pattern and simplified key
                    message = message.replace(f"${key}$", str(value))
            
            return message
            
        except Exception as e:
            return f"Preview error: {str(e)}"


class ConfigManager:
    """Manages webhook configuration files."""
    
    def __init__(self):
        self.config = get_web_config()
        self.backend_dir = Path(__file__).parent.parent.parent
        self.config_file_path = self.backend_dir / self.config.config_file_path
        self.backup_dir = self.backend_dir / self.config.backup_directory
    
    def load_current_configs(self) -> Dict[str, str]:
        """Load current webhook configurations."""
        try:
            from configparser import ConfigParser
            config = ConfigParser()
            
            if self.config_file_path.exists():
                config.read(str(self.config_file_path))
                if 'webhooks' in config:
                    return dict(config['webhooks'])
            
            return {}
            
        except Exception as e:
            return {}
    
    def save_config(
        self, 
        webhook_type: str, 
        config_line: str, 
        create_backup: bool = True
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save webhook configuration.
        
        Args:
            webhook_type: Webhook type name
            config_line: Configuration line to save
            create_backup: Whether to create backup
            
        Returns:
            Tuple of (success, backup_file, error_message)
        """
        try:
            backup_file = None
            
            # Create backup if requested
            if create_backup and self.config_file_path.exists():
                try:
                    backup_file = self._create_backup()
                except Exception as e:
                    # Continue without backup
                    pass
            
            # Load current config
            from configparser import ConfigParser
            config = ConfigParser()
            if self.config_file_path.exists():
                config.read(str(self.config_file_path))
            
            # Ensure webhooks section exists
            if 'webhooks' not in config:
                config['webhooks'] = {}
            
            # Update the specific webhook type
            config['webhooks'][webhook_type] = config_line
            
            # Write back to file with explicit error handling
            try:
                with open(self.config_file_path, 'w') as f:
                    config.write(f)
            except Exception as write_error:
                return False, backup_file, f"Failed to write config file: {str(write_error)}"
            
            return True, backup_file, None
            
        except Exception as e:
            return False, None, str(e)
    
    def _create_backup(self) -> str:
        """Create a backup of the current config file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"webhook-config_{timestamp}.ini.bak"
            
            # Ensure backup directory exists
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_path = self.backup_dir / backup_filename
            shutil.copy2(self.config_file_path, backup_path)
            
            return str(backup_path)
        except Exception as e:
            raise
    
