import requests

# Create a session to maintain cookies
session = requests.Session()

# Try to access member dashboard
r = session.get('http://127.0.0.1:8000/member-dashboard')
print(f"Member dashboard status: {r.status_code}")

# Check if we have cookies
print(f"Cookies: {session.cookies.get_dict()}")

# If we're logged in, try to make a deposit
if r.status_code == 200:
    print("\nTrying to make a deposit...")
    deposit_data = {
        'amount': 1000,
        'payment_method': 'Cash',
        'description': 'Test deposit'
    }
    
    r_deposit = session.post('http://127.0.0.1:8000/member/deposit', data=deposit_data)
    print(f"Deposit status: {r_deposit.status_code}")
    print(f"Deposit response: {r_deposit.text}")
