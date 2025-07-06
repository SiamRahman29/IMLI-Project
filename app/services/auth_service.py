import jwt
import secrets
import smtplib
from datetime import datetime, timedelta
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.models.user import User, UserSession, UserRole
from app.dto.auth_dtos import UserInvitation, UserResponse, TokenResponse, InvitationResponse
import os

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-make-it-strong")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_user_session(db: Session, user_id: int, token: str) -> UserSession:
        expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        session = UserSession(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(session)
        db.commit()
        return session
    
    @staticmethod
    def generate_invitation_token() -> str:
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_temp_password() -> str:
        return secrets.token_urlsafe(12)
    
    @staticmethod
    def send_invitation_email(email: str, full_name: str, temp_password: str, role: UserRole, permissions: List[str]):
        try:
            msg = MIMEMultipart()
            msg['From'] = SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = "Welcome to BARTA-IML Trending Words Analyzer"

            permissions_text = ", ".join(permissions) if permissions else "General Access"
            role_text = "Admin" if role == UserRole.ADMIN else "User"

            body = f"""
            Dear {full_name},

            You are invited to the BARTA-IML Trending Words Analyzer system.

            Your login information:
            - Email: {email}
            - Temporary Password: {temp_password}
            - Role: {role_text}
            - Permissions: {permissions_text}

            Please use this information to log in to the system.
            For security, change your password after your first login.

            Thank you,
            BARTA-IML Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"Email sending failed: {e}")
            return False
    
    @staticmethod
    def create_invitation(db: Session, invitation_data: UserInvitation) -> InvitationResponse:
        # Check if user already exists
        existing_user = AuthService.get_user_by_email(db, invitation_data.email)
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Generate temporary password and invitation token
        temp_password = AuthService.generate_temp_password()
        invitation_token = AuthService.generate_invitation_token()
        
        # Create user with temporary password
        hashed_password = AuthService.get_password_hash(temp_password)
        
        user = User(
            email=invitation_data.email,
            full_name=invitation_data.full_name,
            hashed_password=hashed_password,
            role=invitation_data.role,
            permissions=invitation_data.permissions,
            invitation_token=invitation_token,
            invitation_expires=datetime.utcnow() + timedelta(days=7),
            is_invitation_used=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send invitation email
        email_sent = AuthService.send_invitation_email(
            invitation_data.email,
            invitation_data.full_name,
            temp_password,
            invitation_data.role,
            invitation_data.permissions
        )
        
        if not email_sent:
            # If email fails, we still create the user but log the error
            print(f"Failed to send invitation email to {invitation_data.email}")
        
        return InvitationResponse(
            message="Invitation sent successfully",
            invitation_token=invitation_token,
            expires_at=user.invitation_expires
        )
