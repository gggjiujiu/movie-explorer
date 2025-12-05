import pytest
from app import create_app
from werkzeug.security import generate_password_hash, check_password_hash


# --- Mock User Object ---
# Simulates the User class from users.py,
# implementing only the attributes and methods needed by account.py.
class MockUser:
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.account = "test_account_123"
        self.firstname = "Test"
        self.lastname = "User"
        # Stores the hashed password to simulate the database
        self.password = generate_password_hash(password)
        # Attribute used by account.py
        self.fullname = f"{self.firstname} {self.lastname}"

    def check_password(self, password_input):
        # Simulates password verification logic
        return check_password_hash(self.password, password_input)


# Default user for testing
TEST_USER_ID = 1
TEST_USER_PASSWORD = '12345'
TEST_USER = MockUser(TEST_USER_ID, "test@example.com", TEST_USER_PASSWORD)


# --- Fixtures ---
@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"  # for session
    # Disable CSRF for easier POST testing, in case it is enabled in app.py
    app.config["WTF_CSRF_ENABLED"] = False
    return app


@pytest.fixture
def client(app):
    return app.test_client()


# Client fixture with logged-in status and Mocking
@pytest.fixture
def logged_in_client(client, monkeypatch):
    """Sets the client status to logged in and Mocks db.get_user function."""

    # 1. Mock get_user: Ensures account.py always receives TEST_USER
    def mock_get_user(user_id):
        return TEST_USER if user_id == TEST_USER_ID else None

    # Path to the get_user function used in account.py: routes.account.get_user
    monkeypatch.setattr("routes.account.get_user", mock_get_user)

    # 2. Set session to simulate login
    with client.session_transaction() as sess:
        sess['user_id'] = TEST_USER_ID

    return client


# ==========================================
#  Test Case 1: Guest Mode
# ==========================================
def test_account_redirect_if_not_logged_in(client):
    """Test: Guest access to /account should redirect to the login page."""

    response = client.get('/account')

    # Expect redirect (302) to the login page (auth.home)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/')


# ==========================================
#  Test Case 2: Member Mode
# ==========================================
def test_account_page_loads_if_logged_in(logged_in_client):
    """Test: Accessing /account while logged in should load the page
    successfully and display user info."""

    response = logged_in_client.get('/account')

    assert response.status_code == 200
    assert b"Account Details" in response.data
    # Verify the user's name is correctly passed and rendered
    assert TEST_USER.fullname.encode() in response.data


# ==========================================
#  Test Case 3: Update Email (Success)
# ==========================================
def test_update_email_success(logged_in_client, monkeypatch):
    """Test: Successful email update (email is unique)."""

    # 1. Mock email_exists function:
    # Returns False (meaning the email is available)
    monkeypatch.setattr(
        "routes.account.email_exists",
        lambda new_email, user_id: False
    )

    # 2. Mock update_user_email function: Track that it is called
    update_called = {"status": False, "new_email": None}

    def mock_update_user_email(user, new_email):
        update_called["status"] = True
        update_called["new_email"] = new_email
        monkeypatch.setattr(
            "routes.account.update_user_email",
            mock_update_user_email
        )

    # 3. Send request
    NEW_EMAIL = 'new_test_email@test.com'
    response = logged_in_client.post('/account', data={
        'action': 'update_profile',
        'email': NEW_EMAIL
    }, follow_redirects=True)

    # 4. Verify
    assert update_called["status"]
    assert update_called["new_email"] == NEW_EMAIL
    assert b"Profile updated successfully!" in response.data


# ==========================================
#  Test Case 4: Update Email (Fail - Empty)
# ==========================================
def test_update_email_empty(logged_in_client):
    """Test: Submitting an empty email should show an error."""

    response = logged_in_client.post('/account', data={
        'action': 'update_profile',
        'email': ''  # Empty value
    }, follow_redirects=True)

    assert b"Email cannot be empty." in response.data


# ==========================================
#  Test Case 5: Update Email (Fail - Duplicate)
# ==========================================
def test_update_email_already_registered(logged_in_client, monkeypatch):
    """Test: Updating email already registered by another user should fail."""

    # Mock email_exists function:
    # Returns True (meaning the email is already taken)
    monkeypatch.setattr(
        "routes.account.email_exists",
        lambda new_email, user_id: True
    )

    response = logged_in_client.post('/account', data={
        'action': 'update_profile',
        'email': 'duplicate_user@test.com'
    }, follow_redirects=True)

    assert (
        b"This email is already registered by another user."
        in response.data
    )


# ==========================================
#  Test Case 6: Change Password (Fail - Mismatch)
# ==========================================
def test_change_password_mismatch(logged_in_client):
    """Test: New password and confirm password do not match."""

    response = logged_in_client.post('/account', data={
        'action': 'change_password',
        'current_password': TEST_USER_PASSWORD,
        'new_password': 'new123',
        'confirm_password': 'wrong123'  # Mismatch
    }, follow_redirects=True)

    assert b"New passwords do not match!" in response.data


# ==========================================
#  Test Case 7: Change Password (Fail - Wrong Current Password)
# ==========================================
def test_change_password_wrong_current(logged_in_client):
    """Test: Incorrect current password."""

    response = logged_in_client.post('/account', data={
        'action': 'change_password',
        'current_password': 'WRONG_PASSWORD',  # Incorrect password
        'new_password': 'new123',
        'confirm_password': 'new123'
    }, follow_redirects=True)

    assert b"Incorrect current password." in response.data


# ==========================================
#  Test Case 8: Change Password (Success)
# ==========================================
def test_change_password_success(logged_in_client, monkeypatch):
    """Test: Successful password change."""

    # 1. Mock update_user_password function: Track that it is called
    update_called = {"status": False, "hashed_pw": None}

    def mock_update_user_password(user, hashed_password):
        update_called["status"] = True
        update_called["hashed_pw"] = hashed_password
        monkeypatch.setattr(
            "routes.account.update_user_password",
            mock_update_user_password
        )

    NEW_PASSWORD = 'new5678'

    # 2. Send request
    response = logged_in_client.post('/account', data={
        'action': 'change_password',
        'current_password': TEST_USER_PASSWORD,
        'new_password': NEW_PASSWORD,
        'confirm_password': NEW_PASSWORD
    }, follow_redirects=True)

    # 3. Verify
    assert b"Password updated successfully!" in response.data
    assert update_called["status"]
    # Check if the passed hash is correct
    assert check_password_hash(update_called["hashed_pw"], NEW_PASSWORD)
