#!/usr/bin/env python
"""
Initialize default loan types and interest rates in the database
Run this script once after setting up the application
"""

import sys
sys.path.insert(0, 'backend')

from db import SessionLocal
import models

def initialize_loan_types():
    """Initialize default loan types with interest rates"""
    db = SessionLocal()
    
    loan_types = [
        {
            'loan_type': 'personal',
            'interest_rate': 12.5,
            'min_amount': 10000,
            'max_amount': 5000000
        },
        {
            'loan_type': 'education',
            'interest_rate': 9.5,
            'min_amount': 50000,
            'max_amount': 25000000
        },
        {
            'loan_type': 'home',
            'interest_rate': 8.5,
            'min_amount': 500000,
            'max_amount': 50000000
        },
        {
            'loan_type': 'vehicle',
            'interest_rate': 10.5,
            'min_amount': 50000,
            'max_amount': 10000000
        },
        {
            'loan_type': 'business',
            'interest_rate': 11.5,
            'min_amount': 100000,
            'max_amount': 50000000
        },
        {
            'loan_type': 'emergency',
            'interest_rate': 14.5,
            'min_amount': 10000,
            'max_amount': 500000
        }
    ]
    
    try:
        for loan_type_data in loan_types:
            # Check if loan type already exists
            existing = db.query(models.LoanInterestRate).filter_by(
                loan_type=loan_type_data['loan_type']
            ).first()
            
            if not existing:
                loan_type = models.LoanInterestRate(**loan_type_data)
                db.add(loan_type)
                print(f"✓ Added {loan_type_data['loan_type']} with {loan_type_data['interest_rate']}% interest rate")
            else:
                print(f"⊘ {loan_type_data['loan_type']} already exists, skipping...")
        
        db.commit()
        print("\n✓ Loan types initialized successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error initializing loan types: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    print("Initializing default loan types...")
    initialize_loan_types()
