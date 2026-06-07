from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from .database import engine, SessionLocal
from . import models
from .auth import hash_password
from .routers import auth, dashboard, admin, profile

app = FastAPI(title="Chorival", version="2.0.0")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(profile.router)


def init_db():
    models.Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        # Create admin user if none exists
        if db.query(models.User).count() == 0:
            admin_user = models.User(
                username=os.environ.get("ADMIN_USERNAME", "admin"),
                display_name=os.environ.get("ADMIN_DISPLAY_NAME", "Admin"),
                hashed_password=hash_password(os.environ.get("ADMIN_PASSWORD", "changeme")),
                role="admin",
                color="#6366f1",
            )
            db.add(admin_user)

        # Default tasks if none exist
        if db.query(models.Task).count() == 0:
            defaults = [
                ("Vacuuming", 3, "🧹"),
                ("Mopping", 4, "🪣"),
                ("Dishes", 2, "🍽️"),
                ("Grocery shopping", 3, "🛒"),
                ("Doing laundry", 3, "👕"),
                ("Hanging laundry", 2, "📎"),
                ("Taking out trash", 2, "🗑️"),
                ("Cleaning bathroom", 4, "🚿"),
                ("Cooking", 3, "🍳"),
            ]
            for name, points, icon in defaults:
                db.add(models.Task(name=name, points=points, icon=icon, status="approved"))

        db.commit()
    finally:
        db.close()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
