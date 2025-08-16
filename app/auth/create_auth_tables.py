#!/usr/bin/env python3

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db.database import engine, Base
from app.models.user import User, UserSession, UserRole
from app.models.word import Word, TrendingPhrase, WeeklyTrendingPhrase
from app.auth.auth_utils import get_password_hash
from sqlalchemy.orm import sessionmaker
from datetime import datetime

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully!")

def create_admin_user():
    """Create a default admin user"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if admin already exists
        admin = session.query(User).filter(User.email == "admin@imli.com").first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            email="admin@imli.com",
            full_name="System Administrator",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            permissions=["admin", "read", "write", "generate_words", "manage_users"],
            is_active=True,
            is_invitation_used=True
        )
        
        session.add(admin_user)
        session.commit()
        print("Admin user created successfully!")
        print("Email: admin@imli.com")
        print("Password: admin123")
        print("Please change the password after first login!")
        
    except Exception as e:
        session.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        session.close()

def initialize_database():
    """Initialize database with tables and admin user"""
    print("Initializing database...")
    create_tables()
    print("Creating admin user...")
    create_admin_user()
    print("Database initialization complete!")

if __name__ == "__main__":
    initialize_database()
