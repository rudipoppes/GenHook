from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
import re
from pathlib import Path

from app.core.config import get_config, get_webhook_config
from app.core.extractor import extract_fields
from app.services.sl1_service import sl1_service
from app.services.webhook_logger import init_webhook_logger, get_webhook_logger
from app.web import web_router
from app.web.config import get_web_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GenHook API", version="1.0.0")

# Initialize webhook logger
config = get_config()
webhook_payload_logger = init_webhook_logger(config)

# Configure web interface if enabled
web_config = get_web_config()
if web_config.enabled:
    # Set up static files and templates
    static_dir = Path(__file__).parent / "app" / "static"
    templates_dir = Path(__file__).parent / "app" / "templates"
    
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info("✅ Static files mounted at /static")
    
    if templates_dir.exists():
        templates = Jinja2Templates(directory=str(templates_dir))
        
        # Configure templates in web routes module
        import app.web.routes as web_routes_module
        web_routes_module.templates = templates
        
        # Include web router
        app.include_router(web_router)
        logger.info("✅ Web interface enabled and configured")
    else:
        logger.warning("⚠️ Templates directory not found, web interface disabled")
else:
    logger.info("ℹ️ Web interface disabled in configuration")

@app.get("/")
async def root():
    return {"message": "GenHook API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook/{service}/{token}")
async def receive_webhook(service: str, token: str, request: Request, response: Response):
    """
    Tokenized webhook endpoint that validates token before processing
    """
    try:
        # Check for completely empty body first
        body = await request.body()
        if not body:
            logger.info(f"Empty body received for {service} webhook - returning 200 OK")
            response.status_code = 200
            return {
                "status": "accepted",
                "message": "Empty body received and ignored",
                "service": service
            }
        
        # Parse JSON from non-empty body
        payload = await request.json()
        logger.info(f"Received {service} webhook")
        
        # Handle empty JSON payload
        if not payload:
            logger.info(f"Empty payload received for {service} webhook - returning 200 OK")
            response.status_code = 200
            return {
                "status": "accepted",
                "message": "Empty payload received and ignored",
                "service": service
            }
        
        # Note: Payload logging is handled in log_processing_result() later
        
        webhook_config = get_webhook_config()
        
        # Build the base config key with service_token format (lowercase service to match config)
        base_config_key = f"{service.lower()}_{token}"
        
        # Find the matching config key
        config_key = None
        config_line = None
        alignment_type = None
        alignment_id = None
        
        # Check if exact key exists (could be old or new format)
        if base_config_key in webhook_config:
            config_key = base_config_key
            config_line = webhook_config[config_key]
        
        if config_key is None:
            raise HTTPException(status_code=404, detail=f"Invalid webhook token for '{service}'")
        
        # Parse config line - support both old and new formats
        if '::' in config_line:
            # Old format: fields::message
            fields_part, template = config_line.split('::', 1)
        else:
            # New format: alignment|fields|message
            parts = config_line.split('|', 2)
            if len(parts) == 3:
                alignment_str, fields_part, template = parts
                # Parse alignment string (e.g., "org:123" or "device:456")
                if alignment_str and ':' in alignment_str:
                    alignment_type, alignment_id_str = alignment_str.split(':', 1)
                    try:
                        alignment_id = int(alignment_id_str)
                    except ValueError:
                        alignment_id = None
            else:
                # Fallback parsing
                fields_part = parts[0] if len(parts) > 0 else ""
                template = parts[1] if len(parts) > 1 else ""
        
        # Parse fields carefully to handle nested braces
        fields = []
        current_field = ""
        brace_count = 0
        
        for char in fields_part:
            if char == '{':
                brace_count += 1
                current_field += char
            elif char == '}':
                brace_count -= 1
                current_field += char
            elif char == ',' and brace_count == 0:
                # We're at a top-level comma, end current field
                if current_field.strip():
                    field = current_field.strip()
                    # Expand compound fields like pull_request{title,user{login}}
                    if '{' in field and ',' in field[field.find('{'):field.rfind('}')]:
                        # This is compound - manually expand known patterns
                        if field == 'pull_request{title,user{login}}':
                            fields.extend(['pull_request{title}', 'pull_request{user{login}}'])
                        else:
                            fields.append(field)
                    else:
                        fields.append(field)
                current_field = ""
            else:
                current_field += char
        
        # Don't forget the last field
        if current_field.strip():
            field = current_field.strip()
            if '{' in field and ',' in field[field.find('{'):field.rfind('}')]:
                if field == 'pull_request{title,user{login}}':
                    fields.extend(['pull_request{title}', 'pull_request{user{login}}'])
                else:
                    fields.append(field)
            else:
                fields.append(field)
        
        extracted_data = extract_fields(payload, fields)
        logger.info(f"Fields to extract: {fields}")
        logger.info(f"Extracted data keys: {list(extracted_data.keys())}")
        
        message = template
        for key, value in extracted_data.items():
            if value is not None:
                old_message = message
                message = message.replace(f"${key}$", str(value))
                if old_message != message:
                    logger.info(f"Replaced ${key}$ with '{value}'")
        
        # Replace any remaining unresolved variables with '-'
        # Use a specific pattern that looks for $word.word$ variable patterns
        message = re.sub(r'\$[a-zA-Z_][a-zA-Z0-9_.]*\$', '-', message)
        
        # Prepend service|token| to the message for SL1 (easy to strip)
        final_message = f"{service.lower()}|{token}|{message}"
        
        success = await sl1_service.send_alert(final_message, alignment_type, alignment_id)
        
        # Log the processing result
        webhook_logger = get_webhook_logger()
        if webhook_logger:
            webhook_logger.log_processing_result(
                service.lower(),
                payload,
                "success" if success else "sl1_failed",
                generated_message=final_message,
                metadata={
                    "source_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "content_length": request.headers.get("content-length", "unknown"),
                    "token": token
                }
            )
        
        if success:
            logger.info(f"Successfully processed {service.lower()}:{token} webhook and sent to SL1")
            return {
                "status": "success", 
                "message": "Webhook processed and alert sent to SL1",
                "generated_message": final_message,
                "service_token": f"{service.lower()}:{token}"
            }
        else:
            logger.error(f"Failed to send {service.lower()}:{token} webhook to SL1")
            return {
                "status": "error",
                "message": "Webhook processed but failed to send to SL1",
                "generated_message": final_message,
                "service_token": f"{service.lower()}:{token}"
            }
            
    except ValueError as e:
        logger.error(f"Invalid JSON in {service.lower()}:{token} webhook: {e}")
        
        # Log error if we have a payload logger
        webhook_logger = get_webhook_logger()
        if webhook_logger:
            try:
                body = await request.body()
                webhook_logger.log_processing_result(
                    service.lower(),
                    {"raw_body": body.decode("utf-8", errors="ignore")},
                    "error",
                    error_message=f"Invalid JSON: {str(e)}",
                    metadata={
                        "source_ip": request.client.host if request.client else "unknown",
                        "token": token
                    }
                )
            except:
                pass  # Don't fail if logging fails
        
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing {service.lower()}_{token} webhook: {e}")
        
        # Log error if we have a payload logger
        webhook_logger = get_webhook_logger()
        if webhook_logger:
            try:
                webhook_logger.log_processing_result(
                    service.lower(),
                    {},  # No payload available in this case
                    "error",
                    error_message=str(e),
                    metadata={
                        "source_ip": request.client.host if request.client else "unknown"
                    }
                )
            except:
                pass  # Don't fail if logging fails
        
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Load configuration to get server settings
    config = get_config()
    
    # Get server configuration values
    host = config.get('server', 'host', fallback='0.0.0.0')
    port = config.getint('server', 'port', fallback=8000)
    reload = config.getboolean('server', 'reload', fallback=True)
    
    logger.info(f"🚀 Starting GenHook server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=reload)