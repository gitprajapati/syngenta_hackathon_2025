# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime 

from core.database import get_db
from models.base_models import User, Role, Department, Region 
from core.security import create_access_token, get_current_active_user, oauth2_scheme 
from core.middleware import requires_role 
from schemas.auth import Token, UserCreate, UserResponse 

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()  
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")


    user.last_login = datetime.utcnow()
    db.commit()

    token_data = {"sub": user.email}


    access_token = create_access_token(data=token_data)

    user_role_name = "User"
    if user.role:
        user_role_name = user.role.name

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user_role_name
    }

@router.post("/register", response_model=UserResponse)
async def register_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")


    role = db.query(Role).filter(Role.name == user_data.role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{user_data.role_name}' not found")

    department = db.query(Department).filter(Department.name == user_data.department_name).first()
    if not department:
        raise HTTPException(status_code=404, detail=f"Department '{user_data.department_name}' not found")

    region = db.query(Region).filter(Region.name == user_data.region_name).first()
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{user_data.region_name}' not found")

    new_user = User(
        email=user_data.email,
        employee_id=user_data.employee_id,
        scope=user_data.scope,
        role_id=role.id,
        department_id=department.id,
        region_id=region.id
    )
    new_user.set_password(user_data.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        employee_id=new_user.employee_id,
        is_active=new_user.is_active,
        scope=new_user.scope,
        role=new_user.role.name if new_user.role else None,
        department=new_user.department.name if new_user.department else None,
        region=new_user.region.name if new_user.region else None,
    )


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        employee_id=current_user.employee_id,
        is_active=current_user.is_active,
        scope=current_user.scope,
        role=current_user.role.name if current_user.role else None,
        department=current_user.department.name if current_user.department else None,
        region=current_user.region.name if current_user.region else None,

    )