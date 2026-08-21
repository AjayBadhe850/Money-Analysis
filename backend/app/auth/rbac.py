from typing import List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.user import User, UserRole
from app.auth.jwt import decode_access_token
from app.core.exceptions import CredentialsException, PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise CredentialsException(detail="Not authenticated")
    
    payload = decode_access_token(token)
    if payload is None:
        raise CredentialsException(detail="Invalid or expired authentication token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise CredentialsException(detail="Token missing user identity")
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise CredentialsException(detail="User not found")
    
    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Dependency factory to enforce role-based access control.
    Example: Depends(require_roles([UserRole.ADMIN, UserRole.FINANCE_MANAGER]))
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        # Admin always has access to everything
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        if current_user.role not in allowed_roles:
            raise PermissionDeniedException(
                detail=f"Operation not permitted for role '{current_user.role.value}'. Required: {[r.value for r in allowed_roles]}"
            )
        return current_user
    
    return role_checker
