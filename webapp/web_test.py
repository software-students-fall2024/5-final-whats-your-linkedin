import pytest
import os
from bson import ObjectId
from unittest.mock import patch
import mongomock

# Set environment variables before importing app
os.environ["MONGO_URI"] = "mongodb://localhost:27017"
os.environ["MONGO_DBNAME"] = "test_database"
os.environ["SECRET_KEY"] = "test_key"

import app  # Import after env variables are set

@pytest.fixture(scope='session', autouse=True)
def mock_db():
    # Use mongomock to simulate an in-memory MongoDB
    mock_client = mongomock.MongoClient()
    test_db = mock_client["test_database"]
    # Patch the app's database references
    app.client = mock_client
    app.mydb = test_db
    app.col_users = test_db["USERS"]
    app.col_groups = test_db["GROUPS"]


@pytest.fixture
def client():
    app.app.config["TESTING"] = True
    with app.app.test_client() as client:
        yield client

@pytest.fixture
def test_user():
    """Insert a test user into the DB and yield it for testing."""
    user_id = ObjectId()
    # Pre-hashed password for "testpass"
    hashed_password = b"$2b$12$W0.Vj4Rg.T/JC2yKWZVJZ.u42eQZMebZxbXr6kJ9QZPdbjXQfSG06"
    app.col_users.insert_one({
        "_id": user_id,
        "name": "testuser",
        "password": hashed_password,
        "groups": []
    })
    yield {"_id": user_id, "name": "testuser"}
    app.col_users.delete_one({"_id": user_id})

@pytest.fixture
def logged_in_user(client, test_user):
    """Simulate a logged-in user by setting session."""
    with client.session_transaction() as sess:
        sess["username"] = test_user["name"]

@pytest.fixture
def test_group(test_user):
    """Create a test group and link it to test_user."""
    group_id = str(ObjectId())
    group = {
        "_id": group_id,
        "group_name": "Test Group",
        "group_members": [test_user["name"]],
        "balances": {test_user["name"]: 0},
        "expenses": []
    }
    app.col_groups.insert_one(group)
    app.col_users.update_one({"_id": test_user["_id"]}, {"$push": {"groups": group_id}})
    yield group
    # Cleanup
    app.col_groups.delete_one({"_id": group_id})
    app.col_users.update_one({"_id": test_user["_id"]}, {"$set": {"groups": []}})

### HOME & AUTH TESTS ###

def test_home_logged_out(client):
    response = client.get("/main", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_home_logged_in(client, test_user):
    with client.session_transaction() as sess:
        sess["username"] = test_user["name"]
    response = client.get("/main", follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome to SplitSmart!" in response.data

def test_groups_no_login(client):
    response = client.get("/groups", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

### REGISTRATION TESTS ###

def test_registration_page_loads(client):
    response = client.get("/registration")
    assert response.status_code == 200
    assert b"Sign Up" in response.data

def test_registration_existing_user(client):
    user_id = ObjectId()
    app.col_users.insert_one({
        "_id": user_id,
        "name": "existinguser",
        "password": b"somehash",
        "groups": []
    })

    data = {"username": "existinguser", "password": "newpass"}
    response = client.post("/registration", data=data, follow_redirects=True)
    # After redirect, check for the flash message
    assert b"Username already in use." in response.data

    app.col_users.delete_one({"_id": user_id})

def test_registration_new_user(client):
    data = {"username": "newuser", "password": "newpass"}
    response = client.post("/registration", data=data, follow_redirects=True)
    # Check if user is inserted
    user = app.col_users.find_one({"name": "newuser"})
    assert user is not None  # Ensure user was actually created
    app.col_users.delete_one({"_id": user["_id"]})

### LOGIN TESTS ###

def test_login_nonexistent_user(client):
    data = {"username": "nonexist", "password": "something"}
    response = client.post("/login", data=data, follow_redirects=True)
    assert b"Username not found." in response.data

def test_login_invalid_password(client, test_user):
    data = {"username": test_user["name"], "password": "wrongpass"}
    response = client.post("/login", data=data, follow_redirects=True)
    assert b"Invalid password. Please try again" in response.data

def test_login_valid(client):
    username = "validuser"
    password = "secretpass"
    hashed_password = b"$2b$12$W0.Vj4Rg.T/JC2yKWZVJZ.u42eQZMebZxbXr6kJ9QZPdbjXQfSG06"
    user_id = ObjectId()
    app.col_users.insert_one({
        "_id": user_id,
        "name": username,
        "password": hashed_password,
        "groups": []
    })

    data = {"username": username, "password": password}
    response = client.post("/login", data=data, follow_redirects=True)
    # Check a successful login flash message or redirect
    app.col_users.delete_one({"_id": user_id})

### CHECK-USER TESTS ###

def test_check_user_exists(client, test_user):
    # Now testuser exists
    response = client.get("/check-user?username=testuser")
    assert response.json == {"exists": True}

def test_check_user_not_exists(client):
    response = client.get("/check-user?username=notreal")
    assert response.json == {"exists": False}

### GROUP DETAILS TESTS ###

def test_group_details_no_login(client, test_group):
    response = client.get(f"/group/{test_group['_id']}", follow_redirects=True)
    # Without login, should redirect to login page
    assert b"Login" in response.data

def test_group_details_logged_in(client, logged_in_user, test_group):
    # User is logged in now
    response = client.get(f"/group/{test_group['_id']}", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Group" in response.data

### CREATE GROUP TESTS ###

def test_create_group_logged_out(client):
    response = client.get("/create-group", follow_redirects=True)
    assert b"Login" in response.data

def test_create_group_logged_in_empty_members(client, logged_in_user):
    data = {"group_name": "EmptyGroup", "members": ""}
    # This should flash an error since no members are found
    response = client.post("/create-group", data=data, follow_redirects=True)
    assert b"does not exist" in response.data or b"error" in response.data

def test_create_group_logged_in_nonexistent_member(client, logged_in_user):
    data = {"group_name": "BadGroup", "members": "notexist"}
    response = client.post("/create-group", data=data, follow_redirects=True)
    assert b"does not exist" in response.data

def test_create_group_success(client, logged_in_user, test_user):
    data = {"group_name": "MyNewGroup", "members": "testuser"}
    response = client.post("/create-group", data=data, follow_redirects=True)

### ADD EXPENSE TESTS ###

def test_add_expense_not_logged_in(client):
    response = client.get("/add-expense", follow_redirects=True)
    assert b"Login" in response.data

def test_add_expense_logged_in_no_groups(client, logged_in_user):
    # Logged in but user has no groups, the page should still show Add Expense template or a redirect?
    # If code redirects when no groups are found, handle accordingly
    response = client.get("/add-expense", follow_redirects=True)
    # If it redirects to groups, you might see "Login" or "Not logged in." If it shows empty groups, adjust this check.
    # If you want it to show "Add Expense", ensure user has a group before testing.
    assert b"Add Expense" in response.data or b"create new group" in response.data

def test_add_expense_invalid_data_no_splits(client, logged_in_user, test_group):
    data = {
        "group_id": test_group["_id"],
        "description": "No Splits",
        "amount": "100",
        "paid_by": "testuser",
        "percentages": "1.0"
    }
    # Missing 'split_with[]'
    response = client.post("/add-expense", data=data, follow_redirects=True)
    assert b"The number of split members and percentages do not match." in response.data

def test_add_expense_invalid_group(client, logged_in_user):
    data = {
        "group_id": "fakegroupid",
        "description": "Fake Group Expense",
        "amount": "100",
        "paid_by": "testuser",
        "split_with[]": ["testuser"],
        "percentages": "1.0"
    }
    response = client.post("/add-expense", data=data, follow_redirects=True)
    assert b"Error adding expense:" in response.data

def test_add_expense_success(client, logged_in_user, test_group):
    data = {
        "group_id": test_group["_id"],
        "description": "Test Dinner",
        "amount": "100",
        "paid_by": "testuser",
        "split_with[]": ["testuser"],
        "percentages": "1.0"
    }
    response = client.post("/add-expense", data=data, follow_redirects=True)
    assert b"Expense added successfully!" in response.data

    updated_group = app.col_groups.find_one({"_id": test_group["_id"]})
    assert updated_group is not None
    assert len(updated_group["expenses"]) == 1
    expense = updated_group["expenses"][0]
    assert expense["description"] == "Test Dinner"
    assert expense["amount"] == 100.0
    assert expense["paid_by"] == "testuser"
    assert expense["split_among"]["testuser"] == 100.0

### SETTLE PAYMENTS TESTS ###

def test_settle_payment_not_logged_in(client):
    response = client.get("/settle-payment", follow_redirects=True)
    assert response.status_code == 200
    assert b"Not logged in" in response.data


def test_settle_payment_page_loads(client, logged_in_user):
    response = client.get("/settle-payment", follow_redirects=True)
    assert response.status_code == 200
    assert b"Settle Payments" in response.data


def test_settle_payment_invalid_group(client, logged_in_user):
    data = {
        "group_id": "nonexistentgroup",
        "payment_amount": "50",
    }
    response = client.post("/settle-payment", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Group not found" in response.data


def test_settle_payment_invalid_amount(client, logged_in_user, test_group):
    data = {
        "group_id": test_group["_id"],
        "payment_amount": "-50",
    }
    response = client.post("/settle-payment", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Payment amount must be greater than zero" in response.data


def test_settle_payment_no_balance(client, logged_in_user, test_group):
    app.col_groups.update_one(
        {"_id": test_group["_id"]},
        {"$set": {"balances": {test_group["group_members"][0]: 0}}}
    )

    data = {
        "group_id": test_group["_id"],
        "payment_amount": "50",
    }
    response = client.post("/settle-payment", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"You have no outstanding balance to settle." in response.data


def test_settle_payment_full_balance(client, logged_in_user, test_group):
    app.col_groups.update_one(
        {"_id": test_group["_id"]},
        {"$set": {"balances": {test_group["group_members"][0]: -50, "creditor": 50}}}
    )

    data = {
        "group_id": test_group["_id"],
        "payment_amount": "50",
    }
    response = client.post("/settle-payment", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Payment settled successfully!" in response.data

    updated_group = app.col_groups.find_one({"_id": test_group["_id"]})
    assert updated_group["balances"][test_group["group_members"][0]] == 0
    assert updated_group["balances"]["creditor"] == 0


def test_settle_payment_partial_balance(client, logged_in_user, test_group):
    app.col_groups.update_one(
        {"_id": test_group["_id"]},
        {"$set": {"balances": {test_group["group_members"][0]: -75, "creditor": 75}}}
    )

    data = {
        "group_id": test_group["_id"],
        "payment_amount": "50",
    }
    response = client.post("/settle-payment", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"Payment settled successfully!" in response.data

    updated_group = app.col_groups.find_one({"_id": test_group["_id"]})
    assert updated_group["balances"][test_group["group_members"][0]] == -25
    assert updated_group["balances"]["creditor"] == 25
