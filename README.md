# Society Bank - Cooperative Banking System

A modern web-based cooperative banking platform built with FastAPI and SQLAlchemy.

## ✨ Features

✅ **Member Management** - Registration with auto-generated account numbers, secure login, member dashboard  
✅ **Loan Management** - Application, admin approval, and flexible repayment options  
✅ **Loan Repayment** - 3 payment types: Full Payment, Custom Amount, or EMI  
✅ **Fixed Deposits** - FD applications with admin approval workflow  
✅ **Share Holdings** - Share investment and portfolio tracking  
✅ **Admin Dashboard** - Complete application approvals and management  
✅ **Transactions** - Member-to-member transfers and tracking  
✅ **Reports** - CSV export for members, loans, deposits, and transactions  

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Windows PowerShell or terminal

### Setup
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
cd backend
pip install -r requirements.txt

# Start server
python main.py
```

### Access
- **Homepage**: http://127.0.0.1:8001/
- **Member Login**: http://127.0.0.1:8001/login
- **Admin Login**: http://127.0.0.1:8001/admin-login

## 📁 Project Structure

```
Society-Bank/
├── backend/
│   ├── main.py              # FastAPI application & routes
│   ├── models.py            # Database models
│   ├── db.py                # Database configuration
│   ├── config.py            # Settings
│   ├── requirements.txt      # Dependencies
│   ├── templates/           # 20 HTML templates
│   │   ├── admin.html
│   │   ├── member_dashboard.html
│   │   ├── loan_repayment.html
│   │   ├── loan_application_form.html
│   │   └── ...
│   └── static/              # CSS & JavaScript
│       ├── css/
│       ├── script.js
│       └── styles.css
├── package.json
├── README.md
└── SETUP.md
```

## 🔧 Key APIs

### Member Endpoints
- `GET /member-dashboard` - View dashboard
- `POST /member/apply-loan` - Apply for loan
- `POST /member/apply-fd` - Apply for FD
- `POST /member/repay-loan` - Record repayment
- `GET /api/member/loans` - Get active loans (JSON)

### Admin Endpoints
- `GET /admin` - Admin dashboard
- `GET /admin/approvals` - View pending approvals
- `POST /admin/approve-loan` - Approve loan
- `POST /admin/approve-fd` - Approve FD

## 💾 Database Models

- **Member** - User accounts and personal details
- **Account** - Bank accounts (Savings/Current)
- **Loan** - Loan applications and status
- **LoanRepayment** - Repayment tracking
- **Deposit** - Fixed deposit management
- **Share** - Share holdings
- **Transaction** - All transactions

## 🔐 Security

✅ Bcrypt password hashing  
✅ HttpOnly secure cookies  
✅ SQL injection prevention (ORM)  
✅ Role-based access control  
✅ CSRF protection  

## 🎯 Loan Repayment Options

The new loan repayment page supports:

1. **Full Payment** - Pay entire loan including interest at once
2. **Custom Amount** - Pay any amount between ₹1,000 and total due
3. **EMI** - Monthly installments based on loan tenure

Each option shows real-time calculations and handles payment method selection.

## 📊 Tech Stack

- **Backend**: FastAPI 0.121.2
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Authentication**: Session-based with bcrypt

## 🧪 Testing

### Test User Credentials
- Username: `testuser`
- Password: `password123`

### Test Data
- Test Member created with account number
- Test Loan: ₹50,000 @ 8.5% for 12 months (Personal, Active)

## 📝 Notes

- Database automatically created on first run
- All features work without email/SMS configuration
- Development mode enabled by default
- Static files served from `/static`

## 🚨 Common Issues

### Server won't start
```powershell
# Check if port 8001 is in use
# Activate virtual environment first
.\.venv\Scripts\Activate.ps1
```

### Database errors
```powershell
# Database is stored in backend/instance/
# Delete it to reset: Remove-Item backend/instance -Recurse
```

### Import errors
```powershell
# Reinstall requirements
pip install -r backend/requirements.txt
```

## 📞 Support

For setup help, see **[SETUP.md](SETUP.md)**

---

**Made for Cooperative Banking** 🏦💰
