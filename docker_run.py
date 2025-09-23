import os
import sys
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("docker_runner")

def get_port():
    """Get port from environment with validation"""
    try:
        # Get raw value for logging
        port_raw = os.getenv("PORT", "8000")
        logger.info(f"Raw PORT value: {port_raw}")
        
        # Try to convert to int
        port = int(port_raw)
        
        # Validate range
        if not (1024 <= port <= 65535):
            logger.warning(f"Port {port} outside recommended range (1024-65535), using 8000")
            return 8000
            
        logger.info(f"Using port {port}")
        return port
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid PORT value: {e}, using default 8000")
        return 8000

if __name__ == "__main__":
    # Log environment for debugging
    logger.info("Environment variables:")
    for key, value in os.environ.items():
        if key in ['PORT', 'PYTHONPATH', 'PATH']:
            logger.info(f"{key}={value}")
    
    # Get validated port
    port = get_port()
    logger.info(f"Starting server on port {port}")
    
    try:
        # Start uvicorn with the validated port
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            workers=1,
            timeout_keep_alive=75,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)