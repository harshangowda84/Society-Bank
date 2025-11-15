"""
ER Diagram Generator for Society Bank Database
This script generates an Entity-Relationship diagram from the SQLAlchemy models using matplotlib
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
except ImportError:
    print("Installing required packages...")
    os.system("pip install matplotlib")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Import models to read structure
try:
    from models import Member, Account, Loan, Deposit, Share, LoanRepayment, Transaction, Announcement
    from sqlalchemy import inspect
except ImportError:
    print("Error: Could not import models. Make sure you're in the Society-Bank directory.")
    sys.exit(1)

def create_er_diagram():
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')
    
    # Title
    ax.text(8, 11.5, 'Society Bank - ER Diagram', 
            fontsize=20, fontweight='bold', ha='center')
    
    # Define entity positions
    entities = {
        'Member': (2, 8, ['id (PK)', 'name', 'username', 'password_hash', 
                          'account_no', 'dob', 'is_approved', 'created_at']),
        'Account': (1, 5, ['id (PK)', 'member_id (FK)', 'account_number', 
                           'balance', 'account_type']),
        'Transaction': (1, 2, ['id (PK)', 'account_id (FK)', 'type', 
                               'amount', 'description']),
        'Loan': (6, 8, ['id (PK)', 'member_id (FK)', 'amount', 
                        'interest_rate', 'tenure_months', 'status']),
        'LoanRepayment': (6, 5, ['id (PK)', 'loan_id (FK)', 'principal_paid', 
                                  'interest_paid', 'payment_method']),
        'Deposit': (10, 8, ['id (PK)', 'member_id (FK)', 'amount', 'type', 
                            'maturity_date', 'status']),
        'Share': (14, 8, ['id (PK)', 'member_id (FK)', 'quantity', 
                          'amount_per_share', 'total_amount']),
        'Announcement': (14, 2, ['id (PK)', 'message', 'created_at']),
    }
    
    # Draw entities
    for entity_name, (x, y, attributes) in entities.items():
        # Entity box
        box_height = 0.25 + len(attributes) * 0.15
        entity_box = FancyBboxPatch((x-0.9, y-box_height/2), 1.8, box_height,
                                   boxstyle="round,pad=0.05", 
                                   edgecolor='#0f52ba', facecolor='#e3f2fd',
                                   linewidth=2)
        ax.add_patch(entity_box)
        
        # Entity name
        ax.text(x, y + box_height/2 - 0.15, entity_name, 
               fontsize=11, fontweight='bold', ha='center')
        
        # Attributes
        for i, attr in enumerate(attributes[:6]):  # Show max 6 attributes
            ax.text(x, y + box_height/2 - 0.35 - i*0.15, attr, 
                   fontsize=8, ha='center', style='italic')
    
    # Draw relationships
    relationships = [
        # (from_entity, to_entity, label, style)
        ('Member', 'Account', '1:N', 'Member → Account'),
        ('Member', 'Loan', '1:N', 'Member → Loan'),
        ('Member', 'Deposit', '1:N', 'Member → Deposit'),
        ('Member', 'Share', '1:N', 'Member → Share'),
        ('Account', 'Transaction', '1:N', 'Account → Transaction'),
        ('Loan', 'LoanRepayment', '1:N', 'Loan → Repayment'),
    ]
    
    # Draw arrows
    arrow_positions = [
        ((2, 7.2), (1.5, 5.8)),  # Member to Account
        ((2.5, 7.8), (5.5, 8)),  # Member to Loan
        ((2.5, 8), (9.5, 8)),    # Member to Deposit
        ((2.5, 8.2), (13.5, 8.2)),  # Member to Share
        ((1.5, 4.2), (1.5, 3)),  # Account to Transaction
        ((6, 7.2), (6, 5.8)),    # Loan to Repayment
    ]
    
    for (start, end), (_, _, label, _) in zip(arrow_positions, relationships):
        arrow = FancyArrowPatch(start, end, 
                              arrowstyle='->', mutation_scale=20,
                              color='#9b59b6', linewidth=1.5, 
                              linestyle='--', alpha=0.7)
        ax.add_patch(arrow)
        
        # Add label
        mid_x, mid_y = (start[0] + end[0])/2, (start[1] + end[1])/2
        ax.text(mid_x, mid_y, label, fontsize=7, 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', 
                        edgecolor='#9b59b6', alpha=0.8))
    
    # Add legend
    legend_items = [
        'PK = Primary Key',
        'FK = Foreign Key',
        '1:N = One-to-Many Relationship'
    ]
    
    legend_y = 0.8
    for item in legend_items:
        ax.text(0.5, legend_y, item, fontsize=9, style='italic')
        legend_y -= 0.3
    
    # Add footer
    ax.text(8, 0.2, '© 2025 Bangalore University Society Bank', 
           fontsize=9, ha='center', style='italic', color='gray')
    
    plt.tight_layout()
    
    # Save as PNG
    output_file = 'database_er_diagram.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ ER Diagram saved as: {output_file}")
    
    # Also save as PDF
    output_pdf = 'database_er_diagram.pdf'
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight', facecolor='white')
    print(f"✅ ER Diagram saved as: {output_pdf}")
    
    plt.show()

if __name__ == "__main__":
    print("🔄 Generating ER Diagram...")
    create_er_diagram()
    print("✅ Done! Check the generated files.")

