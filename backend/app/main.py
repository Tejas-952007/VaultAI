from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.routes import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VaultAI Sovereign On-Premise AI Workbench API"
)

# Configure CORS — allow only the local Next.js dev origins.
# In production, replace with the actual deployed frontend URL.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' http://localhost:8000 http://localhost:3000;"
    return response


@app.middleware("http")
async def enforce_api_key(request: Request, call_next):
    if not settings.VAULTAI_API_KEY:
        return await call_next(request)

    if request.url.path.startswith(f"{settings.API_V1_STR}/health"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    api_key_header = request.headers.get("X-API-Key", "")
    expected = settings.VAULTAI_API_KEY.strip()
    provided = ""
    if auth_header.startswith("Bearer "):
        provided = auth_header.split(" ", 1)[1]
    elif api_key_header:
        provided = api_key_header

    if provided != expected:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail={"status": "error", "error": {"code": "AUTH_REQUIRED", "message": "API key required for this local prototype."}})
    return await call_next(request)


# Include v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
