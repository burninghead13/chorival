from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from ..database import get_db
from ..models import User, Task, Invitation
from ..auth import get_current_user, hash_password

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def get_admin(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        return None
    return user


@router.get("", response_class=HTMLResponse)
def admin_panel(request: Request, db: Session = Depends(get_db)):
    admin = get_admin(request, db)
    if not admin:
        return RedirectResponse("/", status_code=302)

    tasks = db.query(Task).order_by(Task.status, Task.name).all()
    users = db.query(User).order_by(User.created_at).all()
    invitations = db.query(Invitation).order_by(Invitation.created_at.desc()).limit(10).all()
    pending_count = db.query(Task).filter(Task.status == "pending").count()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "current_user": admin,
        "tasks": tasks,
        "users": users,
        "invitations": invitations,
        "pending_count": pending_count,
        "base_url": str(request.base_url).rstrip("/"),
    })


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.post("/task/add")
def add_task(request: Request, name: str = Form(...), points: int = Form(...),
             icon: str = Form("🏠"), db: Session = Depends(get_db)):
    if not get_admin(request, db):
        return RedirectResponse("/", status_code=302)
    task = Task(name=name, points=points, icon=icon, status="approved")
    db.add(task)
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/task/edit/{task_id}")
def edit_task(task_id: int, request: Request, name: str = Form(...),
              points: int = Form(...), icon: str = Form("🏠"),
              active: bool = Form(False), db: Session = Depends(get_db)):
    if not get_admin(request, db):
        return RedirectResponse("/", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.name = name
        task.points = points
        task.icon = icon
        task.active = active
        db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/task/approve/{task_id}")
def approve_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    if not get_admin(request, db):
        return RedirectResponse("/", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = "approved"
        task.active = True
        db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/task/reject/{task_id}")
def reject_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    if not get_admin(request, db):
        return RedirectResponse("/", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = "rejected"
        db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/task/delete/{task_id}")
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    if not get_admin(request, db):
        return RedirectResponse("/", status_code=302)
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    return RedirectResponse("/admin", status_code=302)


# ── Users ─────────────────────────────────────────────────────────────────────

@router.post("/user/edit/{user_id}")
def edit_user(user_id: int, request: Request, display_name: str = Form(...),
              color: str = Form("#4f46e5"), role: str = Form("member"),
              db: Session = Depends(get_db)):
    admin = get_admin(request, db)
    if not admin:
        return RedirectResponse("/", status_code=302)
    user = db.query(User).filter(User.id == user_id).first()
    if user and not (user.role == "admin" and user.id != admin.id):
        user.display_name = display_name
        user.color = color
        if user.id != admin.id:
            user.role = role
        db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/user/deactivate/{user_id}")
def deactivate_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = get_admin(request, db)
    if not admin:
        return RedirectResponse("/", status_code=302)
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.id != admin.id:
        user.is_active = False
        db.commit()
    return RedirectResponse("/admin", status_code=302)


# ── Invitations ───────────────────────────────────────────────────────────────

@router.post("/invite/create")
def create_invite(request: Request, db: Session = Depends(get_db)):
    admin = get_admin(request, db)
    if not admin:
        return RedirectResponse("/", status_code=302)
    token = secrets.token_urlsafe(32)
    invite = Invitation(
        token=token,
        created_by_id=admin.id,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(invite)
    db.commit()
    return RedirectResponse("/admin", status_code=302)


@router.post("/invite/delete/{invite_id}")
def delete_invite(invite_id: int, request: Request, db: Session = Depends(get_db)):
    if not get_admin(request, db):
        return RedirectResponse("/", status_code=302)
    invite = db.query(Invitation).filter(Invitation.id == invite_id).first()
    if invite:
        db.delete(invite)
        db.commit()
    return RedirectResponse("/admin", status_code=302)
