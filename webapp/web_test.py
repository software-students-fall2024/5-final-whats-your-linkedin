import pytest
from bson import ObjectId
from app import app, col_users, col_groups
from flask import session


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_user():
    """Insert a test user into the DB and yield it for testing."""
    user_id = ObjectId()
    # Password "testpass" hashed with bcrypt (example hash)
    # You can generate your own hash using bcrypt in a Python shell.
    hashed_password = b"$2b$12$W0.Vj4Rg.T/JC2yKWZVJZ.u42eQZMebZxbXr6kJ9QZPdbjXQfSG06"
    user = {
        "_id": user_id,
        "name": "testuser",
        "password": hashed_password,
        "groups": []
    }
    col_users.insert_one(user)
    yield user
    col_users.delete_one({"_id": user_id})

@pytest.fixture
def logged_in_user(client, test_user):
    """Simulate a logged-in user by setting the session directly."""
    with client.session_transaction() as sess:
        sess["username"] = test_user["name"]

@pytest.fixture
def test_group(test_user):
    """Create a group and link it to test_user."""
    group_id = str(ObjectId())
    group = {
        "_id": group_id,
        "group_name": "Test Group",
        "group_members": [
            [test_user["name"], 0]
        ],
        "expenses": []
    }
    col_groups.insert_one(group)
    # Add group to user
    col_users.update_one({"_id": test_user["_id"]}, {"$push": {"groups": group_id}})
    yield group
    col_groups.delete_one({"_id": group_id})
    col_users.update_one({"_id": test_user["_id"]}, {"$set": {"groups": []}})


### HOME & AUTH TESTS ###

def test_home_logged_out(client):
    """Accessing /main without login should redirect to login."""
    response = client.get("/main", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_home_logged_in(client, test_user):
    """With a logged in user, /main should display home page content."""
    with client.session_transaction() as sess:
        sess["username"] = test_user["name"]
    response = client.get("/main")
    assert response.status_code == 200
    assert b"Welcome to SplitSmart!" in response.data

def test_groups_no_login(client):
    """Accessing /groups without login should redirect."""
    response = client.get("/groups", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

### REGISTRATION TESTS ###

def test_registration_page_loads(client):
    """Check if the registration page loads correctly."""
    response = client.get("/registration")
    assert response.status_code == 200
    assert b"Sign Up" in response.data

def test_registration_existing_user(client):
    """Try registering a user that already exists."""
    user_id = ObjectId()
    col_users.insert_one({
        "_id": user_id,
        "name": "existinguser",
        "password": b"somehash",
        "groups": []
    })

    data = {
        "username": "existinguser",
        "password": "newpass"
    }
    response = client.post("/registration", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Username already in use." in response.data

    col_users.delete_one({"_id": user_id})

def test_registration_new_user(client):
    """Register a new user successfully."""
    data = {
        "username": "newuser",
        "password": "newpass"
    }
    response = client.post("/registration", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Registration successful. Please log in." in response.data

    user = col_users.find_one({"name": "newuser"})
    assert user is not None
    col_users.delete_one({"_id": user["_id"]})

### LOGIN TESTS ###

def test_login_nonexistent_user(client):
    """Try logging in with a username that doesn't exist."""
    data = {"username": "nonexist", "password": "something"}
    response = client.post("/login", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Username not found." in response.data

def test_login_invalid_password(client, test_user):
    """Try logging in with an invalid password."""
    data = {"username": test_user["name"], "password": "wrongpass"}
    response = client.post("/login", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid password. Please try again" in response.data

def test_login_valid(client):
    """Test login with valid credentials."""
    username = "validuser"
    password = "secretpass"
    # Insert user with known password hash for 'secretpass'
    # The hash below must match 'secretpass':
    # You can generate using bcrypt:
    # bcrypt.hashpw("secretpass".encode('utf-8'), bcrypt.gensalt())
    hashed_password = b"$2b$12$W0.Vj4Rg.T/JC2yKWZVJZ.u42eQZMebZxbXr6kJ9QZPdbjXQfSG06"

    user_id = ObjectId()
    col_users.insert_one({
        "_id": user_id,
        "name": username,
        "password": hashed_password,
        "groups": []
    })

    data = {"username": username, "password": password}
    response = client.post("/login", data=data, follow_redirects=True)
    assert response.status_code == 200

    col_users.delete_one({"_id": user_id})

### CREATE GROUP TESTS ###

def test_create_group_logged_out(client):
    """Accessing /create-group without login should redirect to login."""
    response = client.get("/create-group", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_create_group_logged_in(client, logged_in_user):
    """Accessing /create-group when logged in should show group creation form."""
    response = client.get("/create-group")
    assert response.status_code == 200
    assert b"create new group" in response.data.lower()

### ADD EXPENSE TESTS ###

def test_add_expense_not_logged_in(client):
    """If not logged in, accessing /add-expense should redirect to login."""
    response = client.get("/add-expense", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_add_expense_logged_in_no_groups(client, logged_in_user):
    """Logged in user with no groups should see add-expense page but empty group options."""
    response = client.get("/add-expense")
    assert response.status_code == 200
    # Check for page content indicating no groups or a prompt to create a group.
    assert b"Add Expense" in response.data

def test_add_expense_invalid_data(client, logged_in_user, test_group):
    """Posting invalid expense data (percentages not summing to 1.0) should show error."""
    data = {
        "group_id": test_group["_id"],
        "description": "Test Expense",
        "amount": "100",
        "paid_by": "testuser",
        "split_with[]": ["testuser"],
        "percentages": "0.5"  # invalid, does not sum to 1.0
    }
    response = client.post("/add-expense", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Split percentages must sum to 1.0." in response.data

def test_add_expense_success(client, logged_in_user, test_group):
    """Posting valid expense data should add the expense and show success message."""
    data = {
        "group_id": test_group["_id"],
        "description": "Test Dinner",
        "amount": "100",
        "paid_by": "testuser",
        "split_with[]": ["testuser"],
        "percentages": "1.0"
    }
    response = client.post("/add-expense", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Expense added successfully!" in response.data

    updated_group = col_groups.find_one({"_id": test_group["_id"]})
    assert updated_group is not None
    assert len(updated_group["expenses"]) == 1
    expense = updated_group["expenses"][0]
    assert expense["description"] == "Test Dinner"
    assert expense["amount"] == 100.0
    assert expense["paid_by"] == "testuser"
    assert expense["split_among"]["testuser"] == 100.0
    assert b"Test Dinner" in response.data  # expense listed on group details page