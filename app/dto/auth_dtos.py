from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInvitation(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    permissions: List[str] = []

class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: str  # "admin" or "user"
    permissions: Optional[List[str]] = None

class InviteUserResponse(BaseModel):
    message: str
    email: str
    one_time_password: str
    role: str
    permissions: List[str]

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    permissions: List[str]
    
    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class InvitationResponse(BaseModel):
    message: str
    invitation_token: str
    expires_at: datetime

class UserListResponse(BaseModel):
    users: List[UserResponse]

class UpdateUserProfileRequest(BaseModel):
    full_name: Optional[str] = None

class UpdateUserProfileResponse(BaseModel):
    message: str
    user: UserResponse

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordResponse(BaseModel):
    message: str
    email: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

class ResetPasswordResponse(BaseModel):
    message: str
