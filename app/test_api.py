# app/test_api.py
import pytest
from app.schemas import UserCreate
from app.crud import get_user_by_email, create_user
from app.database import get_db

# --- TEST DATA ---
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
TEST_TRAINER = {
    "name": "Test Trainer",
    "email": "trainer@test.com",
    "password": "trainerpassword",
    "role": "trainer"
}
TEST_CLASS_DATA = {
    "name": "Morning Yoga",
    "max_capacity": 10,
    "duration_minutes": 75
}

# Store tokens and global IDs for re-use in subsequent tests
member_token = None
admin_token = None
trainer_token = None
class_id = None


# --- HELPER FUNCTIONS ---

def get_member_token(client):
    """Registers and logs in a member, returns the token."""
    global member_token
    if member_token:
        return member_token
    
    client.post("/register", json=TEST_MEMBER)
    
    # Login
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

    # 1. Ensure user is created and promoted using the passed db_session
    admin_data = UserCreate(**TEST_ADMIN)
    db_admin = get_user_by_email(db_session, admin_data.email)
    if not db_admin:
        db_admin = create_user(db_session, user=admin_data)
        db_admin.role = "admin" 
        db_session.commit()
    
    # 2. Login
    response = client.post(
        "/token", 
        data={"username": TEST_ADMIN["email"], "password": TEST_ADMIN["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    admin_token = response.json()["access_token"]
    return admin_token

def get_trainer_token(client, db_session):
    """Registers and promotes a trainer, returns the token."""
    global trainer_token
    if trainer_token:
        return trainer_token

    # 1. Ensure user is created and promoted using the passed db_session
    trainer_data = UserCreate(**TEST_TRAINER)
    db_trainer = get_user_by_email(db_session, trainer_data.email)
    if not db_trainer:
        db_trainer = create_user(db_session, user=trainer_data)
        db_trainer.role = "trainer" 
        db_session.commit()
    
    # 2. Login
    response = client.post(
        "/token", 
        data={"username": TEST_TRAINER["email"], "password": TEST_TRAINER["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert response.status_code == 200
    trainer_token = response.json()["access_token"]
    return trainer_token

# --- CRITICAL FIX FOR ATTRIBUTEERROR ---
def get_user_id_by_email(db_session, email):
    """Helper to fetch the ID of a user from the DB."""
    # We must use the session passed to the test (db_session) to find users
    # created by the token helpers in the same test session scope.
    from app.crud import get_user_by_email
    
    # Attempt to retrieve the user using the test session
    user = get_user_by_email(db_session, email)
    
    if user is None:
        # If the user is None, it means the necessary get_*_token helper 
        # that registers the user was NOT called before this function.
        raise ValueError(f"CRITICAL: User with email {email} not found in the test session. Ensure the corresponding get_*_token helper was called correctly before retrieving the ID.")
        
    return user.id


# --- CORE AUTH & USER TESTS ---

def test_register_and_check_default_role(client):
    """Tests registration and confirms default role is 'member'."""
    response = client.post("/register", json=TEST_MEMBER)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == TEST_MEMBER["email"]
    assert data["role"] == "member"
    
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

def test_unauthorized_access(client):
    """Tests accessing a protected route without a token."""
    response = client.get("/users/me")
    assert response.status_code == 401


# --- ROLE-BASED ACCESS CONTROL (RBAC) TESTS ---

def test_rbac_admin_update_role_success(client, db_session):
    """Tests Admin-only route by updating a user's role."""
    admin_token = get_admin_token(client, db_session)
    # The member user is created by get_member_token called in the previous tests
    member_id = get_user_id_by_email(db_session, TEST_MEMBER['email'])

    # Admin attempts to change member role to 'trainer'
    response = client.patch(
        f"/admin/update-role/{member_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "trainer"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "trainer"
    
    # Revert role back to 'member' for subsequent tests
    client.patch(
        f"/admin/update-role/{member_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"role": "member"}
    )

def test_rbac_trainer_update_role_fail(client, db_session):
    """Tests if a trainer is blocked from the Admin-only route."""
    trainer_token = get_trainer_token(client, db_session)
    member_id = get_user_id_by_email(db_session, TEST_MEMBER['email'])
    
    # Trainer attempts to change the role
    response = client.patch(
        f"/admin/update-role/{member_id}",
        headers={"Authorization": f"Bearer {trainer_token}"},
        json={"role": "admin"}
    )
    assert response.status_code == 403 # Forbidden

def test_rbac_member_access_trainer_data_fail(client, db_session):
    """Tests if a 'member' is blocked from the Trainer/Admin route."""
    member_token = get_member_token(client)
    response = client.get(
        "/trainer-data",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert response.status_code == 403 # Forbidden

def test_rbac_admin_access_trainer_data_success(client, db_session):
    """Tests if an 'admin' can access the Trainer/Admin route."""
    admin_token = get_admin_token(client, db_session)
    response = client.get(
        "/trainer-data",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200

# --- CLASS MANAGEMENT TESTS ---

def test_class_creation_trainer_success(client, db_session):
    """Tests Trainer's ability to create a new class and stores the ID."""
    global class_id
    trainer_token = get_trainer_token(client, db_session)
    trainer_id = get_user_id_by_email(db_session, TEST_TRAINER['email'])
    
    class_data = TEST_CLASS_DATA.copy()
    class_data["trainer_id"] = trainer_id # Inject the actual trainer ID

    response = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {trainer_token}"},
        json=class_data
    )
    assert response.status_code == 201
    class_id = response.json()["id"] # Store ID for booking tests
    assert response.json()["trainer_id"] == trainer_id

def test_class_creation_member_fail(client, db_session):
    """Tests Member's failure to create a class (RBAC check)."""
    member_token = get_member_token(client)
    trainer_id = get_user_id_by_email(db_session, TEST_TRAINER['email'])
    
    class_data = TEST_CLASS_DATA.copy()
    class_data["trainer_id"] = trainer_id

    response = client.post(
        "/classes",
        headers={"Authorization": f"Bearer {member_token}"},
        json=class_data
    )
    assert response.status_code == 403 # Forbidden

def test_list_classes_success(client, db_session):
    """Tests that any user can view the list of classes."""
    # Note: We pass db_session to ensure get_member_token runs first to guarantee user exists
    token = get_member_token(client) 
    response = client.get(
        "/classes",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert class_id is not None 
    assert any(c["id"] == class_id for c in data)

# --- BOOKING MANAGEMENT TESTS ---

def test_book_class_member_success(client, db_session):
    """Tests a Member successfully booking a class."""
    member_token = get_member_token(client)
    member_id = get_user_id_by_email(db_session, TEST_MEMBER['email'])

    booking_data = {
        "class_id": class_id, 
        "member_id": member_id # Member books for themselves
    }
    
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {member_token}"},
        json=booking_data
    )
    assert response.status_code == 201
    assert response.json()["class_id"] == class_id

def test_book_class_member_for_others_fail(client, db_session):
    """Tests a Member trying to book a class for a different user ID (Security Check)."""
    member_token = get_member_token(client)
    # The user being booked for must exist to get an ID
    get_admin_token(client, db_session) 
    other_user_id = get_user_id_by_email(db_session, TEST_ADMIN['email'])

    booking_data = {
        "class_id": class_id, 
        "member_id": other_user_id # Booking for another ID
    }
    
    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {member_token}"},
        json=booking_data
    )
    assert response.status_code == 403 # Forbidden

def test_book_class_capacity_fail(client, db_session):
    """Tests booking failure when class capacity is reached (using a class of capacity 1)."""
    trainer_token = get_trainer_token(client, db_session)
    trainer_id = get_user_id_by_email(db_session, TEST_TRAINER['email'])
    member_id = get_user_id_by_email(db_session, TEST_MEMBER['email'])

    # 1. Create a low capacity class (Capacity: 1)
    low_cap_data = TEST_CLASS_DATA.copy()
    low_cap_data["trainer_id"] = trainer_id
    low_cap_data["max_capacity"] = 1
    
    response = client.post("/classes", headers={"Authorization": f"Bearer {trainer_token}"}, json=low_cap_data)
    low_cap_class_id = response.json()["id"]

    # 2. First booking (Success, takes the last spot)
    booking_data = {"class_id": low_cap_class_id, "member_id": member_id}
    client.post("/bookings", headers={"Authorization": f"Bearer {get_member_token(client)}"}, json=booking_data)
    
    # 3. Second booking (Failure - Capacity Full)
    response_fail = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {get_member_token(client)}"},
        json=booking_data
    )
    assert response_fail.status_code == 409 # Conflict (Class is fully booked)

def test_get_my_bookings_success(client, db_session):
    """Tests retrieving the current user's bookings."""
    member_token = get_member_token(client)
    
    response = client.get(
        "/users/me/bookings",
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check that at least the class_id from test_book_class_member_success is present
    assert any(b["class_id"] == class_id for b in data)