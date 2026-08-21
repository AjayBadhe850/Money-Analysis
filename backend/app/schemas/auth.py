from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Optional[UserRole] = UserRole.EMPLOYEE
    company_name: Optional[str] = "Acme Global Technologies Inc."


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    company_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


TokenResponse.model_rebuild()
