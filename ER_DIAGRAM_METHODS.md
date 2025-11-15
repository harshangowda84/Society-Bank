# ER Diagram Generation - Available Methods

## 1. **Online Tools (No Installation Required)**

### A. **DbDiagram.io** (Recommended - Best Quality)
- **Website**: https://dbdiagram.io/
- **Steps**:
  1. Go to https://dbdiagram.io/
  2. Create new diagram
  3. Copy and paste the SQL schema from your database
  4. Or manually define your entities
  5. Export as PNG, SVG, or PDF
- **Pros**: Beautiful output, free, no installation
- **Cons**: Need to define schema manually

### B. **Quick DBD** (SQL-based)
- **Website**: https://www.quickdatabasediagrams.com/
- **Steps**:
  1. Paste SQL DDL statements
  2. Auto-generates ER diagram
  3. Export as PNG or PDF
- **Pros**: Quick, auto-generates from SQL
- **Cons**: Limited customization

### C. **Lucidchart** (Professional)
- **Website**: https://www.lucidchart.com/
- **Steps**: 
  1. Create database diagram template
  2. Draw entities and relationships
  3. Export as PNG, PDF, SVG
- **Pros**: Professional quality, many export options
- **Cons**: Paid (has free tier)

### D. **Draw.io** (Miro Diagram)
- **Website**: https://draw.io/
- **Steps**:
  1. Use database shapes from library
  2. Create entities manually
  3. Export as PNG, PDF, SVG
- **Pros**: Free, flexible
- **Cons**: Manual drawing required

---

## 2. **Command-Line Tools**

### A. **SchemaCrawler** (Best for SQLite)
```bash
# Install SchemaCrawler
# Download from: https://www.schemacrawler.com/

# Generate diagram
schemacrawler.sh --server=sqlite --database=backend/instance/society_bank.db --command=diagram --output-format=png --output-file=er_diagram.png
```
- **Pros**: Reads directly from database, high quality
- **Cons**: Requires Java installation

### B. **pgAdmin** (PostgreSQL, but works with others)
```bash
# If you upgrade to PostgreSQL
# Export schema as diagram through pgAdmin UI
```

### C. **MySQL Workbench** (Database modeling tool)
```bash
# For MySQL databases
# Built-in ER diagram reverse engineering
```

### D. **DBeaver** (Universal Database Tool - Recommended)
```bash
# Install: https://dbeaver.io/download/
# Steps:
# 1. Connect to your SQLite database
# 2. Right-click database → ER Diagram
# 3. Export as PNG/PDF
```
- **Pros**: Works with any database, beautiful output, free
- **Cons**: Need to install DBeaver

---

## 3. **Python Libraries**

### A. **SQLAlchemy Diagram** (Simple)
```bash
pip install sqlalchemy-schemadisplay
```
Create `generate_diagram.py`:
```python
from sqlalchemy import MetaData, create_engine
from sqlalchemy_schemadisplay import create_schema_graph
import os

# Create engine
engine = create_engine('sqlite:///backend/instance/society_bank.db')

# Create diagram
graph = create_schema_graph(metadata=MetaData(bind=engine), show_indexes=True)

# Save as PNG
graph.write_png('er_diagram.png')
```

**Run**:
```bash
python generate_diagram.py
```

### B. **SQLAlchemy Automap + Graphviz** (Advanced)
```bash
# Install Graphviz first: https://graphviz.org/download/
# Then install Python package:
pip install pygraphviz

# Then use eralchemy2
pip install eralchemy2
```

### C. **SQAlchemy to PlantUML** (Recommended Alternative)
```bash
pip install sqlacodegen
```
```bash
# Generate PlantUML diagram code
sqlacodegen sqlite:///backend/instance/society_bank.db > schema.py

# Then convert to diagram on: https://www.plantuml.com/plantuml/uml/
```

---

## 4. **SQL Dump Method (Recommended for SQLite)**

### A. **Export and Convert**
```bash
# Dump SQLite schema
sqlite3 backend/instance/society_bank.db .schema > schema.sql

# Then use on DbDiagram.io or Quick DBD
```

---

## **My Recommendations (Ranked)**

### **Option 1: DBeaver (Best Overall)**
- Install DBeaver Community (free)
- Open your SQLite database
- Right-click → Database Diagram → ER Diagram
- Export as PNG/PDF
- **Quality: Excellent** ⭐⭐⭐⭐⭐

### **Option 2: DbDiagram.io (Easiest)**
- No installation needed
- Upload SQL schema
- Beautiful diagrams
- Export PNG/PDF/SVG
- **Quality: Excellent** ⭐⭐⭐⭐⭐

### **Option 3: SchemaCrawler (Most Automated)**
```bash
# Most reliable for SQLite
schemacrawler -server=sqlite -database=backend/instance/society_bank.db -command=diagram -outputformat=png -outputfile=er_diagram.png
```
- **Quality: Very Good** ⭐⭐⭐⭐

### **Option 4: Python Script (SQLAlchemy)**
```bash
pip install sqlalchemy-schemadisplay
python generate_diagram.py
```
- **Quality: Good** ⭐⭐⭐⭐

---

## **Quick Start: Using DbDiagram.io**

1. Export your schema:
```bash
sqlite3 backend/instance/society_bank.db .schema > schema.sql
```

2. Go to https://dbdiagram.io/

3. Paste this SQL in the editor:
```sql
Table Member {
  id int [pk]
  name varchar
  username varchar [unique]
  password_hash varchar
  account_no varchar [unique]
  dob date
  designation varchar
  is_approved boolean
  created_at timestamp
}

Table Account {
  id int [pk]
  member_id int [fk, ref: > Member.id]
  account_number varchar
  balance decimal
  account_type varchar
}

Table Loan {
  id int [pk]
  member_id int [fk, ref: > Member.id]
  amount decimal
  interest_rate decimal
  tenure_months int
  status varchar
}

Table Deposit {
  id int [pk]
  member_id int [fk, ref: > Member.id]
  amount decimal
  type varchar
  maturity_date date
  status varchar
}

Table Share {
  id int [pk]
  member_id int [fk, ref: > Member.id]
  quantity int
  amount_per_share decimal
  total_amount decimal
}

Table Transaction {
  id int [pk]
  account_id int [fk, ref: > Account.id]
  type varchar
  amount decimal
  description text
}

Table LoanRepayment {
  id int [pk]
  loan_id int [fk, ref: > Loan.id]
  principal_paid decimal
  interest_paid decimal
  payment_method varchar
}

Table Announcement {
  id int [pk]
  message text
  created_at timestamp
}
```

4. Click **Export** → Choose PNG/PDF → Download

---

## **Commands Summary**

| Tool | Command | Output |
|------|---------|--------|
| **DbDiagram.io** | Web UI | PNG, SVG, PDF |
| **SchemaCrawler** | `schemacrawler ... -outputformat=png` | PNG |
| **DBeaver** | GUI: Right-click DB | PNG, SVG, PDF |
| **SQLAlchemy** | `python generate_diagram.py` | PNG |
| **Draw.io** | Web UI | PNG, SVG, PDF |

---

## **What I Recommend for Your Project**

✅ **Best Option**: **DBeaver** (Professional, free, easy)
- Download: https://dbeaver.io/download/
- Install and connect to your SQLite database
- Generate ER diagram with one click

✅ **Second Option**: **DbDiagram.io** (No installation)
- Just paste your SQL schema
- Get professional diagram instantly
- No software needed

❌ **Not Recommended**: Matplotlib-based scripts (too basic)
