from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import os
from pathlib import Path

from app.core.config import get_config, get_webhook_config
from app.core.extractor import extract_fields
from app.services.sl1_service import sl1_service
from app.web import web_router
from app.web.config import get_web_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GenHook API", version="1.0.0")

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

@app.post("/webhook/{service}")
async def receive_webhook(service: str, request: Request, response: Response):
    """
    Generic webhook endpoint that processes any configured webhook type
    """
    try:
        # Check for completely empty body first
        body = await request.body()
        if not body:
            logger.info(f"Empty body received for {service} webhook - returning 202 Accepted")
            response.status_code = 202
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
        
        webhook_config = get_webhook_config()
        
        if service not in webhook_config:
            raise HTTPException(status_code=404, detail=f"Webhook type '{service}' not configured")
        
        config_line = webhook_config[service]
        fields_part, template = config_line.split('::', 1)
        
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
        
        success = await sl1_service.send_alert(message)
        
        if success:
            logger.info(f"Successfully processed {service} webhook and sent to SL1")
            return {
                "status": "success", 
                "message": "Webhook processed and alert sent to SL1",
                "generated_message": message
            }
        else:
            logger.error(f"Failed to send {service} webhook to SL1")
            return {
                "status": "error",
                "message": "Webhook processed but failed to send to SL1",
                "generated_message": message
            }
            
    except ValueError as e:
        logger.error(f"Invalid JSON in {service} webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing {service} webhook: {e}")
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