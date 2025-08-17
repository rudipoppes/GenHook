"""
SL1 GraphQL Service for creating Event Policies in ScienceLogic SL1.
"""
import httpx
import logging
import json
from typing import Optional, Dict, Any
from ..core.config import get_config

logger = logging.getLogger(__name__)


class SL1GraphQLService:
    """Service for interacting with SL1 GraphQL API to create Event Policies."""
    
    def __init__(self):
        """Initialize the SL1 GraphQL service with configuration."""
        config = get_config()
        
        # Check if GraphQL section exists
        if 'sl1_graphql' not in config:
            logger.warning("SL1 GraphQL configuration not found. Feature disabled.")
            self.enabled = False
            return
            
        self.enabled = config.getboolean('sl1_graphql', 'enabled', fallback=False)
        
        if not self.enabled:
            logger.info("SL1 GraphQL feature is disabled in configuration.")
            return
            
        self.endpoint = config.get('sl1_graphql', 'endpoint', fallback='')
        self.username = config.get('sl1_graphql', 'username', fallback='')
        self.password = config.get('sl1_graphql', 'password', fallback='')
        self.timeout = config.getint('sl1_graphql', 'timeout', fallback=30)
        
        if not all([self.endpoint, self.username, self.password]):
            logger.error("SL1 GraphQL configuration incomplete. Check endpoint, username, and password.")
            self.enabled = False
    
    async def create_event_policy(
        self, 
        service_name: str, 
        token: str, 
        severity: int
    ) -> Dict[str, Any]:
        """
        Create an SL1 Event Policy via GraphQL mutation.
        
        Args:
            service_name: Name of the service (e.g., 'github', 'meraki')
            token: The webhook token to match in regularExpression1
            severity: Severity level (1=Notice, 2=Minor, 3=Major, 4=Critical)
            
        Returns:
            Dict containing success status and policy ID or error message
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "SL1 GraphQL feature is not enabled or configured"
            }
        
        # Validate severity (1-4, where 4 is most critical)
        if severity not in [1, 2, 3, 4]:
            return {
                "success": False,
                "error": f"Invalid severity: {severity}. Must be 1-4 (1=Notice, 4=Critical)"
            }
        
        # Build the GraphQL mutation
        # Note: The identifierPattern uses 4 backslashes to properly escape in GraphQL
        mutation = """
        mutation CreateEventPolicy {
          eventPolicyCreate(
            message: "%I"
            messageMatch: false
            identifierPattern: ".*\\\\|.*\\\\|(.*)"
            enabled: true
            identifierResultFormat: ""
            multiMatch: false
            name: "GENHOOK_%s"
            regularExpression1: "%s"
            regularExpression2: ""
            regularExpressionSearch: true
            severity: %d
          ) {
            id
          }
        }
        """ % (service_name, token, severity)
        
        # Prepare the GraphQL request
        graphql_request = {
            "query": mutation,
            "variables": {}
        }
        
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=False  # Disable SSL verification if needed
            ) as client:
                response = await client.post(
                    self.endpoint,
                    json=graphql_request,
                    auth=(self.username, self.password),
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check for GraphQL errors
                    if "errors" in result:
                        error_msg = result["errors"][0].get("message", "Unknown GraphQL error")
                        logger.error(f"GraphQL error creating Event Policy: {error_msg}")
                        return {
                            "success": False,
                            "error": f"GraphQL error: {error_msg}"
                        }
                    
                    # Extract policy ID from successful response
                    if "data" in result and "eventPolicyCreate" in result["data"]:
                        policy_id = result["data"]["eventPolicyCreate"].get("id")
                        logger.info(f"Successfully created SL1 Event Policy with ID: {policy_id}")
                        return {
                            "success": True,
                            "policy_id": policy_id,
                            "message": f"Event Policy created successfully with ID: {policy_id}"
                        }
                    else:
                        logger.error(f"Unexpected GraphQL response structure: {result}")
                        return {
                            "success": False,
                            "error": "Unexpected response structure from GraphQL API"
                        }
                else:
                    logger.error(f"SL1 GraphQL API returned status {response.status_code}: {response.text}")
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}: {response.text[:200]}"
                    }
                    
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to SL1 GraphQL endpoint: {self.endpoint}")
            return {
                "success": False,
                "error": "Connection timeout to SL1 GraphQL API"
            }
        except httpx.RequestError as e:
            logger.error(f"Request error connecting to SL1 GraphQL: {e}")
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating SL1 Event Policy: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def get_graphql_preview(self, service_name: str, token: str, severity: int) -> str:
        """
        Generate a preview of the GraphQL mutation for user review.
        
        Args:
            service_name: Name of the service
            token: The webhook token
            severity: Severity level (1-4)
            
        Returns:
            Formatted GraphQL mutation string
        """
        mutation = """mutation CreateEventPolicy {
  eventPolicyCreate(
    message: "%I"
    messageMatch: false
    identifierPattern: ".*\\\\|.*\\\\|(.*)"
    enabled: true
    identifierResultFormat: ""
    multiMatch: false
    name: "GENHOOK_%s"
    regularExpression1: "%s"
    regularExpression2: ""
    regularExpressionSearch: true
    severity: %d
  ) {
    id
  }
}""" % (service_name, token, severity)
        
        return mutation


# Global instance
sl1_graphql_service = SL1GraphQLService()