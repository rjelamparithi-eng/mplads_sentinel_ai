import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.database import engine, Base
from app.routes.health import router as health_router
from app.routes.projects import router as projects_router
from app.routes.ingestion import router as ingestion_router
from app.routes.baselines import router as baselines_router
from app.routes.anomaly import router as anomaly_router
from app.routes.spatial import router as spatial_router
from app.routes.audit import router as audit_router
from app.routes.dashboard import router as dashboard_router

load_dotenv()

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MPLADS Sentinel AI — Backend API",
    description="Explainable Project Review Intelligence Prototype Backend (SIH26102)",
    version="1.0.0"
)

# CORS Configuration
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5174")
origins = [
    frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health_router)
app.include_router(projects_router)
app.include_router(ingestion_router)
app.include_router(baselines_router)
app.include_router(anomaly_router)
app.include_router(spatial_router)
app.include_router(audit_router)
app.include_router(dashboard_router)

@app.get("/")
def root():
    return {
        "title": "MPLADS Sentinel AI API",
        "prototype": "SIH Prototype",
        "use_case": "Designed for MPLADS / MoSPI use case",
        "docs_url": "/docs"
    }
