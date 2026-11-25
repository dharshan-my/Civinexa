# 🚀 CiviNexa AI

**Smart Civic Intelligence. Transparent Public Services.**

CiviNexa AI is an AI-powered civic intelligence platform designed to simplify the process of reporting and tracking public infrastructure problems. It helps citizens report civic issues such as road damage, garbage accumulation, drainage overflow, and broken streetlights.

The platform analyzes submitted complaints, identifies the issue category, suggests the relevant government department, and generates a unique complaint tracking ID.

---

## 🌐 Quick Run Links (Localhost)

When running the project locally, access it at:

* 🏠 **Local Application Link:** [http://localhost:5000](http://localhost:5000) *(or [http://127.0.0.1:5000](http://127.0.0.1:5000))*
* 📝 **Report Grievance:** [http://localhost:5000/report](http://localhost:5000/report)
* 🔍 **Track Complaint:** [http://localhost:5000/track](http://localhost:5000/track)
* 👤 **Citizen Login:** [http://localhost:5000/login](http://localhost:5000/login)
* 🛡️ **Admin Portal:** [http://localhost:5000/admin/login](http://localhost:5000/admin/login)

### 🔑 Demo Login Credentials

| Portal | Username / Email | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin` *(or `dharshan`)* | `admin123` |
| **Citizen** | `rahul.citizen@civinexa.org` | `citizen123` |

---

## ⚡ How to Run the Project

### Option 1: 1-Click Launch (Windows)
Double-click the **`run.bat`** file in the project directory. It automatically installs dependencies, boots the Flask server, and opens the browser.

### Option 2: Command Line
```bash
# 1. Clone repository
git clone https://github.com/dharshan-my/Civinexa.git
cd Civinexa

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the application
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🎯 Objectives

- Simplify civic issue reporting.
- Use AI-based classification to identify public problems.
- Suggest relevant government departments.
- Improve complaint tracking and transparency.
- Help administrators manage and monitor civic complaints.

## ✨ Key Features

- **AI Complaint Analyzer:** Analyzes complaint descriptions and identifies issue categories.
- **Smart Department Finder:** Suggests the appropriate department based on the reported issue.
- **Photo Upload:** Allows citizens to upload images as evidence.
- **Location Tracking:** Captures or accepts the location of reported issues via interactive OpenStreetMap / Leaflet.
- **Complaint Tracking:** Generates unique complaint IDs to track progress.
- **Admin Dashboard:** Allows administrators to view complaints and update their status.
- **Duplicate Detection:** Identifies potentially duplicate complaints.

## 🛠️ Technologies Used

- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
- **Backend:** Python, Flask
- **Database:** SQLite (with WAL mode & foreign keys)
- **AI Engine:** Keyword-weighted semantic classification
- **Maps:** OpenStreetMap and Leaflet.js

## 🔄 Working Process

1. Citizens submit civic complaints.
2. The system analyzes the complaint in real time.
3. The issue category is identified by AI.
4. A relevant government department is suggested.
5. A unique complaint tracking ID is generated.
6. Complaint details and audit history are stored in SQLite database.
7. Administrators manage complaint status and post remarks.
8. Citizens track complaint progress in real time.

---

## 🌍 Expected Impact

CiviNexa AI aims to make civic issue reporting more accessible, organized, and transparent by connecting citizens with relevant public service departments through an intelligent digital platform.
