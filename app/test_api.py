# app/test_api.py
import pytest
from app.schemas import UserCreate
from app.crud import get_user_by_email, create_user
from app.database import get_db

# --- Test Data ---
TEST_MEMBER = {
    "name": "Test Member",
    "email": "member@test.com",
    "password": "testpassword"
}
TEST_ADMIN = {
    "name": "Test Admin",
    "email": "admin@test.com",
    "password": "adminpassword",
    "role": "admin"
}
# Store a token for re-use in subsequent tests
member_token = None
admin_token = None

# --- Helper Functions (Use the client fixture to interact with the API) ---

def get_member_token(client):
    """Registers and logs in a member, returns the token."""
    global member_token
    if member_token:
        return member_token
    
    client.post("/register", json=TEST_MEMBER)
    
    response = client.post(
        "/token", 
        data={"username": TEST_MEMBER["email"], "password": TEST_MEMBER["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    member_token = response.json()["access_token"]
    return member_token

def get_admin_token(client, db_session):
    """Registers and promotes an admin, returns the token."""
    global admin_token
    if admin_token:
        return admin_token

    # 1. Ensure user is created
    admin_data = UserCreate(**TEST_ADMIN)
    db_admin = get_user_by_email(db_session, admin_data.email)
    if not db_admin:
        db_admin = create_user(db_session, user=admin_data)
        # 2. Promote to admin directly in DB to bypass registration default
        db_admin.role = "admin" 
        db_session.commit()
    
    # 3. Login
    response = client.post(
        "/token", 
        data={"username": TEST_ADMIN["email"], "password": TEST_ADMIN["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    admin_token = response.json()["access_token"]
    return admin_token

# --- Core Tests ---

def test_register_and_check_default_role(client):
    """Tests registration and confirms default role is 'member'."""
    response = client.post("/register", json=TEST_MEMBER)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == TEST_MEMBER["email"]
    assert data["role"] == "member"
    
    # Attempt to register again (should fail)
    response_conflict = client.post("/register", json=TEST_MEMBER)
    assert response_conflict.status_code == 400

def test_login_and_get_profile(client):
    """Tests successful login and protected profile access."""
    token = get_member_token(client)
    
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == TEST_MEMBER["email"]
    assert data["role"] == "member"

def test_unauthorized_access(client):
    """Tests accessing a protected route without a token."""
    response = client.get("/users/me")
    assert response.status_code == 401

# --- Role-Based Access Control (RBAC) Tests ---

def test_rbac_member_access_to_services_success(client):
    """Tests if a 'member' can access the /services route."""
    token = get_member_token(client)
    
    response = client.get(
        "/services",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "Cardio Area Access" in data

def test_rbac_admin_update_role_success(client, db_session):
    """Tests Admin-only route by updating a user's role."""
    admin_token = get_admin_token(client, db_session)
    
    # 1. Get the member's ID
    db = next(get_db()) # Get a fresh session for querying
    member = get_user_by_email(db, TEST_MEMBER['email'])
    db.close()

    # 2. Admin attempts to change member role to 'trainer'
    response = client.patch(
        f"/admin/update-role/{member.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "trainer"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "trainer"

def test_rbac_member_update_role_fail(client, db_session):
    """Tests if a member is blocked from the Admin-only route."""
    member_token = get_member_token(client)
    
    # 1. Get the member's ID
    db = next(get_db())
    member = get_user_by_email(db, TEST_MEMBER['email'])
    db.close()
    
    # 2. Member attempts to change the role
    response = client.patch(
        f"/admin/update-role/{member.id}",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"role": "admin"}
    )
    assert response.status_code == 403 # Forbidden