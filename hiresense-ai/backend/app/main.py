from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import Base, engine
from app.api.v1 import api_router
import app.models  # noqa: F401  (ensures all models are registered on Base before create_all)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "HireSense AI — An Explainable AI-Powered Candidate Screening and Ranking Decision "
        "Support System. This API never autonomously advances, rejects, or hires a candidate; "
        "all state-changing hiring decisions require an authenticated human action."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
