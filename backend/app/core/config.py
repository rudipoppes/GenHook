"""
Configuration management for GenHook.
Loads and validates configuration from INI files.
"""
import os
from configparser import ConfigParser
from typing import Dict, List, Optional
from pathlib import Path

from app.models.webhook import (
    WebhookConfig, 
    AppConfig, 
    SL1Config, 
    ServerConfig, 
    LoggingConfig, 
    ThreadingConfig
)


class ConfigManager:
    """Manages all configuration for GenHook."""
    
    def __init__(self, webhook_config_path: str, app_config_path: str):
        """
        Initialize configuration manager.
        
        Args:
            webhook_config_path: Path to webhook-config.ini
            app_config_path: Path to app-config.ini
        """
        self.webhook_configs: Dict[str, WebhookConfig] = {}
        self.app_config: Optional[AppConfig] = None
        
        self._load_configs(webhook_config_path, app_config_path)
    
    def _load_configs(self, webhook_config_path: str, app_config_path: str):
        """Load both configuration files."""
        try:
            self._load_webhook_configs(webhook_config_path)
            self._load_app_config(app_config_path)
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")
    
    def _load_webhook_configs(self, config_path: str):
        """Load webhook configurations from INI file."""
        if not os.path.exists(config_path):
            raise ConfigError(f"Webhook config file not found: {config_path}")
        
        parser = ConfigParser()
        parser.read(config_path)
        
        if 'webhooks' not in parser:
            raise ConfigError("Missing [webhooks] section in webhook config")
        
        webhooks_section = parser['webhooks']
        
        for webhook_type in webhooks_section:
            config_line = webhooks_section[webhook_type]
            try:
                webhook_config = WebhookConfig.from_config_line(webhook_type, config_line)
                self.webhook_configs[webhook_type] = webhook_config
                print(f"Loaded config for webhook type: {webhook_type}")
            except ValueError as e:
                print(f"Warning: Skipping invalid webhook config - {e}")
        
        if not self.webhook_configs:
            raise ConfigError("No valid webhook configurations found")
    
    def _load_app_config(self, config_path: str):
        """Load application configuration from INI file."""
        if not os.path.exists(config_path):
            raise ConfigError(f"App config file not found: {config_path}")
        
        parser = ConfigParser()
        parser.read(config_path)
        
        # Load server config
        server_section = parser['server'] if 'server' in parser else {}
        server_config = ServerConfig(
            host=server_section.get('host', '0.0.0.0'),
            port=int(server_section.get('port', 8000)),
            reload=server_section.getboolean('reload', True) if 'reload' in server_section else True
        )
        
        # Load SL1 config (required)
        if 'sl1' not in parser:
            raise ConfigError("Missing [sl1] section in app config")
        
        sl1_section = parser['sl1']
        required_sl1_fields = ['api_url', 'username', 'password']
        missing_fields = [field for field in required_sl1_fields if field not in sl1_section]
        
        if missing_fields:
            raise ConfigError(f"Missing required SL1 config fields: {missing_fields}")
        
        sl1_config = SL1Config(
            api_url=sl1_section['api_url'],
            username=sl1_section['username'],
            password=sl1_section['password'],
            timeout=int(sl1_section.get('timeout', 30)),
            retry_attempts=int(sl1_section.get('retry_attempts', 3))
        )
        
        # Load logging config
        if 'logging' in parser:
            logging_section = parser['logging']
            logging_config = LoggingConfig(
                level=logging_section.get('level', 'INFO'),
                format=parser.get('logging', 'format', raw=True, fallback='%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                file=logging_section.get('file')
            )
        else:
            logging_config = LoggingConfig(
                level='INFO',
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                file=None
            )
        
        # Load threading config
        threading_section = parser['threading'] if 'threading' in parser else {}
        threading_config = ThreadingConfig(
            max_workers=int(threading_section.get('max_workers', 50)),
            queue_size=int(threading_section.get('queue_size', 10000)),
            processing_timeout=int(threading_section.get('processing_timeout', 30))
        )
        
        self.app_config = AppConfig(
            server=server_config,
            sl1=sl1_config,
            logging=logging_config,
            threading=threading_config
        )
        
        print(f"Loaded app config - SL1 URL: {sl1_config.api_url}")
    
    def get_webhook_config(self, webhook_type: str) -> Optional[WebhookConfig]:
        """Get configuration for a specific webhook type."""
        return self.webhook_configs.get(webhook_type)
    
    def list_webhook_types(self) -> List[str]:
        """Get all configured webhook types."""
        return list(self.webhook_configs.keys())
    
    @property
    def sl1_config(self) -> SL1Config:
        """Get SL1 configuration."""
        return self.app_config.sl1
    
    @property
    def server_config(self) -> ServerConfig:
        """Get server configuration."""
        return self.app_config.server
    
    @property
    def logging_config(self) -> LoggingConfig:
        """Get logging configuration."""
        return self.app_config.logging
    
    @property
    def threading_config(self) -> ThreadingConfig:
        """Get threading configuration."""
        return self.app_config.threading


class ConfigError(Exception):
    """Configuration-related errors."""
    pass


def create_config_manager() -> ConfigManager:
    """
    Create a ConfigManager with default paths.
    Looks for config files relative to the backend directory.
    """
    backend_dir = Path(__file__).parent.parent.parent  # Go up to backend/
    webhook_config_path = backend_dir / "config" / "webhook-config.ini"
    app_config_path = backend_dir / "config" / "app-config.ini"
    
    return ConfigManager(str(webhook_config_path), str(app_config_path))

# Global config manager instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = create_config_manager()
    return _config_manager

def get_config():
    """Get the raw ConfigParser for backward compatibility."""
    from configparser import ConfigParser
    import os
    
    config = ConfigParser()
    backend_dir = Path(__file__).parent.parent.parent
    
    # Auto-detect environment: production config takes precedence if it exists
    prod_config_path = backend_dir / "config" / "app-config.prod.ini"
    dev_config_path = backend_dir / "config" / "app-config.ini"
    
    if prod_config_path.exists():
        config.read(str(prod_config_path))
        print(f"✅ Using production config: {prod_config_path}")
    else:
        config.read(str(dev_config_path))
        print(f"✅ Using development config: {dev_config_path}")
    
    return config

def get_webhook_config():
    """Get webhook configurations as a simple dict for backward compatibility."""
    from configparser import ConfigParser
    config = ConfigParser()
    backend_dir = Path(__file__).parent.parent.parent
    webhook_config_path = backend_dir / "config" / "webhook-config.ini"
    config.read(str(webhook_config_path))
    
    if 'webhooks' in config:
        return dict(config['webhooks'])
    return {}