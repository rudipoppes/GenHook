from fastapi import FastAPI, Request, HTTPException
import logging
import os
from app.core.config import get_config, get_webhook_config
from app.core.extractor import extract_fields
from app.services.sl1_service import sl1_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GenHook API", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "GenHook API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/webhook/{service}")
async def receive_webhook(service: str, request: Request):
    """
    Generic webhook endpoint that processes any configured webhook type
    """
    try:
        payload = await request.json()
        logger.info(f"Received {service} webhook")
        
        # Handle empty or None payload
        if not payload:
            logger.info(f"Empty payload received for {service} webhook - returning 200 OK")
            return {
                "status": "success",
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
        # If it's just empty body, return success instead of error
        if "Expecting value" in str(e):
            logger.info(f"Empty body received for {service} webhook - returning 200 OK")
            return {
                "status": "success", 
                "message": "Empty body received and ignored",
                "service": service
            }
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing {service} webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)