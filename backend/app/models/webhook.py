"""
Webhook data models and configuration structures.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WebhookConfig:
    """Configuration for a specific webhook type."""
    webhook_type: str
    fields: List[str]  # Field extraction patterns like ['action', 'user{name}']
    template: str      # Message template like "User $user.name$ performed $action$"
    
    @classmethod
    def from_config_line(cls, webhook_type: str, config_line: str) -> 'WebhookConfig':
        """
        Parse configuration line format:
        field1,field2,nested{subfield}::Message template with $variables$
        """
        try:
            parts = config_line.split('::', 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid config format for {webhook_type}: missing '::' separator")
            
            fields_str, template = parts
            fields = [field.strip() for field in fields_str.split(',') if field.strip()]
            
            if not fields:
                raise ValueError(f"No fields specified for {webhook_type}")
            
            if not template.strip():
                raise ValueError(f"No template specified for {webhook_type}")
            
            return cls(
                webhook_type=webhook_type,
                fields=fields,
                template=template.strip()
            )
        except Exception as e:
            raise ValueError(f"Failed to parse config for {webhook_type}: {e}")


@dataclass 
class SL1Config:
    """SL1 API configuration."""
    api_url: str
    username: str
    password: str
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None


@dataclass
class ThreadingConfig:
    """Threading configuration."""
    max_workers: int = 50
    queue_size: int = 10000
    processing_timeout: int = 30


@dataclass
class AppConfig:
    """Complete application configuration."""
    server: ServerConfig
    sl1: SL1Config
    logging: LoggingConfig
    threading: ThreadingConfig