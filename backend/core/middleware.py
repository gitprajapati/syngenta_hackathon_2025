#core/middleware.py
from fastapi import Request, HTTPException
from jose import JWTError
from core.security import verify_token
from models.base_models import User

def requires_role(allowed_roles: list):
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            db = request.state.db 
            auth_header = request.headers.get("Authorization")
            
            if not auth_header:
                raise HTTPException(status_code=401, detail="Not authenticated: Authorization header missing")
            
            try:
                scheme, token = auth_header.split()
                if scheme.lower() != "bearer":
                    raise HTTPException(status_code=401, detail="Not authenticated: Authorization scheme not Bearer")
            except ValueError:
                raise HTTPException(status_code=401, detail="Not authenticated: Invalid Authorization header format")

            try:
                payload = verify_token(token, HTTPException(
                    status_code=401, detail="Invalid credentials"))
                
                user_email = payload.get("sub")
                if not user_email:
                    raise HTTPException(status_code=401, detail="Invalid token: Subject missing")

                user = db.query(User).filter(User.email == user_email).first()
                
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                if not user.is_active:
                     raise HTTPException(status_code=403, detail="User is inactive")
                if not user.role or user.role.name not in allowed_roles:
                    raise HTTPException(status_code=403, detail=f"Insufficient permissions. Requires one of: {', '.join(allowed_roles)}")
                
                request.state.current_user = user
                
                return await func(request, *args, **kwargs)
            
            except JWTError: 
                raise HTTPException(status_code=401, detail="Invalid token")
                
        return wrapper
    return decorator