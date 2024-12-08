import pytest
from bson import ObjectId
from app import app, col_users, col_groups
from flask import session
import os

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    # Mock environment variables before app import
    monkeypatch.setenv("MONGO_DBNAME", "TestDB")
    monkeypatch.setenv("MONGO_URI", "mongodb://localhost:27017")

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_user():
    """Insert a test user into the DB and yield it for testing."""
    user_id = ObjectId()
    # Hash for 'testpass'
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
    col_groups.insert_one(group)
    col_users.update_one({"_id": test_user["_id"]}, {"$push": {"groups": group_id}})
    yield group
    # Cleanup
    col_groups.delete_one({"_id": group_id})
    col_users.update_one({"_id": test_user["_id"]}, {"$set": {"groups": []}})

### HOME & AUTH TESTS ###

def test_home_logged_out(client):
    response = client.get("/main", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_home_logged_in(client, test_user):
    with client.session_transaction() as sess:
        sess["username"] = test_user["name"]
    response = client.get("/main")
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
    col_users.insert_one({
        "_id": user_id,
        "name": "existinguser",
        "password": b"somehash",
        "groups": []
    })

    data = {"username": "existinguser", "password": "newpass"}
    response = client.post("/registration", data=data, follow_redirects=True)
    assert b"Username already in use." in response.data

    col_users.delete_one({"_id": user_id})

def test_registration_new_user(client):
    data = {"username": "newuser", "password": "newpass"}
    response = client.post("/registration", data=data, follow_redirects=True)
    assert b"Registration successful. Please log in." in response.data

    user = col_users.find_one({"name": "newuser"})
    assert user is not None
    col_users.delete_one({"_id": user["_id"]})

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
    col_users.insert_one({
        "_id": user_id,
        "name": username,
        "password": hashed_password,
        "groups": []
    })

    data = {"username": username, "password": password}
    response = client.post("/login", data=data, follow_redirects=True)
    col_users.delete_one({"_id": user_id})

### CHECK-USER TESTS ###

def test_check_user_exists(client, test_user):
    # test_user fixture already creates 'testuser'
    response = client.get("/check-user?username=testuser")
    assert response.json == {"exists": True}

def test_check_user_not_exists(client):
    response = client.get("/check-user?username=notreal")
    assert response.json == {"exists": False}

### GROUP DETAILS TESTS ###

def test_group_details_no_login(client, test_group):
    response = client.get(f"/group/{test_group['_id']}", follow_redirects=True)
    assert b"Login" in response.data

def test_group_details_nonexistent(client, logged_in_user):
    response = client.get("/group/fakeid", follow_redirects=True)
    # Should flash "Group not found." and redirect
    assert b"Group not found." in response.data

def test_group_details_logged_in(client, logged_in_user, test_group):
    response = client.get(f"/group/{test_group['_id']}")
    assert response.status_code == 200
    assert b"Test Group" in response.data

### CREATE GROUP TESTS ###

def test_create_group_logged_out(client):
    response = client.get("/create-group", follow_redirects=True)
    assert b"Login" in response.data

def test_create_group_logged_in_empty_members(client, logged_in_user):
    data = {"group_name": "EmptyGroup", "members": ""}
    response = client.post("/create-group", data=data, follow_redirects=True)
    # Should fail because user doesn't exist or is empty input
    # The code tries to find members. If it fails, we get an error flash.
    # Adjust this assert if your code handles empty differently.
    # If your code doesn't handle empty well, consider adding that logic or skip this test.
    # If your code returns an error flash about non-existent users:


def test_create_group_logged_in_nonexistent_member(client, logged_in_user):
    data = {"group_name": "BadGroup", "members": "notexist"}
    response = client.post("/create-group", data=data, follow_redirects=True)

def test_create_group_success(client, logged_in_user, test_user):
    # current user is logged in and will be auto-added if not in members
    data = {"group_name": "MyNewGroup", "members": "testuser"}
    response = client.post("/create-group", data=data, follow_redirects=True)


### ADD EXPENSE TESTS ###

def test_add_expense_not_logged_in(client):
    response = client.get("/add-expense", follow_redirects=True)
    assert b"Login" in response.data

def test_add_expense_logged_in_no_groups(client, logged_in_user):
    response = client.get("/add-expense")
    assert b"Add Expense" in response.data

def test_add_expense_invalid_data_missing_percentages(client, logged_in_user, test_group):
    data = {
        "group_id": test_group["_id"],
        "description": "No Percentages",
        "amount": "100",
        "paid_by": "testuser",
        "split_with[]": ["testuser"],
        "percentages": ""  # empty
    }
    response = client.post("/add-expense", data=data, follow_redirects=True)


def test_add_expense_invalid_data_no_splits(client, logged_in_user, test_group):
    data = {
        "group_id": test_group["_id"],
        "description": "No Splits",
        "amount": "100",
        "paid_by": "testuser",
        # No split_with[] provided
        "percentages": "1.0"
    }
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
    # If code tries to find group and fails, might raise an error flash.
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

    updated_group = col_groups.find_one({"_id": test_group["_id"]})
    assert updated_group is not None
    assert len(updated_group["expenses"]) == 1
    expense = updated_group["expenses"][0]
    assert expense["description"] == "Test Dinner"
    assert expense["amount"] == 100.0
    assert expense["paid_by"] == "testuser"
    assert expense["split_among"]["testuser"] == 100.0
    assert b"Test Dinner" in response.data
    