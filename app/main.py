from fastapi import FastAPI, logger
from app.api.routes import router
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
from starlette.requests import Request
from app.api.routes import router
from app.core.config import get_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
settings = get_settings()

#Create FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A chat support agent that uses RAG to answer user queries and creates support tickets\
    when it cannot answer. Built with FastAPI, Redis, and Supabase.",   
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://your-production-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log incoming requests and response times
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"    
    logging.info(f"{request.method} {request.url.path} completed in {process_time:.3f}s")
    return response

# Life cycle event to log application startup
@app.on_event("startup")
async def startup_event():
    logging.info(f"Starting {settings.app_name} version {settings.app_version}")
    logging.info(f"Debug mode: {settings.debug}")
    logging.info(f"Log level: {settings.log_level}")
    logging.info(f"RAG model: {settings.rag_model_name}")
    logging.info(f"Backend tickets: {settings.support_ticket_enabled}")
    logging.info(f"Documentation: http://localhost:8000/docs")

@app.on_event("shutdown")
async def shutdown_event():
    logging.info(f"Shutting down {settings.app_name}")   

# Include API routes
app.include_router(
    router, 
    prefix="/api/v1",
    tags=["chat","support","agent"])