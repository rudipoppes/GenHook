"""
Quick inline test of the configuration system.
"""
import sys
import os
from pathlib import Path

# Add parent directories to path
current_dir = Path(__file__).parent
backend_dir = current_dir.parent.parent
sys.path.insert(0, str(backend_dir))

try:
    from app.models.webhook import WebhookConfig
    print("✅ Successfully imported WebhookConfig")
    
    # Test webhook config parsing
    test_config = "action,user{name}::User $user.name$ did $action$"
    webhook_config = WebhookConfig.from_config_line("test", test_config)
    print(f"✅ Parsed webhook config: {webhook_config.fields} -> {webhook_config.template}")
    
    # Test config file paths
    config_dir = backend_dir / "config"
    webhook_config_path = config_dir / "webhook-config.ini"
    app_config_path = config_dir / "app-config.ini"
    
    print(f"📁 Config directory: {config_dir}")
    print(f"📄 Webhook config exists: {webhook_config_path.exists()}")
    print(f"📄 App config exists: {app_config_path.exists()}")
    
    if webhook_config_path.exists() and app_config_path.exists():
        from app.core.config import ConfigManager
        config_manager = ConfigManager(str(webhook_config_path), str(app_config_path))
        print(f"✅ ConfigManager created successfully!")
        print(f"📝 Loaded {len(config_manager.webhook_configs)} webhook types")
        print(f"🌐 SL1 URL: {config_manager.sl1_config.api_url}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()