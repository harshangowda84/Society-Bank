#!/usr/bin/env python
"""
Script to create an admin user in the database
"""
from db import SessionLocal, engine
import models
from datetime import datetime

# Drop all existing tables and recreate them with new schema
models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)

def create_admin_user():
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(models.Member).filter(
            models.Member.username == "admin"
        ).first()
        
        if existing_admin:
            print("Admin user already exists!")
            db.close()
            return
        
        # Create new admin user
        admin = models.Member(
            name="Admin",
            username="admin",
            dob="2000-01-01",
            designation="Administrator",
            mobile="9000000000",
            aadhaar="000000000000",
            pan="AAAA00000A",
            is_approved=True,
            application_date=datetime.now().strftime("%Y-%m-%d"),
            bank_account="ACC-ADMIN-0001",
            account_no="ACC-ADMIN-0001",
            address="Admin Office",
            nominee_name="Admin Nominee",
            nominee_relationship="Self"
        )
        
        # Set password
        admin.set_password("Admin@123")
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"✓ Admin user created successfully!")
        print(f"  Username: admin")
        print(f"  Password: admin123")
        print(f"  ID: {admin.id}")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_admin_user()
