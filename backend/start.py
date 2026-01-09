"""
Startup script for the EUFSI LCA Tool backend server
"""
import os
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting EUFSI LCA Tool server on {host}:{port}")
    print(f"Backend API will be available at: http://localhost:{port}/api")
    print(f"API Documentation: http://localhost:{port}/docs")

    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )
