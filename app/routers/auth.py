from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from ..database import get_db
from ..models import User, Invitation
from ..auth import verify_password, create_token, hash_password, COOKIE_NAME, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid username or password"
        })
    token = create_token(user.id)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(COOKIE_NAME, token, httponly=True, max_age=60 * 60 * 24 * 30, samesite="lax")
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/register/{token}", response_class=HTMLResponse)
def register_page(token: str, request: Request, db: Session = Depends(get_db)):
    invite = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.used == False,
        Invitation.expires_at > datetime.utcnow()
    ).first()
    if not invite:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "This invitation link is invalid or has expired."
        })
    return templates.TemplateResponse("register.html", {"request": request, "token": token, "error": None})


@router.post("/register/{token}", response_class=HTMLResponse)
def register(token: str, request: Request,
             username: str = Form(...),
             display_name: str = Form(...),
             password: str = Form(...),
             password2: str = Form(...),
             db: Session = Depends(get_db)):
    invite = db.query(Invitation).filter(
        Invitation.token == token,
        Invitation.used == False,
        Invitation.expires_at > datetime.utcnow()
    ).first()
    if not invite:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "message": "This invitation link is invalid or has expired."
        })

    error = None
    if password != password2:
        error = "Passwords do not match."
    elif len(password) < 6:
        error = "Password must be at least 6 characters."
    elif db.query(User).filter(User.username == username).first():
        error = "Username already taken."

    if error:
        return templates.TemplateResponse("register.html", {
            "request": request, "token": token, "error": error
        })

    user = User(
        username=username,
        display_name=display_name,
        hashed_password=hash_password(password),
        role="member"
    )
    db.add(user)
    invite.used = True
    invite.used_by = username
    db.commit()

    auth_token = create_token(user.id)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(COOKIE_NAME, auth_token, httponly=True, max_age=60 * 60 * 24 * 30, samesite="lax")
    return response
