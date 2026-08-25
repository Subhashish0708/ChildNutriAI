

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from backend.database import engine, Base
from backend.routers import (
    auth, users, children, assessments, photos,
    medical, nutrition, appointments, notifications, ai
)

load_dotenv()

# Automatically initialize all database tables upon startup
Base.metadata.create_all(bind=engine)

# Create application instance
app = FastAPI(
    title="ChildNutri AI - Pediatric Malnutrition Screening System",
    description="Full-stack AI Platform for Infant Malnourishment Identification and Monitoring",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
if allowed_origins_raw == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads directory structure exists
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(os.path.join(UPLOAD_DIR, "children"), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "ai"), exist_ok=True)

# Mount static file server for uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Register all API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(children.router)
app.include_router(assessments.router)
app.include_router(photos.router)
app.include_router(medical.router)
app.include_router(nutrition.router)
app.include_router(appointments.router)
app.include_router(notifications.router)
app.include_router(ai.router)

# Mount frontend static directory at root so web interface is immediately accessible
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
