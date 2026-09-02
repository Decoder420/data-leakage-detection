"""Main FastAPI Application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from backend.api.routes import datasets, agents, allocations, analysis, simulation, reports

app = FastAPI(
    title="Data Leakage Detection & Attribution Platform API",
    description="Enterprise API for Probabilistic Data Leak Attribution & Synthetic Canary Honeytoken Monitoring",
    version="2.0.0"
)

# Enable CORS for local React development and Docker setups
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(datasets.router)
app.include_router(agents.router)
app.include_router(allocations.router)
app.include_router(analysis.router)
app.include_router(simulation.router)
app.include_router(reports.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Data Leakage Detection Engine",
        "version": "2.0.0",
        "features": [
            "Papadimitriou Guilt Probability Model",
            "Context-Aware Synthetic Canary Generation",
            "Smart Overlap Minimization Allocation",
            "Monte Carlo Resilience Simulator",
            "Enterprise Forensic Audit Reports"
        ]
    }


# If frontend production build exists, serve it
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
