"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, RedirectResponse
from pymongo.errors import PyMongoError
import logging
import os
from pathlib import Path
from .backend import routers, database

# Initialize web host
app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities"
)

# Initialize database with sample data if empty
database.init_database()

# Mount the static files directory for serving the frontend
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

# Root endpoint to redirect to static index.html
@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

# Include routers
app.include_router(routers.activities.router)
app.include_router(routers.auth.router)
app.include_router(routers.announcements.router)


@app.exception_handler(PyMongoError)
async def database_error(request: Request, error: PyMongoError):
    logging.getLogger(__name__).error("Database request failed", exc_info=error)
    return JSONResponse(status_code=503, content={"detail": "Service temporarily unavailable"})
