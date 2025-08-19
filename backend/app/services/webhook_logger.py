"""
Webhook payload logging service with rotating logs and automatic directory creation.
"""
import json
import logging
import os
import pwd
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional


class WebhookLogger:
    """
    Manages rotating log files for webhook payloads, with automatic directory creation
    and proper permission handling for production environments.
    """
    
    def __init__(self, config):
        """
        Initialize the webhook logger with configuration.
        
        Args:
            config: ConfigParser instance with webhook_logging section
        """
        self.enabled = config.getboolean('webhook_logging', 'enabled', fallback=True)
        if not self.enabled:
            return
            
        self.base_dir = Path(config.get('webhook_logging', 'base_directory', fallback='logs/webhooks'))
        self.max_bytes = config.getint('webhook_logging', 'max_bytes', fallback=10485760)  # 10MB
        self.backup_count = config.getint('webhook_logging', 'backup_count', fallback=5)
        self.log_file_name = config.get('webhook_logging', 'log_file_name', fallback='payload.log')
        
        # Unknown payload logging settings (disabled by default for production safety)
        self.log_unknown_payloads = config.getboolean('webhook_logging', 'log_unknown_payloads', fallback=False)
        self.unknown_payload_max_size = config.getint('webhook_logging', 'unknown_payload_max_size', fallback=51200)  # 50KB
        self.unknown_payload_daily_limit = config.getint('webhook_logging', 'unknown_payload_daily_limit', fallback=100)
        
        # Track daily unknown payload counts (reset daily)
        self._unknown_count_cache = {}  # Format: {date_str: count}
        
        # Cache for created loggers to avoid recreating them
        self._loggers = {}
        self._lock = Lock()  # Thread safety for logger creation
        
        # Create base directory if it doesn't exist
        self._create_base_directory()
        
        # Configure logging format
        self.formatter = logging.Formatter('%(message)s')  # We'll format JSON ourselves
        
        # Main logger for this service
        self.logger = logging.getLogger(__name__)
    
    def _create_base_directory(self) -> bool:
        """
        Create the base logs directory with proper permissions.
        
        Returns:
            bool: True if successful or already exists, False otherwise
        """
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
            
            # If running as root (shouldn't happen with supervisor), set ownership
            if os.getuid() == 0:
                try:
                    genhook_uid = pwd.getpwnam('genhook').pw_uid
                    genhook_gid = pwd.getpwnam('genhook').pw_gid
                    os.chown(self.base_dir, genhook_uid, genhook_gid)
                except KeyError:
                    # genhook user doesn't exist, continue anyway
                    pass
                    
            return True
        except PermissionError:
            self.logger.warning(f"Cannot create base log directory {self.base_dir}, webhook logging disabled")
            self.enabled = False
            return False
        except Exception as e:
            self.logger.error(f"Error creating base log directory: {e}")
            self.enabled = False
            return False
    
    def _create_webhook_directory(self, webhook_type: str) -> Optional[Path]:
        """
        Create directory for a specific webhook type with proper permissions.
        
        Args:
            webhook_type: The webhook type (github, stripe, etc.)
            
        Returns:
            Path: The created directory path, or None if failed
        """
        try:
            webhook_dir = self.base_dir / webhook_type
            webhook_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
            
            # If running as root, set ownership
            if os.getuid() == 0:
                try:
                    genhook_uid = pwd.getpwnam('genhook').pw_uid
                    genhook_gid = pwd.getpwnam('genhook').pw_gid
                    os.chown(webhook_dir, genhook_uid, genhook_gid)
                except KeyError:
                    pass
                    
            return webhook_dir
        except PermissionError:
            self.logger.warning(f"Cannot create log directory for {webhook_type}, logging disabled for this webhook type")
            return None
        except Exception as e:
            self.logger.error(f"Error creating webhook directory for {webhook_type}: {e}")
            return None
    
    def _get_logger(self, webhook_type: str) -> Optional[logging.Logger]:
        """
        Get or create a logger for a specific webhook type.
        
        Args:
            webhook_type: The webhook type (github, stripe, etc.)
            
        Returns:
            logging.Logger: The logger instance, or None if failed
        """
        if not self.enabled:
            return None
            
        with self._lock:
            # Return cached logger if exists
            if webhook_type in self._loggers:
                return self._loggers[webhook_type]
            
            # Create webhook directory
            webhook_dir = self._create_webhook_directory(webhook_type)
            if webhook_dir is None:
                return None
            
            # Create logger
            logger_name = f"webhook.{webhook_type}"
            webhook_logger = logging.getLogger(logger_name)
            webhook_logger.setLevel(logging.INFO)
            
            # Remove any existing handlers to avoid duplicates
            webhook_logger.handlers = []
            
            # Create rotating file handler
            log_file = webhook_dir / self.log_file_name
            try:
                handler = RotatingFileHandler(
                    str(log_file),
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count,
                    mode='a'
                )
                handler.setFormatter(self.formatter)
                webhook_logger.addHandler(handler)
                
                # Prevent propagation to root logger
                webhook_logger.propagate = False
                
                # Cache the logger
                self._loggers[webhook_type] = webhook_logger
                
                self.logger.info(f"Created webhook logger for {webhook_type}: {log_file}")
                return webhook_logger
                
            except Exception as e:
                self.logger.error(f"Failed to create log handler for {webhook_type}: {e}")
                return None
    
    def log_payload(
        self, 
        webhook_type: str, 
        payload: Dict[str, Any], 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log a webhook payload with metadata.
        
        Args:
            webhook_type: The webhook type (github, stripe, etc.)
            payload: The webhook payload as a dictionary
            metadata: Optional metadata (timestamp, IP, etc.)
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        if not self.enabled:
            return False
            
        webhook_logger = self._get_logger(webhook_type)
        if webhook_logger is None:
            return False
        
        try:
            # Prepare log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "webhook_type": webhook_type,
                "payload": payload
            }
            
            # Add metadata if provided
            if metadata:
                log_entry.update(metadata)
            
            # Log as JSON
            json_line = json.dumps(log_entry, separators=(',', ':'))
            webhook_logger.info(json_line)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log payload for {webhook_type}: {e}")
            return False
    
    def log_processing_result(
        self,
        webhook_type: str,
        payload: Dict[str, Any],
        processing_status: str,
        generated_message: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log webhook payload along with processing results.
        
        Args:
            webhook_type: The webhook type
            payload: The webhook payload
            processing_status: 'success', 'error', or 'failed'
            generated_message: The generated message (if successful)
            error_message: Error message (if failed)
            metadata: Additional metadata
            
        Returns:
            bool: True if logged successfully
        """
        log_metadata = metadata or {}
        log_metadata.update({
            "processing_status": processing_status
        })
        
        if generated_message:
            log_metadata["generated_message"] = generated_message
        if error_message:
            log_metadata["error_message"] = error_message
            
        return self.log_payload(webhook_type, payload, log_metadata)
    
    def _should_log_unknown_payload(self, payload: Dict[str, Any], error_message: str) -> bool:
        """
        Check if an unknown payload should be logged based on configuration and limits.
        
        Args:
            payload: The webhook payload
            error_message: The error message
            
        Returns:
            bool: True if the payload should be logged
        """
        # Feature must be enabled
        if not self.log_unknown_payloads:
            return False
        
        # Must be an "invalid token" error (not other types of errors)
        if "Invalid webhook token" not in error_message:
            return False
            
        # Check payload size limit
        try:
            payload_size = len(json.dumps(payload).encode('utf-8'))
            if payload_size > self.unknown_payload_max_size:
                self.logger.warning(f"Unknown payload too large ({payload_size} bytes), skipping log")
                return False
        except Exception:
            # If we can't serialize, don't log
            return False
        
        # Check daily limit
        today = datetime.now().strftime('%Y-%m-%d')
        current_count = self._unknown_count_cache.get(today, 0)
        
        if current_count >= self.unknown_payload_daily_limit:
            # Only log warning once per day
            if current_count == self.unknown_payload_daily_limit:
                self.logger.warning(f"Daily unknown payload limit ({self.unknown_payload_daily_limit}) reached")
            return False
        
        # Update counter
        self._unknown_count_cache[today] = current_count + 1
        
        # Clean old dates from cache (keep only last 7 days)
        cutoff_days = 7
        all_dates = list(self._unknown_count_cache.keys())
        for date_str in all_dates:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                days_old = (datetime.now() - date_obj).days
                if days_old > cutoff_days:
                    del self._unknown_count_cache[date_str]
            except ValueError:
                # Invalid date format, remove it
                del self._unknown_count_cache[date_str]
        
        return True
    
    def log_unknown_payload(
        self,
        webhook_type: str,
        payload: Dict[str, Any],
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Log an unknown webhook payload (invalid token) if enabled and within limits.
        
        Args:
            webhook_type: The webhook type
            payload: The actual webhook payload
            error_message: The error message
            metadata: Additional metadata
            
        Returns:
            bool: True if logged successfully
        """
        if not self._should_log_unknown_payload(payload, error_message):
            return False
        
        # Create enhanced metadata for unknown payloads
        log_metadata = metadata or {}
        log_metadata.update({
            "processing_status": "unknown_token",
            "error_message": error_message,
            "payload_size": len(json.dumps(payload).encode('utf-8')),
            "daily_unknown_count": self._unknown_count_cache.get(datetime.now().strftime('%Y-%m-%d'), 0)
        })
        
        return self.log_payload(webhook_type, payload, log_metadata)
    
    def get_recent_payloads(self, webhook_type: str, limit: int = 10) -> list:
        """
        Get recent payloads for a webhook type from the log file.
        
        Args:
            webhook_type: The webhook type
            limit: Maximum number of payloads to return
            
        Returns:
            list: List of recent payload entries
        """
        if not self.enabled:
            return []
            
        webhook_dir = self.base_dir / webhook_type
        log_file = webhook_dir / self.log_file_name
        
        if not log_file.exists():
            return []
        
        try:
            payloads = []
            with open(log_file, 'r') as f:
                # Read lines in reverse order (most recent first)
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    line = line.strip()
                    if line:
                        try:
                            payload_data = json.loads(line)
                            payloads.append(payload_data)
                        except json.JSONDecodeError:
                            continue
                            
                    if len(payloads) >= limit:
                        break
            
            return payloads
            
        except Exception as e:
            self.logger.error(f"Error reading recent payloads for {webhook_type}: {e}")
            return []
    
    def get_available_webhook_types(self) -> list:
        """
        Get list of webhook types that have log directories.
        
        Returns:
            list: List of webhook type names
        """
        if not self.enabled or not self.base_dir.exists():
            return []
        
        try:
            webhook_types = []
            for item in self.base_dir.iterdir():
                if item.is_dir():
                    webhook_types.append(item.name)
            return sorted(webhook_types)
        except Exception as e:
            self.logger.error(f"Error listing webhook types: {e}")
            return []


# Global instance - will be initialized in main.py
webhook_logger: Optional[WebhookLogger] = None


def init_webhook_logger(config) -> WebhookLogger:
    """
    Initialize the global webhook logger instance.
    
    Args:
        config: ConfigParser instance
        
    Returns:
        WebhookLogger: The initialized logger instance
    """
    global webhook_logger
    webhook_logger = WebhookLogger(config)
    return webhook_logger


def get_webhook_logger() -> Optional[WebhookLogger]:
    """
    Get the global webhook logger instance.
    
    Returns:
        WebhookLogger: The logger instance, or None if not initialized
    """
    return webhook_logger