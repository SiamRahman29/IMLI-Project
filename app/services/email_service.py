from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
import os

class EmailService:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
            MAIL_FROM=os.getenv("MAIL_FROM", "noreply@iml.com"),
            MAIL_PORT=os.getenv("MAIL_PORT", 587),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "IML Trending Analyzer"),
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        self.fm = FastMail(self.conf)
    
    async def send_invitation_email(
        self,
        email: str,
        name: str,
        one_time_password: str,
        role: str,
        permissions: List[str]
    ):
        """Send invitation email to new user"""
        
        permissions_text = ", ".join(permissions) if permissions else "বেসিক অ্যাক্সেস"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #2563eb; margin-bottom: 30px; }}
                .content {{ line-height: 1.6; color: #333; }}
                .credentials {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563eb; }}
                .button {{ display: inline-block; padding: 15px 30px; background-color: #1e40af; color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; font-weight: bold; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
                .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to IML Trending Words Analyzer</h1>
                </div>
                
                <div class="content">
                    <p>Dear {name},</p>

                    <p>You are invited to IML (Bengali Trending Words Analysis System).</p>

                    <div class="credentials">
                        <h3>Login Information:</h3>
                        <p><strong>Email:</strong> {email}</p>
                        <p><strong>Password:</strong> {one_time_password}</p>
                        <p><strong>Your Role:</strong> {role}</p>
                        <p><strong>Permissions:</strong> {permissions_text}</p>
                    </div>

                    <p>Please log in using the information above. For security, change your password after your first login.</p>

                    <a href="{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login" class="button">Login</a>

                    <p>This invitation is valid for 7 days.</p>
                </div>
                
                <div class="footer">
                    <p>This email was sent automatically. Please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = MessageSchema(
            subject="Welcome to IML Trending Words Analyzer",
            recipients=[email],
            body=html,
            subtype="html"
        )
        
        await self.fm.send_message(message)
