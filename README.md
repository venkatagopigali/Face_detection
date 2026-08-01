# Face Recognition Attendance Management System

## Overview
A production-ready Face Recognition Attendance Management System using Python, Flask, OpenCV, and the `face_recognition` library.

## Features
- **Admin Dashboard**: View statistics (Present today, Absent, Late Arrivals).
- **Employee Management**: CRUD operations for employees.
- **Face Registration**: Capture images directly from the webcam via browser and generate face encodings.
- **Live Attendance**: Detect faces via webcam, identify registered employees, and log login/logout times automatically.
- **Reports**: Filter attendance by date, search by name/ID, and export to CSV or Excel.

## Setup Instructions

### 1. Requirements
Ensure you have Python 3.9+ installed.
You also need CMake and Visual Studio C++ Build Tools installed on Windows for the `dlib` library (required by `face_recognition`) to compile successfully.

### 2. Installation
```bash
# Create a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
By default, the application uses SQLite for easy local setup.
To use MySQL:
1. Ensure MySQL server is running.
2. Create a database `attendance_db`.
3. Set the `DATABASE_URL` environment variable:
   ```bash
   set DATABASE_URL="mysql+pymysql://username:password@localhost/attendance_db"
   ```

### 4. Running the Application
```bash
python app.py
```
The application will automatically create the database tables and a default admin user on the first run.

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin`

Navigate to `http://localhost:5000` in your web browser.

## Directory Structure
- `app.py`: Main application script.
- `config.py`: Configuration settings.
- `models/`: SQLAlchemy database models.
- `routes/`: Flask blueprints for different modules.
- `camera/`: Webcam streaming and frame processing.
- `face_recognition/`: Face encoding and recognition logic.
- `templates/`: HTML Jinja2 templates.
- `static/`: CSS and JS files.
- `datasets/`, `encodings/`, `reports/`: Storage directories.
