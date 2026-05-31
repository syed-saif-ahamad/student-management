# Student Management & Performance Analysis System

Django + MySQL application for managing students, attendance, marks, analytics, and ML-based performance prediction.

## Features

- Faculty & Student login with role-based access
- Student CRUD with search
- Attendance management with percentage calculation
- Marks management (subject-wise, exam-wise)
- Analytics dashboard with Chart.js (bar, pie, line charts)
- ML prediction using Linear Regression (scikit-learn)
- Downloadable student performance report

## Quick Start

### 1. Activate virtual environment

```bash
venv\Scripts\activate
```

### 2. Configure database

**MySQL (recommended):**

Create the database in MySQL Workbench:

```sql
CREATE DATABASE student_management_db;
```

Set environment variables (or edit `sms_project/settings.py`):

```bash
set DB_NAME=student_management_db
set DB_USER=root
set DB_PASSWORD=your_password
```

**SQLite (for quick local testing):**

```bash
set USE_SQLITE=True
```

### 3. Run migrations and setup demo data

```bash
python manage.py migrate
python manage.py setup_demo
```

### 4. Start the server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/

## Demo Credentials

| Role    | Username | Password    |
|---------|----------|-------------|
| Faculty | faculty  | faculty123  |
| Student | cs001    | student123  |

## Project Structure

```
sms_project/          # Django project settings
accounts/             # Authentication & roles
students/             # Student CRUD
attendance/           # Attendance management
marks/                # Marks management
analytics_dashboard/  # Dashboard, analytics, ML
templates/            # Base templates
static/               # CSS, JS, images
```

## Tech Stack

- Python, Django
- MySQL
- HTML, CSS, Bootstrap 5
- Chart.js
- Pandas, scikit-learn
