from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Task
from ..auth import get_current_user, verify_password, hash_password

router = APIRouter(prefix="/profile")
templates = Jinja2Templates(directory="app/templates")


@router.get("", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    pending_count = db.query(Task).filter(Task.status == "pending").count() if user.role == "admin" else 0
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": user,
        "pending_count": pending_count,
        "success": None,
        "error": None,
    })


@router.post("/update")
def update_profile(request: Request, display_name: str = Form(...),
                   color: str = Form("#4f46e5"), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    user.display_name = display_name
    user.color = color
    db.commit()
    pending_count = db.query(Task).filter(Task.status == "pending").count() if user.role == "admin" else 0
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "current_user": user,
        "pending_count": pending_count,
        "success": "Profile updated!",
        "error": None,
    })


@router.post("/password")
def change_password(request: Request, current_password: str = Form(...),
                    new_password: str = Form(...), new_password2: str = Form(...),
                    db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    pending_count = db.query(Task).filter(Task.status == "pending").count() if user.role == "admin" else 0

    if not verify_password(current_password, user.hashed_password):
        return templates.TemplateResponse("profile.html", {
            "request": request, "current_user": user,
            "pending_count": pending_count,
            "error": "Current password is incorrect.", "success": None,
        })
    if new_password != new_password2:
        return templates.TemplateResponse("profile.html", {
            "request": request, "current_user": user,
            "pending_count": pending_count,
            "error": "New passwords do not match.", "success": None,
        })
    if len(new_password) < 6:
        return templates.TemplateResponse("profile.html", {
            "request": request, "current_user": user,
            "pending_count": pending_count,
            "error": "Password must be at least 6 characters.", "success": None,
        })

    user.hashed_password = hash_password(new_password)
    db.commit()
    return templates.TemplateResponse("profile.html", {
        "request": request, "current_user": user,
        "pending_count": pending_count,
        "success": "Password changed successfully!", "error": None,
    })


@router.post("/suggest-task")
def suggest_task(request: Request, name: str = Form(...),
                 points: int = Form(...), icon: str = Form("🏠"),
                 db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    task = Task(name=name, points=points, icon=icon, status="pending", suggested_by=user.id)
    db.add(task)
    db.commit()
    pending_count = db.query(Task).filter(Task.status == "pending").count() if user.role == "admin" else 0
    return templates.TemplateResponse("profile.html", {
        "request": request, "current_user": user,
        "pending_count": pending_count,
        "success": "Task suggestion submitted! The admin will review it.", "error": None,
    })
