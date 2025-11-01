"""
FastAPI application entry point for ECU Map Lab backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import maps

app = FastAPI(
    title="ECU Map Lab API",
    description="Web-based ECU map analysis platform backend",
    version="0.1.0",
)

# Configure CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and CRA default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(maps.router, prefix="/api", tags=["maps"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ECU Map Lab API", "version": "0.1.0"}

