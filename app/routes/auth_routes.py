from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from app.db.database import get_db
from app.models.user import User, UserRole
from app.auth.auth_utils import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    generate_invitation_token,
    generate_one_time_password,
    generate_reset_otp,
    get_user_permissions
)
from app.auth.dependencies import get_current_admin_user, get_current_active_user
from app.dto.auth_dtos import (
    UserLogin,
    UserResponse,
    TokenResponse,
    InviteUserRequest,
    InviteUserResponse,
    UserListResponse,
    UpdateUserProfileRequest,
    UpdateUserProfileResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/login", response_model=TokenResponse)
async def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user with email and password"""
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Activate user on first login if they have an unused invitation
    if not user.is_active and not user.is_invitation_used:
        user.is_active = True
        user.is_invitation_used = True
        db.commit()
        db.refresh(user)
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is deactivated"
        )
    
    access_token_expires = timedelta(minutes=30 * 24 * 60)  # 30 days
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            permissions=user.permissions or get_user_permissions(user.role),
            is_active=user.is_active
        )
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        permissions=current_user.permissions or get_user_permissions(current_user.role),
        is_active=current_user.is_active
    )

@router.post("/invite", response_model=InviteUserResponse)
async def invite_user(
    invite_request: InviteUserRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Invite a new user (Admin only)"""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == invite_request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Generate invitation token and one-time password
    invitation_token = generate_invitation_token()
    one_time_password = generate_one_time_password()
    
    # Create user with invitation
    user = User(
        email=invite_request.email,
        full_name=invite_request.full_name or invite_request.email.split('@')[0],  # Use email username if no full name
        hashed_password=get_password_hash(one_time_password),
        role=UserRole(invite_request.role),
        permissions=invite_request.permissions or get_user_permissions(UserRole(invite_request.role)),
        invitation_token=invitation_token,
        invitation_expires=datetime.utcnow() + timedelta(days=7),  # 7 days to accept
        is_invitation_used=False,
        is_active=False  # User is inactive until first login
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send invitation email
    try:
        email_service = EmailService()
        await email_service.send_invitation_email(
            email=invite_request.email,
            name=invite_request.full_name or invite_request.email.split('@')[0],
            one_time_password=one_time_password,
            role=invite_request.role,
            permissions=invite_request.permissions or get_user_permissions(UserRole(invite_request.role))
        )
    except Exception as e:
        # Log error but don't fail the invitation
        print(f"Failed to send invitation email: {e}")
    
    return InviteUserResponse(
        message="User invited successfully",
        email=invite_request.email,
        one_time_password=one_time_password,
        role=invite_request.role,
        permissions=invite_request.permissions or get_user_permissions(UserRole(invite_request.role))
    )

@router.get("/users", response_model=UserListResponse)
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """List all users (Admin only)"""
    users = db.query(User).all()
    
    user_list = []
    for user in users:
        user_list.append(UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            permissions=user.permissions or get_user_permissions(user.role),
            is_active=user.is_active
        ))
    
    return UserListResponse(users=user_list)

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deactivate a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Activate a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    db.commit()
    
    return {"message": "User activated successfully"}

@router.put("/profile", response_model=UpdateUserProfileResponse)
async def update_user_profile(
    update_request: UpdateUserProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    if update_request.full_name is not None:
        current_user.full_name = update_request.full_name
    
    db.commit()
    db.refresh(current_user)
    
    return UpdateUserProfileResponse(
        message="Profile updated successfully",
        user=UserResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role.value,
            is_active=current_user.is_active,
            permissions=current_user.permissions
        )
    )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Delete a user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting self
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete yourself"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """Send password reset OTP to user's email"""
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # For security, return success even if user doesn't exist
        return ForgotPasswordResponse(
            message="If the email exists in our system, you will receive a password reset OTP",
            email=request.email
        )
    
    # Generate 6-digit OTP
    otp = generate_reset_otp()
    
    # Set OTP and expiration (15 minutes)
    user.reset_otp = otp
    user.reset_otp_expires = datetime.utcnow() + timedelta(minutes=15)
    db.commit()
    
    # Send OTP email
    try:
        email_service = EmailService()
        await email_service.send_password_reset_otp(
            email=request.email,
            name=user.full_name,
            otp=otp
        )
    except Exception as e:
        # Log error but don't fail the request for security
        print(f"Failed to send OTP email: {e}")
    
    return ForgotPasswordResponse(
        message="If the email exists in our system, you will receive a password reset OTP",
        email=request.email
    )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using OTP"""
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if OTP exists and is not expired
    if not user.reset_otp or not user.reset_otp_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password reset request found for this email"
        )
    
    if datetime.utcnow() > user.reset_otp_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new password reset"
        )
    
    # Verify OTP
    if user.reset_otp != request.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Reset password
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_otp = None
    user.reset_otp_expires = None
    db.commit()
    
    return ResetPasswordResponse(
        message="Password reset successfully"
    )
