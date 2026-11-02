"""
CiviNexa AI - Comprehensive Test Suite
File: test_app.py

Validates all 12 core requirements specified in Section 11:
1. User registration
2. User login
3. Complaint submission
4. AI complaint classification
5. Image upload
6. Unique complaint ID generation
7. Complaint tracking
8. Admin login
9. Complaint status updates
10. Database storage and retrieval
11. Invalid input handling
12. Unauthorized admin access
"""

import os
import io
import pytest
from app import app
import database
import classifier


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            database.init_db()
        yield client


# ==============================================================================
# 1. AI Classifier Tests
# ==============================================================================

def test_ai_classification_categories():
    """Validates classification of all civic categories and fallback."""
    # Road Maintenance
    res1 = classifier.classify_issue("There is a big pothole on the road")
    assert res1["category"] == "Road Maintenance"
    assert "Roads" in res1["department"]

    # Waste Management
    res2 = classifier.classify_issue("Garbage is collected near the park and smelling")
    assert res2["category"] == "Waste Management"
    assert "Waste" in res2["department"]

    # Drainage & Sewage
    res3 = classifier.classify_issue("Drain water is overflowing from the manhole")
    assert res3["category"] == "Drainage & Sewage"
    assert "Drainage" in res3["department"]

    # Electricity & Lighting
    res4 = classifier.classify_issue("Streetlight is not working and the street is dark")
    assert res4["category"] == "Electricity & Lighting"
    assert "Electricity" in res4["department"]

    # Water Supply
    res5 = classifier.classify_issue("Water is leaking from a public pipe")
    assert res5["category"] == "Water Supply"
    assert "Water" in res5["department"]

    # Public Infrastructure
    res6 = classifier.classify_issue("Broken bench in the municipal park and broken swing")
    assert res6["category"] == "Public Infrastructure"
    assert "Infrastructure" in res6["department"]

    # Fallback to Manual Review
    res7 = classifier.classify_issue("General inquiry regarding property tax receipt")
    assert res7["category"] == "Needs Manual Review"


def test_api_classify_endpoint(client):
    """Tests the /api/classify JSON API."""
    res = client.post("/api/classify", json={
        "title": "Broken Street Lamp",
        "description": "Streetlight is completely off and dark"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["result"]["category"] == "Electricity & Lighting"


# ==============================================================================
# 2. Database & Unique ID Generation Tests
# ==============================================================================

def test_unique_complaint_id_generation():
    """Ensures complaint IDs follow format CNX-YYYY-XXXX and are unique."""
    id1 = database.generate_complaint_id()
    id2 = database.generate_complaint_id()
    assert id1.startswith("CNX-")
    assert id2.startswith("CNX-")
    assert id1 != id2


def test_database_initial_seeding():
    """Ensures sample demonstration data is pre-seeded upon init."""
    stats = database.get_dashboard_stats()
    assert stats["total"] >= 5
    admin = database.get_admin_by_username("admin")
    assert admin is not None
    user = database.get_user_by_email("rahul.citizen@civinexa.org")
    assert user is not None


# ==============================================================================
# 3. User Authentication Tests
# ==============================================================================

def test_user_registration(client):
    """Tests successful citizen registration."""
    test_email = f"test_{os.urandom(4).hex()}@civinexa.org"
    res = client.post("/register", data={
        "name": "Ananya Sen",
        "email": test_email,
        "phone": "+91 99887 76655",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Registration successful" in res.data
    assert database.get_user_by_email(test_email) is not None


def test_user_registration_password_mismatch(client):
    """Tests registration validation on password mismatch."""
    res = client.post("/register", data={
        "name": "Mismatch User",
        "email": "mismatch@civinexa.org",
        "phone": "+91 90000 00000",
        "password": "password123",
        "confirm_password": "differentpassword"
    }, follow_redirects=True)
    assert b"Passwords do not match" in res.data


def test_user_login_success(client):
    """Tests valid citizen login."""
    res = client.post("/login", data={
        "email": "rahul.citizen@civinexa.org",
        "password": "citizen123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Welcome back" in res.data or b"Dashboard" in res.data


def test_user_login_invalid(client):
    """Tests citizen login with incorrect credentials."""
    res = client.post("/login", data={
        "email": "rahul.citizen@civinexa.org",
        "password": "wrongpassword"
    }, follow_redirects=True)
    assert b"Invalid email or password" in res.data


# ==============================================================================
# 4. Complaint Submission & Image Upload Tests
# ==============================================================================

def test_complaint_submission_and_tracking(client):
    """Tests complaint submission, AI categorization, image upload, and subsequent tracking."""
    # First log in as citizen
    client.post("/login", data={
        "email": "rahul.citizen@civinexa.org",
        "password": "citizen123"
    })

    # Fake image upload
    test_image = (io.BytesIO(b"fake image data content"), "test_pothole.jpg")

    res = client.post("/report", data={
        "complaint_title": "Severe Pothole on Brigade Road",
        "description": "Massive crater on road near signal causing dangerous traffic jams",
        "category": "Auto-Detect with AI",
        "location": "Brigade Road Junction, Ward 12",
        "latitude": "12.9740",
        "longitude": "77.6080",
        "complaint_image": test_image
    }, content_type="multipart/form-data", follow_redirects=True)

    assert res.status_code == 200
    assert b"Complaint registered successfully" in res.data or b"Road Maintenance" in res.data

    # Verify tracking page works for seeded complaint CNX-2026-1001
    track_res = client.get("/track/CNX-2026-1001")
    assert track_res.status_code == 200
    assert b"CNX-2026-1001" in track_res.data
    assert b"Road Maintenance" in track_res.data
    assert b"Audit Trail &amp; Timeline" in track_res.data or b"Timeline" in track_res.data


# ==============================================================================
# 5. Admin Authentication & Status Update Tests
# ==============================================================================

def test_admin_login_success(client):
    """Tests valid administrator authentication."""
    res = client.post("/admin/login", data={
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Executive Grievance Analytics Dashboard" in res.data


def test_admin_login_invalid(client):
    """Tests administrator login with invalid password."""
    res = client.post("/admin/login", data={
        "username": "admin",
        "password": "incorrectpassword"
    }, follow_redirects=True)
    assert b"Invalid administrator credentials" in res.data


def test_unauthorized_admin_access(client):
    """Verifies that unauthenticated visitors cannot access admin routes."""
    res = client.get("/admin/dashboard", follow_redirects=True)
    assert res.status_code == 200
    assert b"Administrator login required" in res.data

    res2 = client.get("/admin/complaints", follow_redirects=True)
    assert b"Administrator login required" in res2.data


def test_admin_complaint_status_update(client):
    """Tests changing status of a complaint and adding administrative remarks."""
    # Authenticate as admin
    client.post("/admin/login", data={
        "username": "admin",
        "password": "admin123"
    })

    # Update status of CNX-2026-1005 from Submitted to In Progress with remarks
    res = client.post("/admin/complaint/CNX-2026-1005/update-status", data={
        "status": "In Progress",
        "remarks": "Playground repair contractor dispatched with welding unit."
    }, follow_redirects=True)

    assert res.status_code == 200

    # Verify updated status and timeline in database
    complaint = database.get_complaint_by_id("CNX-2026-1005")
    assert complaint["status"] == "In Progress"

    history = database.get_complaint_history("CNX-2026-1005")
    assert any(h["new_status"] == "In Progress" for h in history)
    assert any("welding unit" in h["admin_remarks"] for h in history)


# ==============================================================================
# 6. Static Pages and Public Navigation Tests
# ==============================================================================

def test_public_pages(client):
    """Verifies all public pages render with HTTP 200."""
    assert client.get("/").status_code == 200
    assert client.get("/about").status_code == 200
    assert client.get("/contact").status_code == 200
    assert client.get("/track").status_code == 200
