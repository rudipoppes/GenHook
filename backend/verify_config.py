#!/usr/bin/env python3
"""
Manual verification of configuration files and parsing.
"""
from configparser import ConfigParser
import os

def verify_webhook_config():
    """Verify webhook configuration file."""
    config_path = "config/webhook-config.ini"
    print(f"🔍 Checking webhook config: {config_path}")
    
    if not os.path.exists(config_path):
        print(f"❌ File not found: {config_path}")
        return False
    
    parser = ConfigParser()
    try:
        parser.read(config_path)
        print(f"✅ Successfully parsed webhook config")
        
        if 'webhooks' in parser:
            webhooks = parser['webhooks']
            print(f"📝 Found {len(webhooks)} webhook types:")
            for webhook_type in webhooks:
                config_line = webhooks[webhook_type]
                print(f"  • {webhook_type}: {config_line[:50]}...")
                
                # Test parsing
                if '::' in config_line:
                    fields_str, template = config_line.split('::', 1)
                    fields = [f.strip() for f in fields_str.split(',') if f.strip()]
                    print(f"    - Fields: {fields}")
                    print(f"    - Template: {template[:30]}...")
                else:
                    print(f"    ❌ Invalid format (missing '::')")
            return True
        else:
            print("❌ Missing [webhooks] section")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing webhook config: {e}")
        return False

def verify_app_config():
    """Verify app configuration file."""
    config_path = "config/app-config.ini"
    print(f"\n🔍 Checking app config: {config_path}")
    
    if not os.path.exists(config_path):
        print(f"❌ File not found: {config_path}")
        return False
    
    parser = ConfigParser()
    try:
        parser.read(config_path)
        print(f"✅ Successfully parsed app config")
        
        # Check required sections
        sections = ['server', 'sl1', 'logging', 'threading']
        for section in sections:
            if section in parser:
                print(f"✅ Found [{section}] section")
                if section == 'sl1':
                    sl1 = parser['sl1']
                    print(f"  • API URL: {sl1.get('api_url', 'MISSING')}")
                    print(f"  • Username: {sl1.get('username', 'MISSING')}")
                    print(f"  • Password: {'*' * len(sl1.get('password', ''))}")
            else:
                print(f"❌ Missing [{section}] section")
        
        return True
        
    except Exception as e:
        print(f"❌ Error parsing app config: {e}")
        return False

def main():
    """Main verification function."""
    print("🔧 GenHook Configuration Verification\n")
    
    webhook_ok = verify_webhook_config()
    app_ok = verify_app_config()
    
    if webhook_ok and app_ok:
        print(f"\n🎉 All configuration files verified successfully!")
    else:
        print(f"\n❌ Configuration verification failed!")

if __name__ == "__main__":
    main()