#!/usr/bin/env python3

import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db.database import engine, Base
from app.models.user import User, UserSession, UserRole
from app.auth.auth_utils import get_password_hash
from sqlalchemy.orm import sessionmaker

def update_admin_email():
    """Update admin email from old to new format"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Find admin with old email
        admin_old = session.query(User).filter(User.email == "admin@iml.com").first()
        if admin_old:
            print(f"Found admin with old email: {admin_old.email}")
            # Update to new email
            admin_old.email = "admin@imli.com"
            session.commit()
            print(f"Updated admin email to: admin@imli.com")
            return True
        
        # Check if new email admin exists
        admin_new = session.query(User).filter(User.email == "admin@imli.com").first()
        if admin_new:
            print(f"Admin with correct email already exists: {admin_new.email}")
            return True
            
        print("No admin user found!")
        return False
            
    except Exception as e:
        print(f"Error updating admin email: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def check_all_users():
    """Check all users in database"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        users = session.query(User).all()
        print(f"Total users in database: {len(users)}")
        
        for user in users:
            print(f"Email: {user.email}")
            print(f"Full Name: {user.full_name}")
            print(f"Role: {user.role}")
            print(f"Active: {user.is_active}")
            print("---")
            
    except Exception as e:
        print(f"Error checking users: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("Checking all users...")
    check_all_users()
    print("\nUpdating admin email...")
    success = update_admin_email()
    
    if success:
        print("\nFinal check:")
        check_all_users()
