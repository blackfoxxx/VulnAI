from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from prometheus_client import start_http_server, Counter

from app.api import admin_endpoints, tools_endpoints, chat_endpoint, tools_endpoint, tool_requests_endpoint
from app.utils import error_handlers, logger
from app.ml.training_engine import engine as ml_engine

# Load environment variables
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv(verbose=True)

# Verify environment variables
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    print("Warning: OPENAI_API_KEY not found in environment variables")
else:
    print(f"OpenAI API key found: {openai_key[:8]}...")

# Initialize FastAPI app
app = FastAPI(
    title="VulnLearnAI",
    description="AI-powered cybersecurity tool for vulnerability assessment and training",
    version="1.0.0"
)

# Configure CORS with environment variables
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Token"],
)

# Create necessary directories
os.makedirs("data/logs", exist_ok=True)
os.makedirs("data/model", exist_ok=True)

# Register API routers
app.include_router(
    admin_endpoints.router,
    prefix="/api/admin",
    tags=["admin"]
)

app.include_router(
    tools_endpoints.router,
    prefix="/api/tools",
    tags=["tools"]
)

app.include_router(
    tools_endpoint.router,
    prefix="/api",
    tags=["tools-api"]
)

app.include_router(
    tool_requests_endpoint.router,
    prefix="/api",
    tags=["tool-requests"]
)

app.include_router(
    chat_endpoint.router,
    prefix="/api",
    tags=["chat"]
)

# Register exception handlers
error_handlers.register_exception_handlers(app)

# Mount static files
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

# Get absolute paths and log them
base_dir = Path(__file__).parent.parent
landing_dir = base_dir / "landing"
admin_dir = base_dir / "admin-panel"
tools_dir = base_dir / "tools"

print(f"Base dir: {base_dir}")
print(f"Admin dir: {admin_dir}")
print(f"Admin dir exists: {admin_dir.exists()}")
print(f"Training file exists: {(admin_dir / 'training.html').exists()}")

# Mount static files
from fastapi.staticfiles import StaticFiles

# Mount admin panel static files first (higher priority)
app.mount("/admin", StaticFiles(directory=str(admin_dir), html=True), name="admin")

# Mount tools directory for wordlists and security tools
app.mount("/tools", StaticFiles(directory=str(tools_dir), html=True), name="tools")

# Mount landing page last (lowest priority)
app.mount("/", StaticFiles(directory=str(landing_dir), html=True), name="landing")

# Redirect routes to admin panel
@app.get("/chat")
async def chat_redirect():
    return RedirectResponse(url="/admin/chat.html")

@app.get("/chat-tools")
async def chat_tools_redirect():
    return RedirectResponse(url="/admin/chat-tools.html")

@app.get("/training")
async def training_redirect():
    return RedirectResponse(url="/admin/training.html")

@app.get("/tools")
async def tools_redirect():
    return RedirectResponse(url="/admin/tools.html")

@app.get("/analysis")
async def analysis_redirect():
    return RedirectResponse(url="/admin/tools-enhanced.html")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "components": {
            "api": "operational",
            "ml_engine": "operational" if ml_engine.load_models() else "no_model"
        }
    }

from fastapi.responses import HTMLResponse
from pathlib import Path

# Root endpoint serving admin panel index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = admin_dir / "index.html"
    return index_path.read_text(encoding="utf-8")

# Initialize Prometheus metrics
REQUEST_COUNT = Counter("request_count", "Total number of requests", ["endpoint"])

# Start Prometheus metrics server
start_http_server(8001)

@app.middleware("http")
async def prometheus_middleware(request, call_next):
    response = await call_next(request)
    REQUEST_COUNT.labels(endpoint=request.url.path).inc()
    return response

@app.get("/metrics")
def metrics():
    """Expose Prometheus metrics"""
    from prometheus_client import generate_latest
    return generate_latest()

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.log_info("VulnLearnAI service starting up...")
    # Try to load existing ML models
    if ml_engine.load_models():
        logger.log_info("Existing ML models loaded successfully")
    else:
        logger.log_warning("No existing ML models found")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.log_info("VulnLearnAI service shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
