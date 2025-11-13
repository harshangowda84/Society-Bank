# Backend (FastAPI) - run instructions

This backend is a FastAPI application that serves templates and uses SQLAlchemy with a local SQLite database.

Quick start (Windows PowerShell):

1. Activate the project's venv (if not already active):

```powershell
& 'C:/Users/Harshan/Desktop/Society-Bank/.venv/Scripts/Activate.ps1'
```

2. (Optional) copy `.env.example` to `.env` and edit values, or set environment variables in your system.

3. Install dependencies (from the backend folder):

```powershell
cd 'C:/Users/Harshan/Desktop/Society-Bank/backend'
& 'C:/Users/Harshan/Desktop/Society-Bank/.venv/Scripts/python.exe' -m pip install -r requirements.txt
```

4. Run the app with uvicorn:

```powershell
& 'C:/Users/Harshan/Desktop/Society-Bank/.venv/Scripts/python.exe' -m uvicorn main:app --reload --port 8000
```

5. Open http://127.0.0.1:8000 in your browser.

Notes:
- Database file is created at `backend/instance/society_bank.db`.
- Provide `FAST2SMS_API_KEY` or email credentials only if you want SMS/email functionality. Otherwise the app will skip those actions.
- For production, use a proper WSGI/ASGI host, secure credentials via a secrets manager, and a production DB.
