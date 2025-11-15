"""
ER Diagram Generator for Society Bank Database
This script generates an Entity-Relationship diagram from the SQLAlchemy models
"""

from eralchemy2 import render_er
import os

# Set the path to your models file
models_path = "backend/models.py"
output_path = "database_er_diagram.png"

try:
    # Generate ER diagram from SQLAlchemy models
    render_er(f"sqlite:///backend/instance/society_bank.db", output_path)
    print(f"✅ ER Diagram generated successfully: {output_path}")
    print(f"📊 You can now view the diagram in your file explorer")
except Exception as e:
    print(f"❌ Error generating ER diagram: {e}")
    print("\nAlternative method:")
    print("Install eralchemy2 first: pip install eralchemy2")
    print("Then run: python generate_er_diagram.py")
