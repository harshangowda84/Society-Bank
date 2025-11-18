import os
from fastapi import FastAPI, Request, Form, Depends, status, Cookie, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
from db import SessionLocal, engine, Base
import models
import requests
import smtplib
from email.mime.text import MIMEText
import csv
import io
import random
from datetime import datetime, timedelta

app = FastAPI()

# Create the database tables after models have been imported
Base.metadata.create_all(bind=engine)

# Seed initial interest rates if they don't exist
def seed_interest_rates():
    db = SessionLocal()
    try:
        # Check and create default loan interest rates
        loan_types = [
            ('Personal', 12.5, 10000, 500000),
            ('Education', 9.5, 50000, 2500000),
            ('Home', 8.5, 500000, 50000000),
            ('Vehicle', 10.5, 100000, 2000000),
            ('Business', 11.5, 200000, 10000000),
            ('Emergency', 14.5, 10000, 300000),
        ]
        
        for loan_type, rate, min_amt, max_amt in loan_types:
            existing = db.query(models.LoanInterestRate).filter_by(loan_type=loan_type).first()
            if not existing:
                db.add(models.LoanInterestRate(
                    loan_type=loan_type,
                    interest_rate=rate,
                    min_amount=min_amt,
                    max_amount=max_amt
                ))
        
        # Check and create default FD interest rates based on tenure (months and years)
        # Fixed Deposits - Monthly
        fixed_monthly_rates = [
            ('Fixed', 3, None, 3.0),
            ('Fixed', 6, None, 3.5),
        ]
        
        # Fixed Deposits - Yearly
        fixed_yearly_rates = [
            ('Fixed', None, 1, 4.5),
            ('Fixed', None, 2, 5.0),
            ('Fixed', None, 3, 5.5),
            ('Fixed', None, 5, 6.5),
            ('Fixed', None, 7, 7.0),
            ('Fixed', None, 10, 7.5),
        ]
        
        # Recurring Deposits - Monthly
        recurring_monthly_rates = [
            ('Recurring', 6, None, 2.5),
            ('Recurring', 12, None, 3.0),
        ]
        
        # Recurring Deposits - Yearly
        recurring_yearly_rates = [
            ('Recurring', None, 1, 3.5),
            ('Recurring', None, 2, 4.0),
            ('Recurring', None, 3, 4.5),
            ('Recurring', None, 5, 5.5),
        ]
        
        # Senior Citizen Fixed Deposits - Monthly
        senior_monthly_rates = [
            ('Senior Citizen', 3, None, 4.0),
            ('Senior Citizen', 6, None, 4.5),
        ]
        
        # Senior Citizen Fixed Deposits - Yearly
        senior_yearly_rates = [
            ('Senior Citizen', None, 1, 5.5),
            ('Senior Citizen', None, 2, 6.0),
            ('Senior Citizen', None, 3, 6.5),
            ('Senior Citizen', None, 5, 7.5),
            ('Senior Citizen', None, 7, 8.0),
            ('Senior Citizen', None, 10, 8.5),
        ]
        
        # Combine all FD rates
        all_fd_rates = (fixed_monthly_rates + fixed_yearly_rates + 
                       recurring_monthly_rates + recurring_yearly_rates + 
                       senior_monthly_rates + senior_yearly_rates)
        
        for fd_type, tenure_months, tenure_years, rate in all_fd_rates:
            existing = db.query(models.FDInterestRate).filter_by(
                fd_type=fd_type, 
                tenure_months=tenure_months, 
                tenure_years=tenure_years
            ).first()
            if not existing:
                db.add(models.FDInterestRate(
                    fd_type=fd_type,
                    tenure_months=tenure_months,
                    tenure_years=tenure_years,
                    interest_rate=rate
                ))
        
        db.commit()
    except Exception as e:
        print(f"Error seeding interest rates: {e}")
        db.rollback()
    finally:
        db.close()

seed_interest_rates()

base_dir = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# Add custom Jinja2 filters
def strftime_filter(dt, format_string):
    if dt:
        return dt.strftime(format_string)
    return ''

templates.env.filters['strftime'] = strftime_filter

# Read sensitive config from environment variables. Use a .env or system env to set these.
FAST2SMS_API_KEY = os.getenv('FAST2SMS_API_KEY')  # e.g. from fast2sms
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin@123')
SECURE_COOKIES = os.getenv('SECURE_COOKIES', 'false').lower() == 'true'

# Simple in-memory OTP store for dev/testing. For production, use a persistent store.
OTP_STORE = {}
OTP_TTL = int(os.getenv('OTP_TTL_SECONDS', 300))  # 5 minutes default


def send_sms_fast2sms(phone: str, message: str) -> None:
    if not FAST2SMS_API_KEY:
        print('FAST2SMS_API_KEY not set; skipping SMS send')
        return
    url = 'https://www.fast2sms.com/dev/bulkV2'
    headers = {'authorization': FAST2SMS_API_KEY}
    payload = {
        'sender_id': 'FSTSMS',
        'message': message,
        'language': 'english',
        'route': 'v3',
        'numbers': phone
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        print('SMS response:', response.json())
    except Exception as e:
        print('Error sending SMS:', e)


def send_email(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = to_email
    try:
        if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
            print('Email host credentials not set; skipping email send')
            return
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, [to_email], msg.as_string())
        server.quit()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Home page
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    announcements = db.query(models.Announcement).order_by(models.Announcement.created_at.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "announcements": announcements})


# Member login
@app.get("/login", response_class=HTMLResponse, name="login")
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    member = db.query(models.Member).filter_by(username=username).first()
    if not member or not member.check_password(password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials."})
    if not member.is_approved:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Your account is pending approval."})
    response = RedirectResponse(url="/member-dashboard", status_code=status.HTTP_303_SEE_OTHER)
    # Harden member cookies: HttpOnly for sensitive id, SameSite to Lax, optional secure flag via env
    response.set_cookie(key="member_id", value=str(member.id), httponly=True, samesite="Lax", secure=SECURE_COOKIES)
    # Non-sensitive display cookie for convenience (not HttpOnly)
    response.set_cookie(key="name", value=member.name, samesite="Lax", secure=SECURE_COOKIES)
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("member_id")
    response.delete_cookie("name")
    return response


# Admin login / protected admin routes
@app.get("/admin-login", response_class=HTMLResponse, name="admin_login")
def admin_login_form(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


@app.post("/admin-login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    # Use environment-provided admin credentials (configured at top of file)
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="is_admin", value="true", httponly=True, samesite="Lax", secure=SECURE_COOKIES)
        return response
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Invalid admin credentials."})


@app.get("/admin", response_class=HTMLResponse, name="admin")
def admin_dashboard(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    members = db.query(models.Member).all()
    unapproved_members = db.query(models.Member).filter_by(is_approved=False).all()
    recent_members = db.query(models.Member).order_by(models.Member.id.desc()).limit(10).all()
    members_count = db.query(models.Member).count()
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "members_count": members_count,
            "recent_members": recent_members,
            "unapproved_members": unapproved_members,
        },
    )


@app.get("/admin/new-members", response_class=HTMLResponse, name="admin_new_members")
def admin_new_members(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    unapproved_members = db.query(models.Member).filter_by(is_approved=False).all()
    return templates.TemplateResponse(
        "admin_new_members.html",
        {
            "request": request,
            "unapproved_members": unapproved_members,
        },
    )


@app.get("/admin/all-members", response_class=HTMLResponse, name="admin_all_members")
def admin_all_members(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    members = db.query(models.Member).all()
    approved_count = db.query(models.Member).filter_by(is_approved=True).count()
    pending_count = db.query(models.Member).filter_by(is_approved=False).count()
    total_members = db.query(models.Member).count()
    return templates.TemplateResponse(
        "admin_all_members.html",
        {
            "request": request,
            "members": members,
            "total_members": total_members,
            "approved_count": approved_count,
            "pending_count": pending_count,
        },
    )


@app.post("/admin")
def admin_action(request: Request, member_id: int = Form(...), action: str = Form(...), is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    member = db.query(models.Member).get(member_id)
    if member:
        if action == 'approve':
            member.is_approved = True
            db.commit()
        elif action == 'reject':
            db.delete(member)
            db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/admin-logout")
def admin_logout():
    response = RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("is_admin")
    return response


# OTP and password reset skeleton (developer-friendly, replace with production-safe mechanisms)
@app.post('/send-otp')
def send_otp(username: str = Form(...), db: Session = Depends(get_db)):
    member = db.query(models.Member).filter_by(username=username).first()
    if not member:
        return JSONResponse({'ok': False, 'error': 'User not found'}, status_code=404)
    code = str(random.randint(100000, 999999))
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_TTL)
    OTP_STORE[username] = {'code': code, 'expires_at': expires_at}
    # Try SMS first, fallback to email if available
    message = f"Your OTP for Society Bank is: {code}. It expires in {OTP_TTL//60} minutes."
    try:
        if getattr(member, 'mobile', None):
            send_sms_fast2sms(member.mobile, message)
        elif getattr(member, 'email', None):
            send_email(member.email, 'Your OTP', message)
    except Exception:
        pass
    return JSONResponse({'ok': True, 'message': 'OTP sent if contact available'})


@app.post('/verify-otp')
def verify_otp(username: str = Form(...), code: str = Form(...)):
    entry = OTP_STORE.get(username)
    if not entry:
        return JSONResponse({'ok': False, 'error': 'No OTP found'}, status_code=400)
    if datetime.utcnow() > entry['expires_at']:
        del OTP_STORE[username]
        return JSONResponse({'ok': False, 'error': 'OTP expired'}, status_code=400)
    if entry['code'] != code:
        return JSONResponse({'ok': False, 'error': 'Invalid OTP'}, status_code=400)
    # OTP validated — for password reset flow, a token or server-side flag should be set.
    # Here we return success and the client can proceed to call `/reset-password`.
    del OTP_STORE[username]
    return JSONResponse({'ok': True})


@app.post('/reset-password')
def reset_password(username: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    member = db.query(models.Member).filter_by(username=username).first()
    if not member:
        return JSONResponse({'ok': False, 'error': 'User not found'}, status_code=404)
    # In production, ensure this call is gated by a verified OTP or reset token
    member.set_password(new_password)
    db.add(member)
    db.commit()
    return JSONResponse({'ok': True, 'message': 'Password reset successful'})


# Announcements management (admin)
@app.get("/admin/announcements", response_class=HTMLResponse, name="manage_announcements")
def manage_announcements(request: Request, db: Session = Depends(get_db)):
    announcements = db.query(models.Announcement).order_by(models.Announcement.created_at.desc()).all()
    return templates.TemplateResponse("admin_announcements.html", {"request": request, "announcements": announcements})


@app.post("/admin/announcements")
def add_announcement(request: Request, message: str = Form(...), is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    announcement = models.Announcement(message=message)
    db.add(announcement)
    db.commit()
    return RedirectResponse(url="/admin/announcements", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/admin/announcements/delete/{announcement_id}")
def delete_announcement(announcement_id: int, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    announcement = db.query(models.Announcement).filter_by(id=announcement_id).first()
    if announcement:
        db.delete(announcement)
        db.commit()
    return RedirectResponse(url="/admin/announcements", status_code=status.HTTP_303_SEE_OTHER)


# Register (member application) - handle form post from register.html
@app.get("/register", response_class=HTMLResponse, name="register")
def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register_member(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    name = form.get("applicant_name")
    username = form.get("username")
    password = form.get("password")
    dob = form.get("date_of_birth")
    designation = form.get("designation_address")
    mobile = form.get("mobile_number")
    aadhaar = form.get("aadhaar_number")
    pan = form.get("pan_number")

    # Check if username already exists
    existing_user = db.query(models.Member).filter(models.Member.username == username).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Username already exists. Please choose a different username."
        })

    # Generate system date for application (not user input)
    from datetime import date as date_module
    today = date_module.today()
    today_str = today.strftime("%Y-%m-%d")
    today_timestamp = today.strftime("%Y%m%d")
    
    # Generate unique account number: ACC-YYYYMMDD-XXXX (system-generated, not user input)
    account_no = f"ACC-{today_timestamp}-{random.randint(1000, 9999)}"

    member = models.Member(
        name=name,
        username=username,
        dob=dob,
        designation=designation,
        mobile=mobile,
        bank_account=account_no,  # Use system-generated account number
        aadhaar=aadhaar,
        pan=pan,
        application_date=today_str,  # System-generated application date
        is_approved=False,
        account_no=account_no,
    )
    if password:
        member.set_password(password)

    db.add(member)
    db.commit()
    db.refresh(member)
    
    # Send account number via SMS
    sms_msg = f"Welcome to Society Bank! Your Account Number: {account_no}. Username: {username}"
    try:
        if mobile:
            send_sms_fast2sms(mobile, sms_msg)
    except Exception as e:
        print(f"SMS send failed: {e}")
    
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


# Admin: add member (manual)
@app.get("/admin/add-member", response_class=HTMLResponse, name="admin_add_member")
def admin_add_member_form(request: Request, is_admin: str = Cookie(default=None)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("admin_add_member.html", {"request": request})


@app.post("/admin/add-member")
def admin_add_member(request: Request, name: str = Form(...), account_no: str = Form(...), phone: str = Form(...), dob: str = Form(...), is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    username = account_no
    password = f"Society{random.randint(1000,9999)}"
    existing_member = db.query(models.Member).filter((models.Member.account_no == account_no) | (models.Member.username == username)).first()
    if existing_member:
        return templates.TemplateResponse("admin_add_member.html", {"request": request, "error": "Account number or username already exists."})
    new_member = models.Member(
        name=name,
        account_no=account_no,
        phone=phone,
        dob=dob,
        is_approved=True,
        username=username,
    )
    new_member.set_password(password)
    db.add(new_member)
    db.commit()
    return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)


# Member dashboard
@app.get("/member-dashboard", response_class=HTMLResponse, name="member_dashboard")
def member_dashboard(request: Request, db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    member = db.query(models.Member).get(member_id)
    if not member:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    account = db.query(models.Account).filter_by(member_id=member_id).first() if member else None
    transactions = db.query(models.Transaction).filter_by(account_id=account.id).all() if account else []
    loans = db.query(models.Loan).filter_by(member_id=member_id).all() if member else []
    deposits = db.query(models.Deposit).filter_by(member_id=member_id).all() if member else []
    shares = db.query(models.Share).filter_by(member_id=member_id).all() if member else []
    return templates.TemplateResponse("member_dashboard.html", {
        "request": request,
        "member": member,
        "transactions": transactions,
        "loans": loans,
        "deposits": deposits,
        "shares": shares
    })


# List members
@app.get("/members", response_class=HTMLResponse, name="list_members")
def list_members(request: Request, db: Session = Depends(get_db)):
    members = db.query(models.Member).all()
    member_details = []
    for member in members:
        loans = db.query(models.Loan).filter_by(member_id=member.id).all()
        account = db.query(models.Account).filter_by(member_id=member.id).first()
        transactions = db.query(models.Transaction).filter_by(account_id=account.id).all() if account else []
        fixed_deposits = db.query(models.Deposit).filter_by(member_id=member.id).all()
        member_details.append({
            'member': member,
            'loans': loans,
            'transactions': transactions,
            'fixed_deposits': fixed_deposits
        })
    return templates.TemplateResponse("list_members.html", {"request": request, "member_details": member_details})


# Other list endpoints
@app.get("/accounts", response_class=HTMLResponse, name="list_accounts")
def list_accounts(request: Request, db: Session = Depends(get_db)):
    accounts = db.query(models.Account).all()
    return templates.TemplateResponse("accounts.html", {"request": request, "accounts": accounts})


@app.get("/api/member/loans")
def get_member_loans(request: Request, db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return JSONResponse({'error': 'Not authenticated'}, status_code=401)
    
    loans = db.query(models.Loan).filter_by(member_id=member_id).all()
    loans_data = [
        {
            'id': loan.id,
            'loan_type': loan.loan_type,
            'amount': loan.amount,
            'interest_rate': loan.interest_rate,
            'tenure_months': loan.tenure_months,
            'status': loan.status,
            'created_at': loan.created_at.isoformat() if loan.created_at else None
        }
        for loan in loans
    ]
    return JSONResponse(loans_data)


@app.get("/loans", response_class=HTMLResponse, name="list_loans")
def list_loans(request: Request, db: Session = Depends(get_db)):
    loans = db.query(models.Loan).all()
    return templates.TemplateResponse("loans.html", {"request": request, "loans": loans})


@app.get("/deposits", response_class=HTMLResponse, name="list_deposits")
def list_deposits(request: Request, db: Session = Depends(get_db)):
    deposits = db.query(models.Deposit).all()
    return templates.TemplateResponse("deposits.html", {"request": request, "deposits": deposits})


@app.get("/transactions", response_class=HTMLResponse, name="list_transactions")
def list_transactions(request: Request, db: Session = Depends(get_db)):
    transactions = db.query(models.Transaction).all()
    return templates.TemplateResponse("transactions.html", {"request": request, "transactions": transactions})


# Loan application form
@app.get("/loan-application", response_class=HTMLResponse)
def loan_application_form(request: Request):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("loan_application_form.html", {"request": request})


@app.get("/fd-application", response_class=HTMLResponse)
def fd_application_form(request: Request):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("fd_application_form.html", {"request": request})


@app.get("/share-investment", response_class=HTMLResponse)
def share_investment_form(request: Request):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("share_investment_form.html", {"request": request})


@app.get("/loan-repayment", response_class=HTMLResponse)
def loan_repayment_form(request: Request):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse("loan_repayment.html", {"request": request})


@app.get("/admin/approvals", response_class=HTMLResponse)
def admin_approvals_page(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    pending_loans = db.query(models.Loan).filter_by(status='Pending').all()
    pending_fds = db.query(models.Deposit).filter_by(status='Pending').all()
    pending_shares = db.query(models.Share).filter_by(status='Pending').all()
    return templates.TemplateResponse("admin_approvals.html", {
        "request": request,
        "pending_loans": pending_loans,
        "pending_fds": pending_fds,
        "pending_shares": pending_shares
    })


@app.get("/vision", response_class=HTMLResponse, name="vision")
def vision(request: Request):
    return templates.TemplateResponse("vision.html", {"request": request})


@app.get("/services", response_class=HTMLResponse, name="services")
def services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})


@app.get("/benefits", response_class=HTMLResponse, name="benefits")
def benefits(request: Request):
    return templates.TemplateResponse("benefits.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/contact", response_class=HTMLResponse)
def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})


@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})


@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request):
    # List files from static/gallery (if present)
    gallery_dir = os.path.join(os.path.dirname(__file__), "static", "gallery")
    images = []
    try:
        for fname in sorted(os.listdir(gallery_dir)):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                images.append(f"/static/gallery/{fname}")
    except FileNotFoundError:
        images = []
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})


# Member loan application
@app.post("/member/apply-loan")
def apply_loan(request: Request, loan_type: str = Form(...), amount: float = Form(...), tenure_months: int = Form(...), purpose: str = Form(default=''), db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return JSONResponse({'ok': False, 'error': 'Not authenticated'}, status_code=401)
    
    member = db.query(models.Member).get(member_id)
    if not member:
        return JSONResponse({'ok': False, 'error': 'Member not found'}, status_code=404)
    
    # Get interest rate from LoanInterestRate table
    rate_config = db.query(models.LoanInterestRate).filter_by(loan_type=loan_type).first()
    if not rate_config:
        return JSONResponse({'ok': False, 'error': 'Invalid loan type'}, status_code=400)
    
    # Create loan with automatic interest rate
    loan = models.Loan(
        member_id=member_id,
        loan_type=loan_type,
        amount=amount,
        interest_rate=rate_config.interest_rate,
        tenure_months=tenure_months,
        status='Pending',
        office_note=purpose
    )
    db.add(loan)
    db.commit()
    db.refresh(loan)
    return JSONResponse({'ok': True, 'loan_id': loan.id, 'message': 'Loan application submitted'})


# Member FD application
@app.post("/member/apply-fd")
def apply_fd(request: Request, amount: float = Form(...), fd_type: str = Form(...), maturity_date: str = Form(...), db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return JSONResponse({'ok': False, 'error': 'Not authenticated'}, status_code=401)
    member = db.query(models.Member).get(member_id)
    if not member:
        return JSONResponse({'ok': False, 'error': 'Member not found'}, status_code=404)
    deposit = models.Deposit(member_id=member_id, amount=amount, type=fd_type, maturity_date=maturity_date, status='Pending')
    db.add(deposit)
    db.commit()
    db.refresh(deposit)
    return JSONResponse({'ok': True, 'deposit_id': deposit.id, 'message': 'FD application submitted'})


# Member share investment
@app.post("/member/invest-shares")
def invest_shares(request: Request, quantity: int = Form(...), amount_per_share: float = Form(...), db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return JSONResponse({'ok': False, 'error': 'Not authenticated'}, status_code=401)
    member = db.query(models.Member).get(member_id)
    if not member:
        return JSONResponse({'ok': False, 'error': 'Member not found'}, status_code=404)
    total = quantity * amount_per_share
    share = models.Share(member_id=member_id, quantity=quantity, amount_per_share=amount_per_share, total_amount=total, status='Pending')
    db.add(share)
    db.commit()
    db.refresh(share)
    return JSONResponse({'ok': True, 'share_id': share.id, 'message': 'Share investment submitted'})


# Admin loan approval
@app.post("/admin/approve-loan")
def approve_loan(request: Request, loan_id: int = Form(...), office_note: str = Form(...), is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Not authorized'}, status_code=403)
    loan = db.query(models.Loan).get(loan_id)
    if not loan:
        return JSONResponse({'ok': False, 'error': 'Loan not found'}, status_code=404)
    loan.office_approved = True
    loan.office_note = office_note
    loan.approved_at = datetime.utcnow()
    loan.status = 'Approved'
    db.commit()
    return JSONResponse({'ok': True, 'message': 'Loan approved'})


# Admin FD approval
@app.post("/admin/approve-fd")
def approve_fd(request: Request, deposit_id: int = Form(...), office_note: str = Form(...), is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Not authorized'}, status_code=403)
    deposit = db.query(models.Deposit).get(deposit_id)
    if not deposit:
        return JSONResponse({'ok': False, 'error': 'FD not found'}, status_code=404)
    deposit.office_approved = True
    deposit.office_note = office_note
    deposit.approved_at = datetime.utcnow()
    deposit.status = 'Approved'
    db.commit()
    return JSONResponse({'ok': True, 'message': 'FD approved'})


# Admin share approval
@app.post("/admin/approve-share")
def approve_share(request: Request, share_id: int = Form(...), office_note: str = Form(...), is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Not authorized'}, status_code=403)
    share = db.query(models.Share).get(share_id)
    if not share:
        return JSONResponse({'ok': False, 'error': 'Share not found'}, status_code=404)
    share.office_approved = True
    share.office_note = office_note
    share.approved_at = datetime.utcnow()
    share.status = 'Approved'
    db.commit()
    return JSONResponse({'ok': True, 'message': 'Share investment approved'})


# Admin loan repayment & pre-closure
@app.post("/member/repay-loan")
def repay_loan(request: Request, loan_id: int = Form(...), principal: float = Form(...), interest: float = Form(...), payment_method: str = Form(...), db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return JSONResponse({'ok': False, 'error': 'Not authenticated'}, status_code=401)
    loan = db.query(models.Loan).get(loan_id)
    if not loan or loan.member_id != int(member_id):
        return JSONResponse({'ok': False, 'error': 'Loan not found or unauthorized'}, status_code=404)
    repayment = models.LoanRepayment(loan_id=loan_id, principal_paid=principal, interest_paid=interest, payment_method=payment_method)
    db.add(repayment)
    if principal + interest >= (loan.amount + (loan.amount * loan.interest_rate / 100)):
        loan.repayment_status = 'Completed'
    else:
        loan.repayment_status = 'Active'
    db.commit()
    return JSONResponse({'ok': True, 'message': 'Repayment recorded'})


# Member to Member Transfer
@app.post("/member/transfer")
def transfer_funds(request: Request, recipient_account_no: str = Form(...), amount: float = Form(...), 
                   description: str = Form(default="Transfer"), db: Session = Depends(get_db)):
    member_id = request.cookies.get("member_id")
    if not member_id:
        return JSONResponse({'ok': False, 'error': 'Not authenticated'}, status_code=401)
    
    member = db.query(models.Member).get(member_id)
    if not member:
        return JSONResponse({'ok': False, 'error': 'Sender not found'}, status_code=404)
    
    recipient = db.query(models.Member).filter_by(account_no=recipient_account_no).first()
    if not recipient:
        return JSONResponse({'ok': False, 'error': 'Recipient not found'}, status_code=404)
    
    if amount <= 0:
        return JSONResponse({'ok': False, 'error': 'Amount must be positive'}, status_code=400)
    
    sender_account = db.query(models.Account).filter_by(member_id=member_id).first()
    recipient_account = db.query(models.Account).filter_by(member_id=recipient.id).first()
    
    if not sender_account or not recipient_account:
        return JSONResponse({'ok': False, 'error': 'Account not found'}, status_code=404)
    
    if sender_account.balance < amount:
        return JSONResponse({'ok': False, 'error': 'Insufficient balance'}, status_code=400)
    
    # Atomic transaction
    try:
        sender_account.balance -= amount
        recipient_account.balance += amount
        
        # Create transaction records
        debit_txn = models.Transaction(account_id=sender_account.id, type='Debit', amount=amount, 
                                      description=f"Transfer to {recipient.account_no}")
        credit_txn = models.Transaction(account_id=recipient_account.id, type='Credit', amount=amount,
                                       description=f"Transfer from {member.account_no}")
        
        db.add(debit_txn)
        db.add(credit_txn)
        db.commit()
        
        return JSONResponse({'ok': True, 'message': f'₹{amount} transferred to {recipient.account_no}'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


# Bank reports: P&L and transaction history
@app.get("/admin/bank-reports", response_class=HTMLResponse)
def bank_reports(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    total_loans = db.query(models.Loan).filter_by(status='Approved').count()
    total_fds = db.query(models.Deposit).filter_by(status='Approved').count()
    total_shares = db.query(models.Share).filter_by(status='Approved').count()
    total_members = db.query(models.Member).filter_by(is_approved=True).count()
    total_loan_amount = sum([l.amount for l in db.query(models.Loan).filter_by(status='Approved').all()]) or 0
    total_fd_amount = sum([d.amount for d in db.query(models.Deposit).filter_by(status='Approved').all()]) or 0
    total_share_amount = sum([s.total_amount for s in db.query(models.Share).filter_by(status='Approved').all()]) or 0
    all_transactions = db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).limit(100).all()
    
    return templates.TemplateResponse("bank_reports.html", {
        "request": request,
        "total_members": total_members,
        "total_loans": total_loans,
        "total_fds": total_fds,
        "total_shares": total_shares,
        "total_loan_amount": total_loan_amount,
        "total_fd_amount": total_fd_amount,
        "total_share_amount": total_share_amount,
        "transactions": all_transactions
    })


# Admin image upload for gallery
@app.post("/admin/upload-gallery-image")
async def upload_gallery_image(file: UploadFile = None, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Not authorized'}, status_code=403)
    if not file:
        return JSONResponse({'ok': False, 'error': 'No file provided'}, status_code=400)
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        return JSONResponse({'ok': False, 'error': 'Invalid file type'}, status_code=400)
    gallery_dir = os.path.join(os.path.dirname(__file__), "static", "gallery")
    os.makedirs(gallery_dir, exist_ok=True)
    file_path = os.path.join(gallery_dir, file.filename)
    try:
        with open(file_path, 'wb') as f:
            content = await file.read()
            f.write(content)
        return JSONResponse({'ok': True, 'message': f'Image {file.filename} uploaded'})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


# CSV Export endpoints

@app.get("/export/members")
def export_members_csv(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'error': 'Not authorized'}, status_code=403)
    
    members = db.query(models.Member).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Username', 'Account No', 'Phone', 'DOB', 'Is Approved'])
    
    for member in members:
        writer.writerow([
            member.id,
            member.name,
            member.username,
            member.account_no or '',
            member.mobile or '',
            member.dob or '',
            'Yes' if member.is_approved else 'No'
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"}
    )


@app.get("/export/loans")
def export_loans_csv(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'error': 'Not authorized'}, status_code=403)
    
    loans = db.query(models.Loan).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Member ID', 'Amount', 'Interest Rate (%)', 'Tenure (Months)', 'Status', 'Repayment Status', 'Created At'])
    
    for loan in loans:
        writer.writerow([
            loan.id,
            loan.member_id,
            f"{loan.amount:.2f}",
            loan.interest_rate,
            loan.tenure_months,
            loan.status,
            loan.repayment_status,
            loan.created_at.strftime('%Y-%m-%d') if loan.created_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=loans.csv"}
    )


@app.get("/export/deposits")
def export_deposits_csv(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'error': 'Not authorized'}, status_code=403)
    
    deposits = db.query(models.Deposit).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Member ID', 'Amount', 'Type', 'Maturity Date', 'Status', 'Created At'])
    
    for deposit in deposits:
        writer.writerow([
            deposit.id,
            deposit.member_id,
            f"{deposit.amount:.2f}",
            deposit.type,
            deposit.maturity_date if deposit.maturity_date else '',
            deposit.status,
            deposit.created_at.strftime('%Y-%m-%d') if deposit.created_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=deposits.csv"}
    )


@app.get("/export/transactions")
def export_transactions_csv(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'error': 'Not authorized'}, status_code=403)
    
    transactions = db.query(models.Transaction).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Account ID', 'Type', 'Amount', 'Description', 'Created At'])
    
    for txn in transactions:
        writer.writerow([
            txn.id,
            txn.account_id,
            txn.type,
            f"{txn.amount:.2f}",
            txn.description or '',
            txn.created_at.strftime('%Y-%m-%d %H:%M:%S') if txn.created_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )


@app.get("/export/bank-report")
def export_bank_report_csv(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'error': 'Not authorized'}, status_code=403)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Summary section
    writer.writerow(['SOCIETY BANK - REPORT'])
    writer.writerow(['Generated on', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    
    # Statistics
    writer.writerow(['STATISTICS'])
    total_members = db.query(models.Member).filter_by(is_approved=True).count()
    total_loans = db.query(models.Loan).filter_by(status='Approved').count()
    total_fds = db.query(models.Deposit).filter_by(status='Approved').count()
    total_shares = db.query(models.Share).filter_by(status='Approved').count()
    total_loan_amount = sum([l.amount for l in db.query(models.Loan).filter_by(status='Approved').all()]) or 0
    total_fd_amount = sum([d.amount for d in db.query(models.Deposit).filter_by(status='Approved').all()]) or 0
    total_share_amount = sum([s.total_amount for s in db.query(models.Share).filter_by(status='Approved').all()]) or 0
    
    writer.writerow(['Total Members', total_members])
    writer.writerow(['Total Approved Loans', total_loans])
    writer.writerow(['Total Loan Amount', f"{total_loan_amount:.2f}"])
    writer.writerow(['Total FDs', total_fds])
    writer.writerow(['Total FD Amount', f"{total_fd_amount:.2f}"])
    writer.writerow(['Total Shares', total_shares])
    writer.writerow(['Total Share Amount', f"{total_share_amount:.2f}"])
    writer.writerow([])
    
    # P&L
    writer.writerow(['PROFIT & LOSS'])
    writer.writerow(['Total Deposits (FD)', f"{total_fd_amount:.2f}"])
    writer.writerow(['Total Loans Disbursed', f"{total_loan_amount:.2f}"])
    net_position = total_fd_amount - total_loan_amount
    writer.writerow(['Net Position', f"{net_position:.2f}"])
    writer.writerow([])
    
    # Transactions
    writer.writerow(['RECENT TRANSACTIONS (Last 100)'])
    writer.writerow(['ID', 'Type', 'Amount', 'Created At'])
    all_transactions = db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).limit(100).all()
    for txn in all_transactions:
        writer.writerow([
            txn.id,
            txn.type,
            f"{txn.amount:.2f}",
            txn.created_at.strftime('%Y-%m-%d %H:%M') if txn.created_at else ''
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=bank_report.csv"}
    )


# Admin Loan Management Routes
@app.get("/admin/loan-management", response_class=HTMLResponse)
def loan_management(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    
    loan_rates = db.query(models.LoanInterestRate).all()
    loans = db.query(models.Loan).options(joinedload(models.Loan.member)).order_by(models.Loan.created_at.desc()).all()
    
    return templates.TemplateResponse("admin_loan_management.html", {
        "request": request,
        "loan_rates": loan_rates,
        "loans": loans
    })


@app.post("/admin/update-loan-rate")
async def update_loan_rate(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        data = await request.json()
        rate_id = data.get('id')
        interest_rate = data.get('interest_rate')
        min_amount = data.get('min_amount')
        max_amount = data.get('max_amount')
        
        rate = db.query(models.LoanInterestRate).filter_by(id=rate_id).first()
        if not rate:
            return JSONResponse({'ok': False, 'error': 'Loan rate not found'})
        
        rate.interest_rate = interest_rate
        rate.min_amount = min_amount
        rate.max_amount = max_amount
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'Interest rate updated successfully'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)




# Admin Loan Management - Separate JSON API Routes
@app.post("/admin/loan/approve")
async def admin_approve_loan(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        data = await request.json()
        loan_id = data.get('loan_id')
        
        loan = db.query(models.Loan).filter_by(id=loan_id).first()
        if not loan:
            return JSONResponse({'ok': False, 'error': 'Loan not found'})
        
        loan.status = 'Approved'
        loan.office_approved = True
        loan.approved_at = datetime.utcnow()
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'Loan approved successfully'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.post("/admin/loan/reject")
async def admin_reject_loan(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        data = await request.json()
        loan_id = data.get('loan_id')
        reason = data.get('reason', '')
        
        loan = db.query(models.Loan).filter_by(id=loan_id).first()
        if not loan:
            return JSONResponse({'ok': False, 'error': 'Loan not found'})
        
        loan.status = 'Rejected'
        loan.office_note = reason
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'Loan rejected successfully'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.get("/admin/loan/{loan_id}/details")
def admin_loan_details(loan_id: int, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    loan = db.query(models.Loan).filter_by(id=loan_id).first()
    if not loan:
        return JSONResponse({'ok': False, 'error': 'Loan not found'})
    
    return JSONResponse({
        'ok': True,
        'loan': {
            'id': loan.id,
            'member_name': loan.member.name,
            'amount': loan.amount,
            'interest_rate': loan.interest_rate,
            'tenure_months': loan.tenure_months,
            'status': loan.status,
            'created_at': loan.created_at.strftime('%Y-%m-%d %H:%M') if loan.created_at else ''
        }
    })


# ===== FD Management Routes =====

@app.get("/admin/fd-management", response_class=HTMLResponse)
def fd_management(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return RedirectResponse(url="/admin-login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("admin_fd_management.html", {"request": request})


@app.get("/admin/fd-applications")
def get_fd_applications(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        deposits = db.query(models.Deposit).options(joinedload(models.Deposit.member)).order_by(models.Deposit.created_at.desc()).all()
        
        applications = []
        for deposit in deposits:
            applications.append({
                'id': deposit.id,
                'member_id': deposit.member_id,
                'member_name': deposit.member.name if deposit.member else 'N/A',
                'fd_type': deposit.type,
                'amount': deposit.amount,
                'period': deposit.period,
                'interest_rate': deposit.interest_rate,
                'status': deposit.status if deposit.status in ['Pending', 'Approved', 'Rejected'] else 'Pending',
                'created_at': deposit.created_at.strftime('%Y-%m-%d %H:%M') if deposit.created_at else ''
            })
        
        return JSONResponse({'ok': True, 'applications': applications})
    except Exception as e:
        print(f"Error fetching FD applications: {e}")
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.get("/admin/fd/{fd_id}/details")
def get_fd_details(fd_id: int, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        deposit = db.query(models.Deposit).filter_by(id=fd_id).first()
        if not deposit:
            return JSONResponse({'ok': False, 'error': 'FD not found'})
        
        return JSONResponse({
            'ok': True,
            'fd': {
                'id': deposit.id,
                'member_id': deposit.member_id,
                'member_name': deposit.member.name if deposit.member else 'N/A',
                'fd_type': deposit.type,
                'amount': deposit.amount,
                'period': deposit.period,
                'interest_rate': deposit.interest_rate,
                'interest_payment': deposit.interest_payment,
                'maturity_amount': deposit.maturity_amount or (deposit.amount * (1 + deposit.interest_rate * deposit.period / 100)),
                'nominee_name': deposit.nominee_name or 'N/A',
                'nominee_relationship': deposit.nominee_relationship or 'N/A',
                'status': deposit.status,
                'created_at': deposit.created_at.strftime('%Y-%m-%d %H:%M') if deposit.created_at else ''
            }
        })
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.post("/admin/fd/{fd_id}/approve")
async def approve_fd(fd_id: int, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        deposit = db.query(models.Deposit).filter_by(id=fd_id).first()
        if not deposit:
            return JSONResponse({'ok': False, 'error': 'FD not found'})
        
        deposit.status = 'Approved'
        deposit.office_approved = True
        deposit.approved_at = datetime.utcnow()
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'FD approved successfully'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.post("/admin/fd/{fd_id}/reject")
async def reject_fd(fd_id: int, request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        data = await request.json()
        reason = data.get('reason', '')
        
        deposit = db.query(models.Deposit).filter_by(id=fd_id).first()
        if not deposit:
            return JSONResponse({'ok': False, 'error': 'FD not found'})
        
        deposit.status = 'Rejected'
        deposit.office_note = reason
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'FD rejected successfully'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.get("/api/fd-rates")
def get_fd_rates_public(db: Session = Depends(get_db)):
    """Public endpoint for members to fetch FD rates"""
    try:
        rates = db.query(models.FDInterestRate).all()
        
        rate_list = []
        for rate in rates:
            rate_list.append({
                'fd_type': rate.fd_type,
                'interest_rate': rate.interest_rate
            })
        
        return JSONResponse({'ok': True, 'rates': rate_list})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.get("/admin/fd-rates")
def get_fd_rates(is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        # Order by fd_type, then tenure_months (nulls last), then tenure_years
        rates = db.query(models.FDInterestRate).order_by(
            models.FDInterestRate.fd_type,
            models.FDInterestRate.tenure_months.is_(None),
            models.FDInterestRate.tenure_months,
            models.FDInterestRate.tenure_years
        ).all()
        
        # Group rates by FD type
        rate_dict = {}
        for rate in rates:
            if rate.fd_type not in rate_dict:
                rate_dict[rate.fd_type] = []
            rate_dict[rate.fd_type].append({
                'id': rate.id,
                'fd_type': rate.fd_type,
                'tenure_months': rate.tenure_months,
                'tenure_years': rate.tenure_years,
                'interest_rate': rate.interest_rate,
                'updated_at': rate.updated_at.isoformat() if rate.updated_at else None
            })
        
        return JSONResponse({'ok': True, 'rates': rate_dict})
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.get("/admin/fd-rate/{fd_type}")
def get_fd_rate_detail(fd_type: str, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        rates = db.query(models.FDInterestRate).filter_by(fd_type=fd_type).order_by(
            models.FDInterestRate.tenure_months.is_(None),
            models.FDInterestRate.tenure_months,
            models.FDInterestRate.tenure_years
        ).all()
        if not rates:
            return JSONResponse({'ok': False, 'error': 'FD rate not found'})
        
        return JSONResponse({
            'ok': True,
            'rates': [{
                'id': rate.id,
                'fd_type': rate.fd_type,
                'tenure_months': rate.tenure_months,
                'tenure_years': rate.tenure_years,
                'interest_rate': rate.interest_rate,
                'updated_at': rate.updated_at.isoformat() if rate.updated_at else None
            } for rate in rates]
        })
    except Exception as e:
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.post("/admin/update-fd-rate")
async def update_fd_rate(request: Request, is_admin: str = Cookie(default=None), db: Session = Depends(get_db)):
    if is_admin != "true":
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        data = await request.json()
        rate_id = data.get('id')
        
        rate = db.query(models.FDInterestRate).filter_by(id=rate_id).first()
        if not rate:
            return JSONResponse({'ok': False, 'error': 'FD rate not found'})
        
        rate.interest_rate = float(data.get('interest_rate', rate.interest_rate))
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'FD interest rate updated successfully'})
    except Exception as e:
        db.rollback()
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


@app.post("/member/apply-fd")
async def apply_fd(
    request: Request,
    member_id: int = Cookie(default=None),
    db: Session = Depends(get_db)
):
    if not member_id:
        return JSONResponse({'ok': False, 'error': 'Unauthorized'}, status_code=403)
    
    try:
        form_data = await request.form()
        
        fd_type = form_data.get('fd_type')
        amount = float(form_data.get('amount', 0))
        period = int(form_data.get('period', 1))
        interest_rate = float(form_data.get('interest_rate', 6.5))
        interest_payment = form_data.get('interest_payment', 'annual')
        nominee_name = form_data.get('nominee_name', '')
        nominee_relationship = form_data.get('nominee_relationship', '')
        special_instructions = form_data.get('special_instructions', '')
        
        if amount < 10000:
            return JSONResponse({'ok': False, 'error': 'Minimum deposit amount is ₹10,000'})
        
        # Calculate maturity amount
        maturity_amount = amount * (1 + (interest_rate * period / 100))
        
        # Create deposit record
        deposit = models.Deposit(
            member_id=member_id,
            amount=amount,
            type=fd_type,
            period=period,
            interest_rate=interest_rate,
            interest_payment=interest_payment,
            maturity_amount=maturity_amount,
            nominee_name=nominee_name if nominee_name else None,
            nominee_relationship=nominee_relationship if nominee_relationship else None,
            special_instructions=special_instructions if special_instructions else None,
            status='Pending'
        )
        
        db.add(deposit)
        db.commit()
        
        return JSONResponse({'ok': True, 'message': 'FD application submitted successfully'})
    except Exception as e:
        db.rollback()
        print(f"Error applying for FD: {e}")
        return JSONResponse({'ok': False, 'error': str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)