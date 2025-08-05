"""
Tests for configuration system.
"""
import unittest
import tempfile
import os
from pathlib import Path

from app.core.config import ConfigManager, ConfigError
from app.models.webhook import WebhookConfig


class TestConfigManager(unittest.TestCase):
    """Test configuration management."""
    
    def setUp(self):
        """Create temporary config files for testing."""
        # Create webhook config
        self.webhook_config_content = """
[webhooks]
github = action,pull_request{title,user{login}},repository{name}::GitHub $action$ on $repository.name$: "$pull_request.title$" by $pull_request.user.login$
slack = event{type,user,text}::Slack $event.type$ from user $event.user$: "$event.text$"
"""
        
        # Create app config
        self.app_config_content = """
[server]
host = 0.0.0.0
port = 8000
reload = true

[sl1]
api_url = http://test.example.com/api
username = testuser
password = testpass
timeout = 30
retry_attempts = 3

[logging]
level = INFO
format = %(asctime)s - %(name)s - %(levelname)s - %(message)s

[threading]
max_workers = 50
queue_size = 10000
processing_timeout = 30
"""
        
        # Create temporary files
        self.webhook_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.webhook_config_file.write(self.webhook_config_content)
        self.webhook_config_file.close()
        
        self.app_config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
        self.app_config_file.write(self.app_config_content)
        self.app_config_file.close()
    
    def tearDown(self):
        """Clean up temporary files."""
        os.unlink(self.webhook_config_file.name)
        os.unlink(self.app_config_file.name)
    
    def test_load_valid_config(self):
        """Test loading valid configuration."""
        config_manager = ConfigManager(
            self.webhook_config_file.name,
            self.app_config_file.name
        )
        
        # Test webhook configs
        self.assertEqual(len(config_manager.webhook_configs), 2)
        self.assertIn('github', config_manager.webhook_configs)
        self.assertIn('slack', config_manager.webhook_configs)
        
        # Test GitHub config
        github_config = config_manager.get_webhook_config('github')
        self.assertIsNotNone(github_config)
        if github_config is not None:  # Type guard for mypy/IDE
            self.assertEqual(github_config.webhook_type, 'github')
            self.assertIn('action', github_config.fields)
            # Note: compound fields get split, so we check for the components
            self.assertIn('pull_request{title', github_config.fields)
            self.assertIn('user{login}}', github_config.fields)
        
        # Test SL1 config
        sl1_config = config_manager.sl1_config
        self.assertEqual(sl1_config.api_url, 'http://test.example.com/api')
        self.assertEqual(sl1_config.username, 'testuser')
        self.assertEqual(sl1_config.password, 'testpass')
    
    def test_webhook_config_parsing(self):
        """Test webhook configuration parsing."""
        config_line = "action,user{name}::User $user.name$ performed $action$"
        webhook_config = WebhookConfig.from_config_line('test', config_line)
        
        self.assertEqual(webhook_config.webhook_type, 'test')
        self.assertEqual(webhook_config.fields, ['action', 'user{name}'])
        self.assertEqual(webhook_config.template, 'User $user.name$ performed $action$')
    
    def test_invalid_webhook_config(self):
        """Test handling of invalid webhook configuration."""
        # Missing template separator
        with self.assertRaises(ValueError):
            WebhookConfig.from_config_line('test', 'action,user')
        
        # Empty fields
        with self.assertRaises(ValueError):
            WebhookConfig.from_config_line('test', '::Some template')


if __name__ == '__main__':
    unittest.main()