"""
View Registered Users and Their Credentials
This script displays all registered members in the database
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from db import SessionLocal
from models import Member

def view_users():
    db = SessionLocal()
    
    try:
        members = db.query(Member).all()
        
        if not members:
            print("❌ No registered users found in the database")
            return
        
        print("\n" + "="*100)
        print("REGISTERED USERS - SOCIETY BANK DATABASE")
        print("="*100)
        print(f"\n{'ID':<5} {'Username':<20} {'Name':<25} {'Account No':<18} {'Mobile':<15} {'Status':<12}")
        print("-"*100)
        
        for member in members:
            status = "✅ Approved" if member.is_approved else "⏳ Pending"
            print(f"{member.id:<5} {member.username:<20} {member.name:<25} {member.account_no:<18} {member.mobile:<15} {status:<12}")
        
        print("\n" + "="*100)
        print(f"TOTAL USERS: {len(members)}")
        print("="*100)
        
        # Show detailed info
        print("\n\n📋 DETAILED USER INFORMATION:\n")
        for i, member in enumerate(members, 1):
            print(f"\n{'─'*100}")
            print(f"User #{i}")
            print(f"{'─'*100}")
            print(f"ID:                 {member.id}")
            print(f"Name:               {member.name}")
            print(f"Username:           {member.username}")
            print(f"Account Number:     {member.account_no}")
            print(f"Email:              {member.email or 'N/A'}")
            print(f"Mobile:             {member.mobile or 'N/A'}")
            print(f"Phone:              {member.phone or 'N/A'}")
            print(f"DOB:                {member.dob or 'N/A'}")
            print(f"Designation:        {member.designation or 'N/A'}")
            print(f"Address:            {member.address or 'N/A'}")
            print(f"Gender:             {member.gender or 'N/A'}")
            print(f"Bank Account:       {member.bank_account or 'N/A'}")
            print(f"Aadhaar:            {member.aadhaar or 'N/A'}")
            print(f"PAN:                {member.pan or 'N/A'}")
            print(f"Is Approved:        {'✅ Yes' if member.is_approved else '⏳ No'}")
            print(f"Application Date:   {member.application_date or 'N/A'}")
            print(f"Balance:            ₹{member.balance or 0}")
        
        print(f"\n{'─'*100}\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    view_users()
