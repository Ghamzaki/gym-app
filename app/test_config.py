# app/test_config.py

# --- Database Configuration ---
# Use an isolated SQLite file for local testing to ensure fast, clean tests.
TEST_DATABASE_URL = "sqlite:///./test.db" 


# --- Test User Data ---
# These dictionaries mirror the app/schemas.py UserCreate model but include the role for setup
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

# --- Test Entity Data ---
TEST_CLASS_DATA = {
    "name": "Morning Yoga",
    "max_capacity": 10,
    "duration_minutes": 75
}