import pytest
from werkzeug.security import generate_password_hash, check_password_hash

from routes import account


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

        # Stores the hashed password to simulate the DB-stored password
        self.password = generate_password_hash(password)

        # fullname is used by account.py when rendering user details
        self.fullname = f"{self.firstname} {self.lastname}"

    def check_password(self, password_input):
        # Simulates password verification logic
        return check_password_hash(self.password, password_input)


# Default user for testing
TEST_USER_ID = 1
TEST_USER_PASSWORD = "12345"
TEST_USER = MockUser(TEST_USER_ID, "test@example.com", TEST_USER_PASSWORD)


# ----------------------
# Fixture: logged_in_client
# ----------------------
@pytest.fixture
def logged_in_client(client, monkeypatch):
    """
    Simulates a logged-in user and patches account.get_user so that
    account.py always receives a mock user object instead of querying the DB.
    """

    # Ensures account.py always receives TEST_USER
    def mock_get_user(user_id):
        return TEST_USER if user_id == TEST_USER_ID else None

    # Must patch the function on the 'account' module itself
    monkeypatch.setattr(account, "get_user", mock_get_user)

    # Set the session to simulate login
    with client.session_transaction() as sess:
        sess["user_id"] = TEST_USER_ID

    return client


# ==========================================
#  Test Case 1: Guest Mode
# ==========================================
def test_account_redirect_if_not_logged_in(client):
    """Test: Guest access to /account should redirect to the login page."""

    response = client.get("/account")

    # Expect redirect (302) to the login page (auth.home)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


# ==========================================
#  Test Case 2: Member Mode
# ==========================================
def test_account_page_loads_if_logged_in(logged_in_client):
    """
    Test: Accessing /account while logged in should load the page
    successfully and display user info.
    """

    response = logged_in_client.get("/account")

    assert response.status_code == 200
    assert b"Account Details" in response.data

    # Verify the user's name is correctly passed and rendered
    assert TEST_USER.fullname.encode() in response.data


# ==========================================
#  Test Case 3: Update Email (Success)
# ==========================================
def test_update_email_success(logged_in_client, monkeypatch):
    """Test: Successful email update when new email is unique."""

    # 1. Mock email_exists to indicate the email is available
    monkeypatch.setattr(account,
                        "email_exists",
                        lambda new_email,
                        user_id: False)

    # Track whether update_user_email is called
    update_called = {"status": False, "new_email": None}

    def mock_update_user_email(user, new_email):
        update_called["status"] = True
        update_called["new_email"] = new_email

    # Correct monkeypatch target
    monkeypatch.setattr(account, "update_user_email", mock_update_user_email)

    # 2. Send POST request
    NEW_EMAIL = "new_test_email@test.com"
    response = logged_in_client.post(
        "/account",
        data={"action": "update_profile", "email": NEW_EMAIL},
        follow_redirects=True,
    )

    # 3. Verify
    assert update_called["status"]
    assert update_called["new_email"] == NEW_EMAIL
    assert b"Profile updated successfully!" in response.data


# ==========================================
#  Test Case 4: Update Email (Fail - Empty)
# ==========================================
def test_update_email_empty(logged_in_client):
    """Test: Submitting an empty email should show an error."""

    response = logged_in_client.post(
        "/account",
        data={"action": "update_profile", "email": ""},
        follow_redirects=True,
    )

    assert b"Email cannot be empty." in response.data


# ==========================================
#  Test Case 5: Update Email (Fail - Duplicate)
# ==========================================
def test_update_email_already_registered(logged_in_client, monkeypatch):
    """Test: Updating email that is already taken should fail."""

    # email_exists returns True → email already used by another user
    monkeypatch.setattr(account, "email_exists", lambda e, uid: True)

    response = logged_in_client.post(
        "/account",
        data={"action": "update_profile", "email": "duplicate_user@test.com"},
        follow_redirects=True,
    )

    assert (b"This email is already registered by another user."
            in response.data)


# ==========================================
#  Test Case 6: Change Password (Fail - Mismatch)
# ==========================================
def test_change_password_mismatch(logged_in_client):
    """Test: New password and confirm password do not match."""

    response = logged_in_client.post(
        "/account",
        data={
            "action": "change_password",
            "current_password": TEST_USER_PASSWORD,
            "new_password": "new123",
            "confirm_password": "wrong123",  # Mismatch
        },
        follow_redirects=True,
    )

    assert b"New passwords do not match!" in response.data


# ==========================================
#  Test Case 7: Change Password (Fail - Wrong Current Password)
# ==========================================
def test_change_password_wrong_current(logged_in_client):
    """Test: Incorrect current password should be rejected."""

    response = logged_in_client.post(
        "/account",
        data={
            "action": "change_password",
            "current_password": "WRONG_PASSWORD",  # Incorrect password
            "new_password": "new123",
            "confirm_password": "new123",
        },
        follow_redirects=True,
    )

    assert b"Incorrect current password." in response.data


# ==========================================
#  Test Case 8: Change Password (Success)
# ==========================================
def test_change_password_success(logged_in_client, monkeypatch):
    """Test: Successful password change with valid input."""

    update_called = {"status": False, "hashed_pw": None}

    def mock_update_user_password(user, hashed_password):
        update_called["status"] = True
        update_called["hashed_pw"] = hashed_password

    # Proper module-level monkeypatch
    monkeypatch.setattr(account,
                        "update_user_password",
                        mock_update_user_password)

    NEW_PASSWORD = "new5678"

    response = logged_in_client.post(
        "/account",
        data={
            "action": "change_password",
            "current_password": TEST_USER_PASSWORD,
            "new_password": NEW_PASSWORD,
            "confirm_password": NEW_PASSWORD,
        },
        follow_redirects=True,
    )

    assert b"Password updated successfully!" in response.data
    assert update_called["status"]
    assert check_password_hash(update_called["hashed_pw"], NEW_PASSWORD)
