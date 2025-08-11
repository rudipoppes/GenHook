"""
Token generation service for webhook authentication.
"""
import secrets
import string
from typing import Optional


def generate_webhook_token(length: int = 32, prefix: Optional[str] = None) -> str:
    """
    Generate a cryptographically secure token for webhook authentication.
    
    Args:
        length: Length of the random part (default 32 characters)
        prefix: Optional prefix for the token (e.g., 'prod', 'dev', 'test')
    
    Returns:
        str: A unique token string
    """
    # Use alphanumeric characters for URL safety
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def is_token_unique(token: str, existing_configs: dict) -> bool:
    """
    Check if a token is unique across all existing configurations.
    
    Args:
        token: The token to check
        existing_configs: Dictionary of existing webhook configurations
    
    Returns:
        bool: True if token is unique, False otherwise
    """
    # Check if any config key contains this token
    for config_key in existing_configs.keys():
        if '_' in config_key:
            parts = config_key.rsplit('_', 1)  # Split from the right to handle service names with underscores
            if len(parts) == 2:
                _, existing_token = parts
                if existing_token == token:
                    return False
    return True


def generate_unique_token(existing_configs: dict, prefix: Optional[str] = None) -> str:
    """
    Generate a unique token that doesn't exist in current configurations.
    
    Args:
        existing_configs: Dictionary of existing webhook configurations
        prefix: Optional prefix for the token
    
    Returns:
        str: A unique token string
    """
    max_attempts = 10  # Prevent infinite loop in extremely unlikely collision scenario
    
    for _ in range(max_attempts):
        token = generate_webhook_token(prefix=prefix)
        if is_token_unique(token, existing_configs):
            return token
    
    # If we somehow can't generate a unique token in 10 attempts,
    # add timestamp to ensure uniqueness
    import time
    timestamp = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
    return generate_webhook_token(length=26, prefix=f"{prefix}_{timestamp}" if prefix else timestamp)