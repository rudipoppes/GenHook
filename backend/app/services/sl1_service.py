import httpx
import asyncio
import logging
from typing import Optional
from ..core.config import get_config

logger = logging.getLogger(__name__)

class SL1Service:
    def __init__(self):
        config = get_config()
        self.api_url = config.get('sl1', 'api_url', fallback='https://sl1.company.com/api/alert')
        self.username = config.get('sl1', 'username', fallback='')
        self.password = config.get('sl1', 'password', fallback='')
        self.timeout = config.getint('sl1', 'timeout', fallback=30)
        self.retry_attempts = config.getint('sl1', 'retry_attempts', fallback=3)
        
        if not self.username or not self.password:
            logger.warning("SL1 credentials not configured. Check app-config.ini")
    
    async def send_alert(self, message: str) -> bool:
        """
        Send alert to SL1 monitoring system
        
        Args:
            message: Human-readable message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.username or not self.password:
            logger.error("SL1 credentials not configured")
            return False
        
        payload = {
            "force_ytype": "0",
            "force_yid": "0", 
            "force_yname": "",
            "message": message,
            "value": "",
            "threshold": "",
            "message_time": "0",
            "aligned_resource": "/api/organization/0"
        }
        
        auth = (self.username, self.password)
        
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, verify=False) as client:
                    response = await client.post(
                        self.api_url,
                        json=payload,
                        auth=auth,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json, */*",
                            "Pragma": "no-cache",
                            "Cache-Control": "no-cache",
                            "x-em7-guid-paths": "1"
                        }
                    )
                    
                    if response.status_code in [200, 201]:
                        logger.info(f"Successfully sent alert to SL1: {message[:100]}...")
                        return True
                    else:
                        logger.warning(f"SL1 API returned status {response.status_code}: {response.text}")
                        
            except httpx.TimeoutException:
                logger.warning(f"SL1 API timeout on attempt {attempt + 1}")
            except httpx.RequestError as e:
                logger.warning(f"SL1 API request error on attempt {attempt + 1}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending to SL1 on attempt {attempt + 1}: {e}")
            
            if attempt < self.retry_attempts - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying SL1 API call in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"Failed to send alert to SL1 after {self.retry_attempts} attempts")
        return False
    
    def send_alert_sync(self, message: str) -> bool:
        """
        Synchronous wrapper for send_alert
        """
        return asyncio.run(self.send_alert(message))

# Global instance
sl1_service = SL1Service()