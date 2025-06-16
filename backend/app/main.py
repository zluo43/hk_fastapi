from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import stations, general

app = FastAPI(title="FastAPI Backend")

# Add CORS middleware FIRST, before any routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using "*"
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
)

# Add a manual OPTIONS handler as backup
@app.options("/{full_path:path}")
async def options_handler():
    return {}

# Include routers AFTER middleware
app.include_router(general.router)
app.include_router(stations.router)
