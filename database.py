"""
CiviNexa AI - Database Layer
Module: database.py

Manages SQLite connection, schema definition, parameterized queries,
and automatic table creation and demo data seeding.
"""

import os
import sqlite3
import datetime
import random
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "civinexa.db")


def get_db():
    """Returns a SQLite database connection with Row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes the database schema and populates sample demonstration data."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Complaints Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            complaint_title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            suggested_department TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            image_path TEXT,
            status TEXT NOT NULL DEFAULT 'Submitted',
            priority TEXT DEFAULT 'Medium',
            confidence INTEGER DEFAULT 80,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        );
    """)

    # 3. Admins Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Administrator',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Status History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            history_id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT NOT NULL,
            previous_status TEXT,
            new_status TEXT NOT NULL,
            admin_remarks TEXT,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE
        );
    """)

    conn.commit()

    # Seed sample demonstration data if database is brand new
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        seed_demonstration_data(conn)

    conn.close()


def seed_demonstration_data(conn):
    """Inserts initial demonstration records for admins, users, and civic complaints."""
    cursor = conn.cursor()
    now = datetime.datetime.now()

    # Seed Default Administrator (admin / admin123)
    admin_pw = generate_password_hash("admin123")
    cursor.execute("""
        INSERT INTO admins (username, password_hash, role, created_date)
        VALUES (?, ?, ?, ?)
    """, ("admin", admin_pw, "Chief Civic Administrator", now.strftime("%Y-%m-%d %H:%M:%S")))

    # Seed Demo Citizen (rahul.citizen@civinexa.org / citizen123)
    user_pw = generate_password_hash("citizen123")
    cursor.execute("""
        INSERT INTO users (user_id, name, email, phone, password_hash, created_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("USR-1001", "Rahul Sharma", "rahul.citizen@civinexa.org", "+91 98765 43210", user_pw, now.strftime("%Y-%m-%d %H:%M:%S")))
    demo_user_id = cursor.lastrowid

    # Seed Demo Complaints
    sample_complaints = [
        {
            "cid": "CNX-2026-1001",
            "title": "Severe Pothole causing traffic snarls on MG Road",
            "desc": "A dangerous 3-foot wide pothole has developed right near the metro pillar 42. Two two-wheelers skidded yesterday during evening rain.",
            "cat": "Road Maintenance",
            "dept": "Department of Roads & Infrastructure / Public Works (PWD)",
            "loc": "MG Road, Near Metro Pillar 42, Central Zone",
            "lat": 12.9752, "lng": 77.6067,
            "status": "In Progress",
            "priority": "High",
            "conf": 92,
            "history": [
                ("Submitted", "Complaint registered via CiviNexa Web Portal.", "2026-10-28 09:15:00"),
                ("Under Review", "Site inspection scheduled by Assistant Engineer PWD.", "2026-10-28 14:30:00"),
                ("In Progress", "Road asphalt repair crew dispatched; cold-mix filling underway.", "2026-10-29 11:00:00")
            ]
        },
        {
            "cid": "CNX-2026-1002",
            "title": "Overflowing Community Garbage Bin near City Park",
            "desc": "Garbage has not been collected for three days. Waste is spilling over onto the main footpath, emitting a foul stench and attracting stray animals.",
            "cat": "Waste Management",
            "dept": "Municipal Solid Waste Management & Sanitation Dept.",
            "loc": "7th Cross, East Park Boulevard, Ward 14",
            "lat": 12.9815, "lng": 77.6150,
            "status": "Under Review",
            "priority": "Medium",
            "conf": 88,
            "history": [
                ("Submitted", "Complaint registered with geolocation photos.", "2026-10-30 08:45:00"),
                ("Under Review", "Assigned to Ward 14 sanitation supervisor for priority clearing.", "2026-10-30 16:20:00")
            ]
        },
        {
            "cid": "CNX-2026-1003",
            "title": "Continuous Pipeline Burst causing Clean Water Waste",
            "desc": "Major drinking water pipeline burst near Residential Sector 3 junction. High pressure clean water is flooding the street since early morning.",
            "cat": "Water Supply",
            "dept": "Public Water Supply & Sewerage Board (Jal Board)",
            "loc": "Main Ring Road, Near Water Tank Sector 3",
            "lat": 12.9680, "lng": 77.5900,
            "status": "In Progress",
            "priority": "Urgent",
            "conf": 94,
            "history": [
                ("Submitted", "Auto-classified with Urgent priority by CiviNexa AI.", "2026-10-30 06:10:00"),
                ("In Progress", "Emergency valve shutoff executed. Excavation and pipe replacement started.", "2026-10-30 07:30:00")
            ]
        },
        {
            "cid": "CNX-2026-1004",
            "title": "Dead Streetlights on 12th Main causing darkness & safety hazard",
            "desc": "Three consecutive lampposts are non-functional for past 5 days. Entire street section is completely dark, creating danger for women and pedestrians.",
            "cat": "Electricity & Lighting",
            "dept": "City Electricity Board & Public Lighting Authority",
            "loc": "12th Main Road, Behind City College, South District",
            "lat": 12.9550, "lng": 77.5800,
            "status": "Resolved",
            "priority": "High",
            "conf": 89,
            "history": [
                ("Submitted", "Complaint registered by citizen Rahul Sharma.", "2026-10-26 20:10:00"),
                ("Under Review", "Forwarded to Lighting Maintenance Wing.", "2026-10-27 10:00:00"),
                ("In Progress", "Electrician team dispatched with replacement LED fixtures.", "2026-10-27 15:40:00"),
                ("Resolved", "LED lights and faulty cable connection successfully replaced and tested.", "2026-10-28 17:15:00")
            ]
        },
        {
            "cid": "CNX-2026-1005",
            "title": "Broken Swings and Damaged Boundary Railing at Children Park",
            "desc": "Children playground swings have broken metal chains with sharp edges. Part of the boundary fence has also collapsed.",
            "cat": "Public Infrastructure",
            "dept": "Urban Development & Civic Infrastructure Directorate",
            "loc": "Green Valley Children's Park, Block C",
            "lat": 12.9900, "lng": 77.6200,
            "status": "Submitted",
            "priority": "Low",
            "conf": 82,
            "history": [
                ("Submitted", "Complaint submitted with location coordinates.", "2026-10-31 10:00:00")
            ]
        }
    ]

    for item in sample_complaints:
        cursor.execute("""
            INSERT INTO complaints (
                complaint_id, user_id, complaint_title, description, category,
                suggested_department, location, latitude, longitude, status,
                priority, confidence, created_date, updated_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["cid"], demo_user_id, item["title"], item["desc"], item["cat"],
            item["dept"], item["loc"], item["lat"], item["lng"], item["status"],
            item["priority"], item["conf"],
            item["history"][0][2], item["history"][-1][2]
        ))

        # Insert history
        prev_st = None
        for hist_st, remarks, h_time in item["history"]:
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, admin_remarks, updated_date)
                VALUES (?, ?, ?, ?, ?)
            """, (item["cid"], prev_st, hist_st, remarks, h_time))
            prev_st = hist_st

    conn.commit()


# ==============================================================================
# Helper Query Functions
# ==============================================================================

def generate_complaint_id():
    """Generates a unique and human-readable complaint tracking ID (e.g., CNX-2026-4821)."""
    conn = get_db()
    cursor = conn.cursor()
    current_year = datetime.datetime.now().year
    while True:
        random_suffix = random.randint(1000, 9999)
        new_id = f"CNX-{current_year}-{random_suffix}"
        cursor.execute("SELECT 1 FROM complaints WHERE complaint_id = ?", (new_id,))
        if not cursor.fetchone():
            conn.close()
            return new_id


def create_user(name, email, password_hash, phone=""):
    """Registers a new citizen user."""
    conn = get_db()
    cursor = conn.cursor()
    user_id = f"USR-{random.randint(1000, 9999)}"
    cursor.execute("""
        INSERT INTO users (user_id, name, email, phone, password_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, name, email, phone, password_hash))
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id


def get_user_by_email(email):
    """Fetches user details by email."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    """Fetches user details by primary key."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_admin_by_username(username):
    """Fetches admin details by username."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", (username.strip(),))
    admin = cursor.fetchone()
    conn.close()
    return admin


def create_complaint(user_id, title, description, category, department, location,
                     latitude, longitude, image_path, priority="Medium", confidence=85):
    """Inserts a new civic complaint and creates the initial status history entry."""
    conn = get_db()
    cursor = conn.cursor()
    complaint_id = generate_complaint_id()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO complaints (
            complaint_id, user_id, complaint_title, description, category,
            suggested_department, location, latitude, longitude, image_path,
            status, priority, confidence, created_date, updated_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Submitted', ?, ?, ?, ?)
    """, (
        complaint_id, user_id, title, description, category,
        department, location, latitude, longitude, image_path,
        priority, confidence, now_str, now_str
    ))

    # Add initial status history
    cursor.execute("""
        INSERT INTO status_history (complaint_id, previous_status, new_status, admin_remarks, updated_date)
        VALUES (?, NULL, 'Submitted', 'Complaint successfully logged and submitted by citizen.', ?)
    """, (complaint_id, now_str))

    conn.commit()
    conn.close()
    return complaint_id


def get_complaint_by_id(complaint_id):
    """Retrieves full complaint information by unique ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, u.name as citizen_name, u.email as citizen_email, u.phone as citizen_phone
        FROM complaints c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.complaint_id = ?
    """, (complaint_id.strip(),))
    complaint = cursor.fetchone()
    conn.close()
    return complaint


def get_complaints_by_user(user_id):
    """Fetches all complaints submitted by a particular user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM complaints
        WHERE user_id = ?
        ORDER BY created_date DESC
    """, (user_id,))
    complaints = cursor.fetchall()
    conn.close()
    return complaints


def get_all_complaints(status_filter=None, category_filter=None, search_query=None):
    """Fetches all complaints with optional filtering by status, category, or search term."""
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT c.*, u.name as citizen_name, u.email as citizen_email
        FROM complaints c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != "All":
        query += " AND c.status = ?"
        params.append(status_filter)

    if category_filter and category_filter != "All":
        query += " AND c.category = ?"
        params.append(category_filter)

    if search_query:
        query += " AND (c.complaint_id LIKE ? OR c.complaint_title LIKE ? OR c.location LIKE ? OR c.description LIKE ?)"
        wildcard = f"%{search_query.strip()}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY c.created_date DESC"
    cursor.execute(query, params)
    complaints = cursor.fetchall()
    conn.close()
    return complaints


def update_complaint_status(complaint_id, new_status, remarks=""):
    """Updates the status of a complaint and logs a status history record."""
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get current status
    cursor.execute("SELECT status FROM complaints WHERE complaint_id = ?", (complaint_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    old_status = row["status"]

    # Update complaint
    cursor.execute("""
        UPDATE complaints
        SET status = ?, updated_date = ?
        WHERE complaint_id = ?
    """, (new_status, now_str, complaint_id))

    # Insert status history
    cursor.execute("""
        INSERT INTO status_history (complaint_id, previous_status, new_status, admin_remarks, updated_date)
        VALUES (?, ?, ?, ?, ?)
    """, (complaint_id, old_status, new_status, remarks.strip() if remarks else f"Status changed to {new_status}", now_str))

    conn.commit()
    conn.close()
    return True


def get_complaint_history(complaint_id):
    """Returns the ordered status timeline for a complaint."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM status_history
        WHERE complaint_id = ?
        ORDER BY updated_date ASC, history_id ASC
    """, (complaint_id.strip(),))
    history = cursor.fetchall()
    conn.close()
    return history


def get_dashboard_stats():
    """Computes overall summary metrics for the Admin Dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    # Total complaints
    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    # Status counts
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM complaints
        GROUP BY status
    """)
    status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

    # Category counts
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM complaints
        GROUP BY category
    """)
    category_counts = {row["category"]: row["count"] for row in cursor.fetchall()}

    # Total registered citizens
    cursor.execute("SELECT COUNT(*) FROM users")
    total_citizens = cursor.fetchone()[0]

    # Recent complaints (last 5)
    cursor.execute("""
        SELECT complaint_id, complaint_title, category, status, priority, created_date, location
        FROM complaints
        ORDER BY created_date DESC
        LIMIT 5
    """)
    recent_complaints = cursor.fetchall()

    conn.close()

    return {
        "total": total,
        "submitted": status_counts.get("Submitted", 0),
        "under_review": status_counts.get("Under Review", 0),
        "in_progress": status_counts.get("In Progress", 0),
        "resolved": status_counts.get("Resolved", 0),
        "rejected": status_counts.get("Rejected", 0),
        "pending_total": status_counts.get("Submitted", 0) + status_counts.get("Under Review", 0) + status_counts.get("In Progress", 0),
        "total_citizens": total_citizens,
        "category_counts": category_counts,
        "status_counts": status_counts,
        "recent_complaints": recent_complaints
    }
