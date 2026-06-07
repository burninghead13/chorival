from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from ..database import get_db
from ..models import User, Task, Entry
from ..auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def current_month() -> str:
    return date.today().strftime("%Y-%m")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    month = current_month()
    users = db.query(User).filter(User.is_active == True).all()
    tasks = db.query(Task).filter(Task.active == True, Task.status == "approved").order_by(Task.name).all()

    # Scores for current month
    scores = {}
    for u in users:
        total = db.query(func.coalesce(func.sum(Entry.points), 0)).filter(
            Entry.user_id == u.id, Entry.month == month
        ).scalar()
        scores[u.id] = total

    # Recent entries
    recent = db.query(Entry).filter(Entry.month == month)\
        .order_by(Entry.created_at.desc()).limit(20).all()

    # Pending tasks count for admin badge
    pending_count = 0
    if user.role == "admin":
        pending_count = db.query(Task).filter(Task.status == "pending").count()

    month_label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    max_score = max(scores.values()) if scores else 0

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": user,
        "users": users,
        "tasks": tasks,
        "scores": scores,
        "recent": recent,
        "month_label": month_label,
        "max_score": max_score,
        "pending_count": pending_count,
    })


@router.post("/entry/add", response_class=HTMLResponse)
def add_entry(request: Request, task_id: int = Form(...),
              db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    task = db.query(Task).filter(Task.id == task_id, Task.active == True, Task.status == "approved").first()
    if task:
        entry = Entry(
            user_id=user.id,
            task_id=task.id,
            points=task.points,
            month=current_month()
        )
        db.add(entry)
        db.commit()
    return RedirectResponse("/", status_code=302)


@router.post("/entry/delete/{entry_id}")
def delete_entry(entry_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    entry = db.query(Entry).filter(Entry.id == entry_id).first()
    if entry and (user.role == "admin" or entry.user_id == user.id):
        db.delete(entry)
        db.commit()
    return RedirectResponse("/", status_code=302)


@router.get("/history", response_class=HTMLResponse)
def history(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    users = db.query(User).filter(User.is_active == True).all()
    months = db.query(Entry.month).distinct().order_by(Entry.month.desc()).all()

    archive = []
    for (month,) in months:
        scores = {}
        for u in users:
            total = db.query(func.coalesce(func.sum(Entry.points), 0)).filter(
                Entry.user_id == u.id, Entry.month == month
            ).scalar()
            scores[u.id] = total
        label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
        archive.append({"month": month, "label": label, "scores": scores})

    pending_count = db.query(Task).filter(Task.status == "pending").count() if user.role == "admin" else 0

    return templates.TemplateResponse("history.html", {
        "request": request,
        "current_user": user,
        "users": users,
        "archive": archive,
        "pending_count": pending_count,
    })


@router.get("/history/{month}", response_class=HTMLResponse)
def history_detail(month: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)

    users = db.query(User).filter(User.is_active == True).all()
    entries = db.query(Entry).filter(Entry.month == month)\
        .order_by(Entry.created_at.desc()).all()

    scores = {}
    for u in users:
        total = db.query(func.coalesce(func.sum(Entry.points), 0)).filter(
            Entry.user_id == u.id, Entry.month == month
        ).scalar()
        scores[u.id] = total

    label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    max_score = max(scores.values()) if scores else 0
    pending_count = db.query(Task).filter(Task.status == "pending").count() if user.role == "admin" else 0

    return templates.TemplateResponse("history_detail.html", {
        "request": request,
        "current_user": user,
        "users": users,
        "entries": entries,
        "scores": scores,
        "label": label,
        "max_score": max_score,
        "pending_count": pending_count,
    })
