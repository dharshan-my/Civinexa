"""
CiviNexa AI - AI-Powered Civic Issue Reporting and Tracking System
Main Application Controller: app.py
"""

import os
import time
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import database
import classifier

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "civinexa-ai-super-secret-key-2026-production")

# Configuration for File Uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """Checks if the uploaded file has an allowed image extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ==============================================================================
# Authentication Decorators
# ==============================================================================

def login_required(f):
    """Restricts access to authenticated citizens."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Restricts access to authenticated administrators."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Administrator login required to access the admin portal.", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# Public & Citizen Routes
# ==============================================================================

@app.route("/")
def index():
    """Landing Page showcasing CiviNexa AI capabilities and recent civic resolution stats."""
    stats = database.get_dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/about")
def about():
    """About Us page explaining the platform vision, AI architecture, and municipal workflow."""
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page with municipal helpline directories and inquiry form."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all required contact fields.", "warning")
        else:
            flash("Thank you for reaching out! Your message has been forwarded to the Civic Liaison Office.", "success")
            return redirect(url_for("contact"))

    return render_template("contact.html")


# ==============================================================================
# Citizen Authentication Routes
# ==============================================================================

@app.route("/register", methods=["GET", "POST"])
def register():
    """Citizen user registration."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return render_template("register.html", name=name, email=email, phone=phone)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", name=name, email=email, phone=phone)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", name=name, email=email, phone=phone)

        existing_user = database.get_user_by_email(email)
        if existing_user:
            flash("An account with this email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)
        user_id = database.create_user(name, email, password_hash, phone)

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Citizen user login."""
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = database.get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if next_page else url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Logs out the current citizen session."""
    session.pop("user_id", None)
    session.pop("user_name", None)
    session.pop("user_email", None)
    flash("You have been safely logged out.", "info")
    return redirect(url_for("login"))


# ==============================================================================
# Citizen Dashboard & Complaint Operations
# ==============================================================================

@app.route("/dashboard")
@login_required
def dashboard():
    """Citizen personal dashboard displaying their submitted issues and statuses."""
    user_id = session["user_id"]
    complaints = database.get_complaints_by_user(user_id)

    total_count = len(complaints)
    resolved_count = sum(1 for c in complaints if c["status"] == "Resolved")
    in_progress_count = sum(1 for c in complaints if c["status"] == "In Progress")
    review_count = sum(1 for c in complaints if c["status"] in ("Submitted", "Under Review"))

    return render_template(
        "dashboard.html",
        complaints=complaints,
        total_count=total_count,
        resolved_count=resolved_count,
        in_progress_count=in_progress_count,
        review_count=review_count
    )


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    """Complaint submission page with Leaflet map location picker and AI categorization."""
    if request.method == "POST":
        title = request.form.get("complaint_title", "").strip()
        description = request.form.get("description", "").strip()
        user_selected_category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        latitude_str = request.form.get("latitude", "").strip()
        longitude_str = request.form.get("longitude", "").strip()

        # Validation
        if not title or not description or not location:
            flash("Please provide a complaint title, detailed description, and location.", "danger")
            return render_template("report.html", title=title, description=description, location=location)

        # Parse coordinates
        try:
            latitude = float(latitude_str) if latitude_str else 12.9716
            longitude = float(longitude_str) if longitude_str else 77.5946
        except ValueError:
            latitude = 12.9716
            longitude = 77.5946

        # Run AI Classification Engine
        ai_result = classifier.classify_issue(description=description, title=title)

        # If user explicitly picked an overriding category, respect their choice
        if user_selected_category and user_selected_category != "Auto-Detect with AI":
            final_category = user_selected_category
            config = classifier.CivicIssueClassifier.CATEGORIES_CONFIG.get(final_category)
            final_department = config["department"] if config else ai_result["department"]
        else:
            final_category = ai_result["category"]
            final_department = ai_result["department"]

        # Handle Image File Upload
        image_path = None
        if "complaint_image" in request.files:
            file = request.files["complaint_image"]
            if file and file.filename != "" and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                unique_filename = f"{int(time.time())}_{safe_name}"
                file_dest = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
                file.save(file_dest)
                image_path = unique_filename

        # Insert Complaint into Database
        complaint_id = database.create_complaint(
            user_id=session["user_id"],
            title=title,
            description=description,
            category=final_category,
            department=final_department,
            location=location,
            latitude=latitude,
            longitude=longitude,
            image_path=image_path,
            priority=ai_result["priority"],
            confidence=ai_result["confidence_percent"]
        )

        flash(
            f"Complaint registered successfully! Your tracking ID is {complaint_id}. "
            f"AI assigned category '{final_category}' to '{final_department}'.",
            "success"
        )
        return redirect(url_for("track", complaint_id=complaint_id))

    return render_template("report.html")


@app.route("/track")
@app.route("/track/<complaint_id>")
def track(complaint_id=None):
    """Complaint tracking module allowing citizens to view chronological progress."""
    search_id = complaint_id or request.args.get("complaint_id", "").strip()
    complaint = None
    history = []

    if search_id:
        complaint = database.get_complaint_by_id(search_id)
        if complaint:
            history = database.get_complaint_history(search_id)
        else:
            flash(f"No complaint found matching ID '{search_id}'. Please check and try again.", "warning")

    return render_template("track.html", complaint=complaint, history=history, search_id=search_id)


# ==============================================================================
# Administrator Routes
# ==============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Administrator authentication portal."""
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = database.get_admin_by_username(username)
        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["admin_id"]
            session["admin_username"] = admin["username"]
            session["admin_role"] = admin["role"]
            flash(f"Welcome to CiviNexa Admin Command Center, {admin['username']}!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid administrator credentials. Access denied.", "danger")

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    """Logs out the administrative session."""
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    session.pop("admin_role", None)
    flash("Administrator logged out successfully.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Administrator dashboard showcasing aggregate metrics and recent complaints."""
    stats = database.get_dashboard_stats()
    return render_template("admin_dashboard.html", stats=stats)


@app.route("/admin/complaints")
@admin_required
def complaints():
    """Complaint management page with filters, search, and status update actions."""
    status_filter = request.args.get("status", "All")
    category_filter = request.args.get("category", "All")
    search_query = request.args.get("search", "").strip()

    all_complaints = database.get_all_complaints(
        status_filter=status_filter,
        category_filter=category_filter,
        search_query=search_query
    )

    categories = list(classifier.CivicIssueClassifier.CATEGORIES_CONFIG.keys()) + ["Needs Manual Review"]

    return render_template(
        "complaints.html",
        complaints=all_complaints,
        categories=categories,
        current_status=status_filter,
        current_category=category_filter,
        search_query=search_query
    )


@app.route("/admin/complaint/<complaint_id>/update-status", methods=["POST"])
@admin_required
def update_status(complaint_id):
    """Processes status change and logs administrative remarks."""
    new_status = request.form.get("status", "").strip()
    remarks = request.form.get("remarks", "").strip()

    valid_statuses = {"Submitted", "Under Review", "In Progress", "Resolved", "Rejected"}
    if new_status not in valid_statuses:
        flash("Invalid status specified.", "danger")
        return redirect(url_for("complaints"))

    success = database.update_complaint_status(complaint_id, new_status, remarks)
    if success:
        flash(f"Complaint {complaint_id} status updated to '{new_status}'.", "success")
    else:
        flash(f"Failed to update complaint {complaint_id}.", "danger")

    return redirect(request.referrer or url_for("complaints"))


# ==============================================================================
# API Endpoints (For Live UI Enhancements)
# ==============================================================================

@app.route("/api/classify", methods=["POST"])
def api_classify():
    """Live JSON endpoint for real-time AI classification preview in reporting form."""
    data = request.get_json(silent=True) or {}
    description = data.get("description", "")
    title = data.get("title", "")

    result = classifier.classify_issue(description=description, title=title)
    return jsonify({"status": "success", "result": result})


@app.route("/api/stats", methods=["GET"])
def api_stats():
    """JSON API returning dashboard statistics for Chart.js rendering."""
    stats = database.get_dashboard_stats()
    return jsonify({
        "status": "success",
        "category_counts": stats["category_counts"],
        "status_counts": stats["status_counts"],
        "total": stats["total"]
    })


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    """Securely serves uploaded complaint photographs."""
    safe_filename = secure_filename(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_filename)


# ==============================================================================
# Application Startup
# ==============================================================================

if __name__ == "__main__":
    # Ensure database tables and demo records are initialized
    database.init_db()
    print("=" * 60)
    print(" CiviNexa AI - Municipal Issue Reporting & Tracking System")
    print(" Server running at: http://127.0.0.1:5000")
    print(" Demo Admin: admin / admin123")
    print(" Demo Citizen: rahul.citizen@civinexa.org / citizen123")
    print("=" * 60)
    app.run(debug=True, port=5000)
