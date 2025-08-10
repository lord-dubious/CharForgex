#!/usr/bin/env python3
"""
CharForgex Integrated Web Server
Serves GUI and provides local API endpoint for testing
"""

import os
import sys
import json
import logging
import asyncio
import threading
from pathlib import Path
from typing import Dict, Any, Optional

# Add workspace to Python path
sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/runpod_worker')

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("⚠️ FastAPI not available, falling back to simple HTTP server")
    FastAPI = None

# Import CharForgex components
try:
    from handler import CharForgeHandler
    from utils import setup_logging, ensure_directories
except ImportError as e:
    print(f"⚠️ CharForgex components not available: {e}")
    CharForgeHandler = None

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class CharForgexWebServer:
    """Integrated web server for CharForgex GUI and API"""
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.app = None
        self.handler = None
        self.gui_dir = Path(__file__).parent / "gui"
        
        if FastAPI:
            self.setup_fastapi()
        else:
            self.setup_simple_server()
    
    def setup_fastapi(self):
        """Setup FastAPI application"""
        self.app = FastAPI(
            title="CharForgex RunPod Worker",
            description="AI-Powered Character LoRA Creation & Inference",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Mount static files (GUI)
        if self.gui_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(self.gui_dir)), name="static")
        
        # Setup routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_gui():
            """Serve the main GUI"""
            index_file = self.gui_dir / "index.html"
            if index_file.exists():
                return HTMLResponse(content=index_file.read_text(), status_code=200)
            else:
                return HTMLResponse(content="<h1>CharForgex GUI not found</h1>", status_code=404)
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            try:
                if not self.handler:
                    self.handler = CharForgeHandler() if CharForgeHandler else None
                
                if self.handler:
                    status = self.handler.get_system_status()
                    return JSONResponse(content=status)
                else:
                    return JSONResponse(content={
                        "status": "degraded",
                        "message": "CharForgex handler not available",
                        "gui_available": True
                    })
            except Exception as e:
                return JSONResponse(content={
                    "status": "error",
                    "message": str(e),
                    "gui_available": True
                }, status_code=500)
        
        @self.app.post("/api/inference")
        async def inference_endpoint(request: Request):
            """Local inference endpoint for GUI testing"""
            try:
                data = await request.json()
                
                if not self.handler:
                    self.handler = CharForgeHandler() if CharForgeHandler else None
                
                if not self.handler:
                    raise HTTPException(status_code=503, detail="CharForgex handler not available")
                
                # Add operation type
                data["operation"] = "inference"
                
                # Process inference request
                result = self.handler.handle_inference(data)
                return JSONResponse(content=result)
                
            except Exception as e:
                logger.error(f"Inference error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/training")
        async def training_endpoint(request: Request):
            """Local training endpoint for GUI testing"""
            try:
                data = await request.json()
                
                if not self.handler:
                    self.handler = CharForgeHandler() if CharForgeHandler else None
                
                if not self.handler:
                    raise HTTPException(status_code=503, detail="CharForgex handler not available")
                
                # Add operation type
                data["operation"] = "training"
                
                # Process training request
                result = self.handler.handle_training(data)
                return JSONResponse(content=result)
                
            except Exception as e:
                logger.error(f"Training error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/characters")
        async def list_characters():
            """List available characters"""
            try:
                if not self.handler:
                    self.handler = CharForgeHandler() if CharForgeHandler else None
                
                if not self.handler:
                    return JSONResponse(content={"characters": []})
                
                result = self.handler.list_characters()
                return JSONResponse(content=result)
                
            except Exception as e:
                logger.error(f"List characters error: {e}")
                return JSONResponse(content={"characters": [], "error": str(e)})
        
        @self.app.post("/api/runpod")
        async def runpod_proxy(request: Request):
            """Proxy requests to RunPod endpoint"""
            try:
                import requests
                
                data = await request.json()
                endpoint_url = data.get("endpoint_url")
                api_key = data.get("api_key")
                payload = data.get("payload", {})
                
                if not endpoint_url or not api_key:
                    raise HTTPException(status_code=400, detail="Missing endpoint_url or api_key")
                
                # Make request to RunPod
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(endpoint_url, json=payload, headers=headers, timeout=300)
                
                if response.status_code == 200:
                    return JSONResponse(content=response.json())
                else:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
                
            except Exception as e:
                logger.error(f"RunPod proxy error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def setup_simple_server(self):
        """Setup simple HTTP server fallback"""
        import http.server
        import socketserver
        import os

        gui_dir = str(self.gui_dir)

        class CustomHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=gui_dir, **kwargs)

        self.server = socketserver.TCPServer(("0.0.0.0", self.port), CustomHandler)
    
    async def start_async(self):
        """Start FastAPI server"""
        if self.app:
            config = uvicorn.Config(
                app=self.app,
                host="0.0.0.0",
                port=self.port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            await server.serve()
    
    def start_simple(self):
        """Start simple HTTP server"""
        if hasattr(self, 'server'):
            logger.info(f"🌐 Simple GUI server running at http://0.0.0.0:{self.port}")
            self.server.serve_forever()
    
    def start(self):
        """Start the appropriate server"""
        logger.info(f"🚀 Starting CharForgex Web Server on port {self.port}")
        
        # Ensure directories exist
        ensure_directories()
        
        if self.app:
            logger.info("🌟 Starting FastAPI server with full API support")
            asyncio.run(self.start_async())
        else:
            logger.info("📁 Starting simple HTTP server (GUI only)")
            self.start_simple()

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="CharForgex Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on")
    parser.add_argument("--gui-only", action="store_true", help="Serve GUI only (no API)")
    
    args = parser.parse_args()
    
    # Force simple server if requested
    if args.gui_only:
        global FastAPI
        FastAPI = None
    
    server = CharForgexWebServer(port=args.port)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
