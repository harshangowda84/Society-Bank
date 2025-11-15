# Society Bank - Setup Guide

## Prerequisites
- Python 3.8 or higher
- Git
- A text editor or IDE (VS Code recommended)

## Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/harshangowda84/Society-Bank.git
cd Society-Bank
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Run the Application
```bash
cd backend
uvicorn main:app --reload
```

### 5. Access the Application
Open your browser and go to:
- **Home Page**: http://localhost:8000
- **Admin Login**: http://localhost:8000/admin-login
- **Member Login**: http://localhost:8000/login

## Default Admin Credentials
- **Username**: admin
- **Password**: Admin@123

## Project Structure
```
Society-Bank/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── db.py                # Database configuration
│   ├── config.py            # Configuration settings
│   ├── requirements.txt     # Python dependencies
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, images
│   └── instance/            # SQLite database
└── README.md
```

## Features
- Member Registration & Login
- Loan Applications
- Fixed Deposit Applications
- Share Investments
- Admin Dashboard
- Member Dashboard
- Fund Transfers
- Reports & Analytics

## Database
- SQLite database is automatically created on first run
- Location: `backend/instance/society_bank.db`

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Database Issues
Delete the database and restart:
```bash
rm backend/instance/society_bank.db
# Then run the application again
```

## Environment Variables (Optional)
Create a `.env` file in the `backend` directory:
```env
FAST2SMS_API_KEY=your_api_key
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123
```

## Contributing
1. Create a new branch: `git checkout -b feature-name`
2. Make your changes
3. Commit: `git commit -m "Description of changes"`
4. Push: `git push origin feature-name`
5. Create a Pull Request

## Contact
For issues or questions, contact the repository owner.
