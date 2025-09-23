import os
import sys
import uvicorn

def get_port():
    """Get port from environment with validation"""
    try:
        port = int(os.getenv("PORT", "8000"))
        if not (1024 <= port <= 65535):
            print(f"Warning: Port {port} outside recommended range (1024-65535), using 8000")
            return 8000
        return port
    except ValueError:
        print("Warning: Invalid PORT value, using default 8000")
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