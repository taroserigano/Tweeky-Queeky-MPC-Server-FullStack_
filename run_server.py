"""Simple server runner script"""
import os
import sys

# Disable MCP for testing
os.environ['SKIP_MCP'] = 'true'

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5001,
        log_level="info"
    )
