#!/usr/bin/env python3
"""
Production version of main.py with environment-aware configuration
"""
import os
from fastapi import FastAPI, Request, HTTPException
import logging
from app.core.config import get_config, get_webhook_config
from app.core.extractor import extract_fields
from app.services.sl1_service import sl1_service

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/genhook/app.log'),
        logging.StreamHandler()  # Also log to console for supervisor
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GenHook API", 
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENV") != "production" else None,  # Disable docs in prod
    redoc_url=None
)

@app.on_startup
async def startup_event():
    logger.info("🚀 GenHook starting up...")
    logger.info(f"Environment: {os.getenv('ENV', 'development')}")

@app.get("/")
async def root():
    return {"message": "GenHook API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check for load balancers and monitoring"""
    try:
        # Test configuration loading
        config = get_config()
        webhook_config = get_webhook_config()
        
        return {
            "status": "healthy",
            "version": "1.0.0",
            "webhook_types": len(webhook_config),
            "timestamp": "2024-08-05T15:38:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/webhook/{service}")
async def receive_webhook(service: str, request: Request):
    """
    Generic webhook endpoint that processes any configured webhook type
    """
    start_time = time.time()
    
    try:
        payload = await request.json()
        logger.info(f"Received {service} webhook from {request.client.host}")
        
        webhook_config = get_webhook_config()
        
        if service not in webhook_config:
            logger.warning(f"Unknown webhook type: {service}")
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
                if current_field.strip():
                    field = current_field.strip()
                    if '{' in field and ',' in field[field.find('{'):field.rfind('}')]:
                        if field == 'pull_request{title,user{login}}':
                            fields.extend(['pull_request{title}', 'pull_request{user{login}}'])
                        else:
                            fields.append(field)
                    else:
                        fields.append(field)
                current_field = ""
            else:
                current_field += char
        
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
        
        message = template
        for key, value in extracted_data.items():
            if value is not None:
                message = message.replace(f"${key}$", str(value))
        
        success = await sl1_service.send_alert(message)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        if success:
            logger.info(f"Successfully processed {service} webhook in {processing_time:.1f}ms")
            return {
                "status": "success", 
                "message": "Webhook processed and alert sent to SL1",
                "generated_message": message,
                "processing_time_ms": round(processing_time, 1)
            }
        else:
            logger.error(f"Failed to send {service} webhook to SL1 after {processing_time:.1f}ms")
            return {
                "status": "error",
                "message": "Webhook processed but failed to send to SL1",
                "generated_message": message,
                "processing_time_ms": round(processing_time, 1)
            }
            
    except ValueError as e:
        logger.error(f"Invalid JSON in {service} webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Error processing {service} webhook after {processing_time:.1f}ms: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import time
    
    # Production settings
    uvicorn.run(
        "production_main:app", 
        host="127.0.0.1",  # Only bind to localhost, nginx will proxy
        port=8000,
        workers=1,  # Single worker for MVP
        reload=False,  # Disable auto-reload in production
        access_log=True,
        log_level="info"
    )