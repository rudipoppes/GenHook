"""
GenHook Web Configuration Interface

This module provides a web-based interface for configuring GenHook webhook processing.
Users can visually select fields from JSON payloads and generate webhook configurations.
"""

from .routes import router as web_router
from .config import WebConfig

__all__ = ["web_router", "WebConfig"]