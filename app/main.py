from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(
    title="SONiC OpenConfig Diagnostic Gateway",
    description=(
        "Network diagnostic gateway that discovers device capabilities "
        "through gNMI, retrieves interface state using OpenConfig and "
        "Cisco-native YANG models, and runs evidence-backed diagnostic rules."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Routers ──────────────────────────────────────────────────────────

from app.api.health import router as health_router
from app.api.discovery import router as discovery_router
from app.api.diagnostics import router as diagnostics_router
from app.api.changes import router as changes_router

app.include_router(health_router)
app.include_router(discovery_router)
app.include_router(diagnostics_router)
app.include_router(changes_router)

# ── Global error handlers ────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(_request: Request, exc: FileNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Required fixture or configuration file not found. "
                "Check DEVICE_MODE and fixture directory."
            ),
        },
    )

@app.exception_handler(Exception)
async def generic_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc}"},
    )
