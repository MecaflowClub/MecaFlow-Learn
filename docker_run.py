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
        port = int(os.getenv("PORT", "8000"))
        if not (1024 <= port <= 65535):
            logger.warning(f"Port {port} outside recommended range (1024-65535), using 8000")
            return 8000
        logger.info(f"Using port {port}")
        return port
    except ValueError:
        logger.warning("Invalid PORT value in environment, using default 8000")
        return 8000

if __name__ == "__main__":
    # Get validated port
    port = get_port()
    print(f"Starting server on port {port}")
    
    # Start uvicorn with the validated port
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        timeout_keep_alive=75
    )