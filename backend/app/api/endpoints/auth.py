from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.schemas.user import UserOut
from app.services.auth_service import register_user, authenticate_user
from app.services.audit_service import log_activity
from app.auth.rbac import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    res = register_user(db, data)
    log_activity(
        db=db,
        company_id=res.user.company_id or 1,
        user_id=res.user.id,
        action="USER_REGISTER",
        entity="User",
        entity_id=str(res.user.id),
        details=f"User {res.user.email} registered with role {res.user.role.value}",
        ip_address=request.client.host if request.client else None
    )
    return res


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    res = authenticate_user(db, data)
    log_activity(
        db=db,
        company_id=res.user.company_id or 1,
        user_id=res.user.id,
        action="USER_LOGIN",
        entity="User",
        entity_id=str(res.user.id),
        details=f"User {res.user.email} logged in successfully",
        ip_address=request.client.host if request.client else None
    )
    return res


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        company_id=current_user.company_id
    )
