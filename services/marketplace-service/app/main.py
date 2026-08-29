from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import marketplace
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )

@app.get("/health")
def health():
    return {"status": "healthy", "service": "marketplace-service"}

@app.get("/api/v1/marketplace/health")
def health_prefixed():
    return {"status": "healthy", "service": "marketplace-service"}

app.include_router(marketplace.router, prefix="/api/v1/marketplace", tags=["marketplace"])
