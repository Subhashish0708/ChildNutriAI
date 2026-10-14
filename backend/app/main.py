"""
ChildNutri AI — FastAPI Main Application
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from backend.app.database import engine
from backend.app.models import Base

# Import all models so they register with Base
import backend.app.models  # noqa

# Create all tables
Base.metadata.create_all(bind=engine)

from backend.app.routers.auth import router as auth_router
from backend.app.routers.children import router as children_router
from backend.app.routers.assessments import router as assessments_router
from backend.app.routers.ocr import router as ocr_router, resources_router, meta_router
from backend.app.routers.uploads import router as uploads_router
from backend.app.routers.vision import router as vision_router
from backend.app.services.seed_data import seed_articles

app = FastAPI(
    title="ChildNutri AI",
    description="Pediatric Malnutrition Screening & Decision-Support System",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Serve frontend from the same origin — no CORS needed for production
# Keep CORS loose for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory
APP_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_DIR = os.path.dirname(BACKEND_DIR)
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
seed_articles()

# Register all API routers
app.include_router(auth_router)
app.include_router(children_router)
app.include_router(assessments_router)
app.include_router(ocr_router)
app.include_router(uploads_router)
app.include_router(vision_router)
app.include_router(resources_router)
app.include_router(meta_router)

# Serve frontend static files (FastAPI serves both API + frontend from port 8000)
FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
