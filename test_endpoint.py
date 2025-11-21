import requests

# Test home page
try:
    r = requests.get('http://127.0.0.1:8000/')
    print(f"Home page status: {r.status_code}")
except Exception as e:
    print(f"Home page error: {e}")

# Test member dashboard (should redirect to login)
try:
    r = requests.get('http://127.0.0.1:8000/member-dashboard')
    print(f"Member dashboard status: {r.status_code}")
    if r.status_code == 500:
        print("Response text:", r.text[:500])
except Exception as e:
    print(f"Member dashboard error: {e}")
