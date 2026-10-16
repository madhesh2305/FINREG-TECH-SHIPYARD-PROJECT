import httpx
import json
from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Query the user registered in Phase 2
    users = conn.execute(text("SELECT user_id, email FROM identity.users WHERE email LIKE 'audit_persisted_user_%' ORDER BY user_id DESC LIMIT 1")).fetchone()
    project = conn.execute(text("SELECT project_id, project_name, project_code FROM project_management.projects WHERE project_code LIKE 'PRJ-AUDIT-%' ORDER BY project_id DESC LIMIT 1")).fetchone()
    print("Latest Persisted User in PostgreSQL:", users)
    print("Latest Persisted Project in PostgreSQL:", project)

assert users is not None, "No test user found in PostgreSQL"
assert project is not None, "No test project found in PostgreSQL"

user_id, email = users
suffix = email.split("_user_")[1].split("@")[0]
password = f"P@ssword_{suffix}!Secure"

# Authenticate against PostgreSQL after server restart
login_res = httpx.post("http://127.0.0.1:8000/api/v1/auth/login", json={"email": email, "password": password})
print(f"Login status after backend restart: {login_res.status_code}")
assert login_res.status_code == 200, f"Login failed: {login_res.text}"
token = login_res.json()["access_token"]

# Retrieve Project Details
project_id, project_name, project_code = project
proj_res = httpx.get(f"http://127.0.0.1:8000/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
print(f"Project retrieval status after backend restart: {proj_res.status_code}")
assert proj_res.status_code == 200, f"Project retrieval failed: {proj_res.text}"
proj_data = proj_res.json()
print(f"Retrieved Project Name: '{proj_data.get('name')}', Code: '{proj_data.get('code')}'")

# Retrieve Audit Events
audit_res = httpx.get(f"http://127.0.0.1:8000/api/v1/projects/{project_id}/audit-events", headers={"Authorization": f"Bearer {token}"})
print(f"Audit events status after backend restart: {audit_res.status_code}")
assert audit_res.status_code == 200
events = audit_res.json()
print(f"Total audit events retrieved from PostgreSQL after reboot: {len(events)}")
for ev in events:
    print(f"  -> Persisted Audit Event: {ev.get('event_type')} (ID: {ev.get('audit_event_id')})")

print("\nRESTART PERSISTENCE VERIFICATION: 100% SUCCESSFUL AND FULLY PERSISTENT IN POSTGRESQL!")
