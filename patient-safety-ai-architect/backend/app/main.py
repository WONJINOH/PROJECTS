"""
Patient Safety Incident Reporting System - FastAPI Application

Phase 1 Features:
- Incident intake (Common page)
- Fall details
- Medication details
- Approvals workflow
- Actions tracking
- Attachments (local storage)

Phase 1.5 Features (Risk Management):
- Risk Register (P×S Matrix)
- Risk Assessment history
- PSR → Risk auto-escalation
- Just Culture classification
- Incident Timeline feedback

Phase E Features:
- Pressure Ulcer Management
- Auto-calculated improvement rate (monthly scheduler)
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    incidents,
    attachments,
    approvals,
    auth,
    indicators,
    actions,
    fall_details,
    medication_details,
    infection_details,
    pressure_ulcer_details,
    transfusion_details,
    thermal_injury_details,
    procedure_details,
    environment_details,
    security_details,
    risks,
    dashboard,
    lookup,
    pressure_ulcer_management,
)
from app.security.audit import AuditMiddleware
from app.tasks.scheduler import start_scheduler, shutdown_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Patient Safety API...")
    print("Starting Patient Safety API...")

    # Start background scheduler
    try:
        start_scheduler()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start scheduler: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Patient Safety API...")
    print("Shutting down Patient Safety API...")

    # Stop background scheduler
    try:
        shutdown_scheduler()
        logger.info("Background scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping scheduler: {e}")


app = FastAPI(
    title="Patient Safety Incident Reporting API",
    description="Internal QI system for patient safety incident management",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    # Disable automatic trailing slash redirects to prevent 307 redirects
    # that lose Authorization headers
    redirect_slashes=False,
)

# CORS Configuration
# In development, allow all origins for easier testing
# In production, restrict to specific domains
import os
_is_dev = os.getenv("ENVIRONMENT", "development") == "development"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _is_dev else [
        "http://localhost:3000",
        "https://localhost:3443",
        "https://localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Audit Logging Middleware
app.add_middleware(AuditMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["Attachments"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(indicators.router, prefix="/api/indicators", tags=["Indicators"])
app.include_router(actions.router, prefix="/api/actions", tags=["Actions"])
app.include_router(fall_details.router, prefix="/api/fall-details", tags=["Fall Details"])
app.include_router(medication_details.router, prefix="/api/medication-details", tags=["Medication Details"])
app.include_router(infection_details.router, prefix="/api/infection-details", tags=["Infection Details"])
app.include_router(pressure_ulcer_details.router, prefix="/api/pressure-ulcer-details", tags=["Pressure Ulcer Details"])
app.include_router(transfusion_details.router, prefix="/api/transfusion-details", tags=["Transfusion Details"])
app.include_router(thermal_injury_details.router, prefix="/api/thermal-injury-details", tags=["Thermal Injury Details"])
app.include_router(procedure_details.router, prefix="/api/procedure-details", tags=["Procedure Details"])
app.include_router(environment_details.router, prefix="/api/environment-details", tags=["Environment Details"])
app.include_router(security_details.router, prefix="/api/security-details", tags=["Security Details"])
app.include_router(risks.router, prefix="/api/risks", tags=["Risk Management"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(lookup.router, prefix="/api/lookup", tags=["Lookup (진료과/주치의)"])
app.include_router(pressure_ulcer_management.router, prefix="/api/pressure-ulcers", tags=["Pressure Ulcer Management"])


@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Patient Safety Incident Reporting API",
        "docs": "/api/docs",
    }
