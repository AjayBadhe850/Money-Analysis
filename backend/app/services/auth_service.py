from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.company import Company
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.exceptions import CredentialsException, ValidationException


def register_user(db: Session, data: UserRegister) -> TokenResponse:
    # Check if user already exists
    existing = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if existing:
        raise ValidationException(detail="Email is already registered")

    # Find or create default company
    company_name = data.company_name or "Acme Global Technologies Inc."
    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        company = Company(name=company_name, industry="Technology", currency="USD")
        db.add(company)
        db.flush()

    new_user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role=data.role or UserRole.EMPLOYEE,
        company_id=company.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(subject=str(new_user.id))
    user_resp = UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        company_id=new_user.company_id
    )

    return TokenResponse(access_token=access_token, user=user_resp)


def authenticate_user(db: Session, data: UserLogin) -> TokenResponse:
    user = db.query(User).filter(User.email == data.email.lower().strip()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise CredentialsException(detail="Invalid email or password")

    access_token = create_access_token(subject=str(user.id))
    user_resp = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        company_id=user.company_id
    )

    return TokenResponse(access_token=access_token, user=user_resp)
