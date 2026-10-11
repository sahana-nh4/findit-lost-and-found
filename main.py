import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes import router as api_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure uploads folder exists
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    # Initialize SQLite database and demo data
    init_db()
    yield


app = FastAPI(
    title="FindIt — Community Lost & Found Portal",
    description="A responsive local community lost and found portal built with FastAPI, SQLite, and vanilla modern frontend.",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include backend API endpoints
app.include_router(api_router)


@app.get("/", response_class=FileResponse)
async def serve_homepage():
    """Serves the main public portal."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))


@app.get("/admin", response_class=FileResponse)
async def serve_admin_page():
    """Serves the administrative moderation dashboard."""
    return FileResponse(os.path.join(TEMPLATES_DIR, "admin.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
