import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash

from app import create_app
from db import engine
from models.users import User

# ==========================================
#  Test Fixture: Setup
# ==========================================
@pytest.fixture
def client():
    """
    Setup a virtual test client for the Flask application.
    Runs before each test function.
    """
    app = create_app()
    app.config['TESTING'] = True  # Enable testing mode
    app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for easier POST testing
    
    with app.test_client() as client:
        yield client

# ==========================================
#  Test Case 1: Guest Mode
# ==========================================
def test_account_redirect_if_not_logged_in(client):
    """Test: Accessing /account without login should redirect to login page."""
    
    # 1. Action: Simulate a GET request to /account
    response = client.get('/account')

    # 2. Verify: Status code should be 302 (Redirect)
    assert response.status_code == 302

# ==========================================
#  Test Case 2: Member Mode
# ==========================================
def test_account_page_loads_if_logged_in(client):
    """Test: Accessing /account with a valid session should load the page."""

    # 1. Action: Manually set user_id in session to simulate login
    with client.session_transaction() as sess:
        sess['user_id'] = 1  # Assume user ID 1 exists

    # 2. Action: Send GET request
    response = client.get('/account')

    # 3. Verify: Status code should be 200 (OK)
    assert response.status_code == 200
    
    # 4. Verify: Check if "Account Details" text exists in response
    assert b"Account Details" in response.data

# ==========================================
#  Test Case 3: Update Email (Success)
# ==========================================
def test_update_email_success(client):
    """Test: Updating email with valid unique data should succeed."""
    
    # 1. Simulate login
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    # 2. Action: Send POST request with action='update_profile'
    response = client.post('/account', data={
        'action': 'update_profile',
        'email': 'new_test_email@test.com'
    }, follow_redirects=True)

    # 3. Verify: Check for success flash message
    assert response.status_code == 200
    assert b"Profile updated successfully" in response.data

# ==========================================
#  Test Case 4: Update Email (Fail - Empty)
# ==========================================
def test_update_email_empty(client):
    """Test: Submitting an empty email should show an error."""
    
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/account', data={
        'action': 'update_profile',
        'email': ''  # Empty value
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Email cannot be empty" in response.data

# ==========================================
#  Test Case 5: Update Email (Fail - Duplicate)
# ==========================================
def test_update_email_already_registered(client):
    """Test: Updating to an email that belongs to another user should fail."""
    
    target_email = "duplicate_user@test.com"

    # 1. Setup: Create a temporary dummy user (User 2) with the target email
    # We use a DB session to insert this user directly
    with Session(engine) as db_session:
        # Check if user already exists to avoid errors
        stmt = select(User).where(User.email == target_email)
        existing = db_session.execute(stmt).scalar_one_or_none()
        
        if not existing:
            user2 = User(
                id=999, # Use a safe ID that likely doesn't exist
                account="temp_user_999",
                firstname="Temp",
                lastname="User",
                email=target_email,
                password=generate_password_hash("1234")
            )
            db_session.add(user2)
            db_session.commit()

    try:
        # 2. Login as User 1
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        # 3. Action: User 1 tries to change email to User 2's email
        response = client.post('/account', data={
            'action': 'update_profile',
            'email': target_email
        }, follow_redirects=True)

        # 4. Verify: Error message should appear
        assert response.status_code == 200
        assert b"This email is already registered by another user" in response.data

    finally:
        # 5. Teardown: Delete the temporary user to clean up database
        with Session(engine) as db_session:
            stmt = select(User).where(User.email == target_email)
            user_to_del = db_session.execute(stmt).scalar_one_or_none()
            if user_to_del:
                db_session.delete(user_to_del)
                db_session.commit()

# ==========================================
#  Test Case 6: Change Password (Fail - Mismatch)
# ==========================================
def test_change_password_mismatch(client):
    """Test: New password and confirm password do not match."""
    
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/account', data={
        'action': 'change_password',
        'current_password': '1234',
        'new_password': 'new123',
        'confirm_password': 'wrong123' # Mismatch
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"New passwords do not match" in response.data

# ==========================================
#  Test Case 7: Change Password (Fail - Wrong Old Password)
# ==========================================
def test_change_password_wrong_current(client):
    """Test: Incorrect old password should prevent change."""
    
    with client.session_transaction() as sess:
        sess['user_id'] = 1

    response = client.post('/account', data={
        'action': 'change_password',
        'current_password': 'WRONG_PASSWORD', # Incorrect password
        'new_password': 'new123',
        'confirm_password': 'new123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Incorrect current password" in response.data

# ==========================================
#  Test Case 8: Change Password (Success)
# ==========================================
def test_change_password_success(client):
    """Test: Changing password with correct old and new passwords should succeed and clean up."""

    # 1. Setup: Reset Password to known state ('12345')
    # This ensures every test run starts with the correct initial password.
    with Session(engine) as db_session:
        user = db_session.get(User, 1)
        # Check if password needs reset
        if not check_password_hash(user.password, '12345'):
            user.password = generate_password_hash('12345')
            db_session.commit()
            
    try:
        # 2a. Simulate login
        with client.session_transaction() as sess:
            sess['user_id'] = 1

        # 2b. Action: Send POST request using the current password ('12345')
        response = client.post('/account', data={
            'action': 'change_password',
            'current_password': '12345',      
            'new_password': 'new5678',       
            'confirm_password': 'new5678'    
        }, follow_redirects=True)

        # 3. Verify UI: Check for success message
        assert response.status_code == 200
        assert b"Password updated successfully" in response.data

        # 4. Verify Database Persistence:
        # Fetch User 1 again to verify the password was updated successfully.
        with Session(engine) as db_session:
            user = db_session.get(User, 1)
            # Verification A: Check if the new password works against the stored hash
            assert check_password_hash(user.password, 'new5678')
            # Verification B: Check if the old password is now invalid (proving overwrite)
            assert not check_password_hash(user.password, '12345')

    finally:
        # 5. Teardown: Reset the password back to '12345'
        with Session(engine) as db_session:
            user = db_session.get(User, 1)
            user.password = generate_password_hash('12345')
            db_session.merge(user)
            db_session.commit()