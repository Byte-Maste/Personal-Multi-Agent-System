from uuid import UUID
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str | None = None

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UpdateUserRequest(BaseModel):
    name: str | None = None
    monthly_income: float | None = None
    emergency_fund_target: float | None = None
    risk_profile: str | None = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str | None = None
    monthly_income: float | None = None
    currency: str = "INR"
    emergency_fund_target: float | None = None
    risk_profile: str | None = None
    is_active: bool = True

    class Config:
        from_attributes = True
