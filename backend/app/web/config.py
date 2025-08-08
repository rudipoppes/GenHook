"""
Web interface configuration management.
"""
import os
from configparser import ConfigParser
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


class WebConfig(BaseModel):
    """Web interface configuration settings."""
    
    # Web settings
    enabled: bool = True
    base_path: str = "/config"
    static_path: str = "/static"
    template_path: str = "templates/"
    
    # Security settings
    require_auth: bool = False
    allowed_ips: List[str] = ["127.0.0.1", "192.168.0.0/16"]
    max_payload_size: str = "10MB"
    session_timeout: int = 3600
    
    # Feature flags
    backup_configs: bool = True
    backup_retention_days: int = 30
    enable_config_validation: bool = True
    enable_live_preview: bool = True
    
    # Service integration
    config_file_path: str = "config/webhook-config.ini"
    backup_directory: str = "backups/configs/"
    
    # UI settings
    theme: str = "default"
    show_sample_values: bool = True
    max_fields_display: int = 100
    default_message_template: str = "$service$ Alert: $summary$"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = "/var/log/genhook/web-interface.log"
    enable_access_log: bool = True


def load_web_config(config_path: Optional[str] = None) -> WebConfig:
    """
    Load web interface configuration from INI file.
    
    Args:
        config_path: Path to web-config.ini file. If None, uses default location.
        
    Returns:
        WebConfig instance with loaded settings.
    """
    if config_path is None:
        # Auto-detect environment: production config takes precedence if it exists
        backend_dir = Path(__file__).parent.parent.parent
        prod_config_path = backend_dir / "config" / "web-config.prod.ini"
        dev_config_path = backend_dir / "config" / "web-config.ini"
        
        if prod_config_path.exists():
            config_path = str(prod_config_path)
            print(f"✅ Loaded web interface config from: {prod_config_path}")
        else:
            config_path = str(dev_config_path)
            print(f"✅ Loaded web interface config from: {dev_config_path}")
    
    config = ConfigParser()
    
    # Set defaults
    config_dict = {}
    
    if os.path.exists(config_path):
        config.read(str(config_path))
        
        # Web section
        if 'web' in config:
            web_section = config['web']
            config_dict.update({
                'enabled': web_section.getboolean('enabled', True),
                'base_path': web_section.get('base_path', '/config'),
                'static_path': web_section.get('static_path', '/static'),
                'template_path': web_section.get('template_path', 'templates/'),
            })
        
        # Security section
        if 'security' in config:
            security_section = config['security']
            allowed_ips = security_section.get('allowed_ips', '127.0.0.1,192.168.0.0/16')
            config_dict.update({
                'require_auth': security_section.getboolean('require_auth', False),
                'allowed_ips': [ip.strip() for ip in allowed_ips.split(',')],
                'max_payload_size': security_section.get('max_payload_size', '10MB'),
                'session_timeout': security_section.getint('session_timeout', 3600),
            })
        
        # Features section
        if 'features' in config:
            features_section = config['features']
            config_dict.update({
                'backup_configs': features_section.getboolean('backup_configs', True),
                'backup_retention_days': features_section.getint('backup_retention_days', 30),
                'enable_config_validation': features_section.getboolean('enable_config_validation', True),
                'enable_live_preview': features_section.getboolean('enable_live_preview', True),
            })
        
        # Service section
        if 'service' in config:
            service_section = config['service']
            config_dict.update({
                'config_file_path': service_section.get('config_file_path', 'config/webhook-config.ini'),
                'backup_directory': service_section.get('backup_directory', 'backups/configs/'),
            })
        
        # UI section
        if 'ui' in config:
            ui_section = config['ui']
            config_dict.update({
                'theme': ui_section.get('theme', 'default'),
                'show_sample_values': ui_section.getboolean('show_sample_values', True),
                'max_fields_display': ui_section.getint('max_fields_display', 100),
                'default_message_template': ui_section.get('default_message_template', '$service$ Alert: $summary$'),
            })
        
        # Logging section
        if 'logging' in config:
            logging_section = config['logging']
            config_dict.update({
                'log_level': logging_section.get('log_level', 'INFO'),
                'log_file': logging_section.get('log_file'),
                'enable_access_log': logging_section.getboolean('enable_access_log', True),
            })
        
        print(f"✅ Loaded web interface config from: {config_path}")
    else:
        print(f"⚠️  Web config file not found: {config_path}, using defaults")
    
    return WebConfig(**config_dict)


# Global web config instance
_web_config = None


def get_web_config() -> WebConfig:
    """Get the global web configuration instance."""
    global _web_config
    if _web_config is None:
        _web_config = load_web_config()
    return _web_config