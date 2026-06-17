from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.services.auth_service import hash_password, verify_password, create_access_token, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse, UpdateUserRequest

router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        name=body.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    body: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.monthly_income is not None:
        if body.monthly_income <= 0:
            raise HTTPException(status_code=422, detail="monthly_income must be > 0")
        current_user.monthly_income = body.monthly_income
    if body.name is not None:
        current_user.name = body.name
    if body.emergency_fund_target is not None:
        if body.emergency_fund_target < 0:
            raise HTTPException(status_code=422, detail="emergency_fund_target cannot be negative")
        current_user.emergency_fund_target = body.emergency_fund_target
    if body.risk_profile is not None:
        valid_profiles = ("conservative", "moderate", "aggressive")
        if body.risk_profile not in valid_profiles:
            raise HTTPException(status_code=422, detail=f"risk_profile must be one of {valid_profiles}")
        current_user.risk_profile = body.risk_profile
    await db.commit()
    await db.refresh(current_user)
    return current_user
