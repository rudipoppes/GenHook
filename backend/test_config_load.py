#!/usr/bin/env python3
"""
Test script to verify configuration loading works with actual config files.
"""
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import create_config_manager, ConfigError


def main():
    """Test configuration loading."""
    try:
        print("🔧 Testing GenHook Configuration System...")
        
        # Create config manager
        config_manager = create_config_manager()
        
        print("\n✅ Configuration loaded successfully!")
        
        # Display webhook configurations
        print(f"\n📝 Loaded {len(config_manager.webhook_configs)} webhook types:")
        for webhook_type in config_manager.list_webhook_types():
            config = config_manager.get_webhook_config(webhook_type)
            print(f"  • {webhook_type}: {len(config.fields)} fields -> {config.template[:50]}...")
        
        # Display SL1 configuration
        sl1_config = config_manager.sl1_config
        print(f"\n🌐 SL1 Configuration:")
        print(f"  • URL: {sl1_config.api_url}")
        print(f"  • Username: {sl1_config.username}")
        print(f"  • Password: {'*' * len(sl1_config.password)}")
        print(f"  • Timeout: {sl1_config.timeout}s")
        print(f"  • Retry attempts: {sl1_config.retry_attempts}")
        
        # Display server configuration  
        server_config = config_manager.server_config
        print(f"\n🖥️  Server Configuration:")
        print(f"  • Host: {server_config.host}")
        print(f"  • Port: {server_config.port}")
        print(f"  • Reload: {server_config.reload}")
        
        # Test specific webhook config parsing
        print(f"\n🔍 Testing GitHub webhook config:")
        github_config = config_manager.get_webhook_config('github')
        if github_config:
            print(f"  • Fields: {github_config.fields}")
            print(f"  • Template: {github_config.template}")
        else:
            print("  ❌ GitHub config not found")
        
        print(f"\n🎉 Configuration system test completed successfully!")
        
    except ConfigError as e:
        print(f"❌ Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()