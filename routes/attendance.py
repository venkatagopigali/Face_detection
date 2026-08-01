from flask import Blueprint, render_template, Response, request, send_file, current_app
from flask_login import login_required
from models.attendance import Attendance
from models.employee import Employee
from camera.stream import CameraStream
import pandas as pd
from config import Config
import os
import datetime

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

# Global camera object
camera = None

@attendance_bp.route('/live')
@login_required
def live():
    return render_template('attendance/live.html')

def gen_frames(app):
    global camera
    if camera is None:
        camera = CameraStream()
    yield from camera.get_frame(app)

@attendance_bp.route('/video_feed')
@login_required
def video_feed():
    app = current_app._get_current_object()
    return Response(gen_frames(app),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@attendance_bp.route('/stop_camera')
@login_required
def stop_camera():
    global camera
    if camera is not None:
        del camera
        camera = None
    return "OK"

@attendance_bp.route('/records')
@login_required
def records():
    date_filter = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    search_query = request.args.get('search', '')
    
    query = Attendance.query.join(Employee)
    
    if date_filter:
        query = query.filter(Attendance.attendance_date == date_filter)
        
    if search_query:
        query = query.filter((Employee.name.ilike(f'%{search_query}%')) | (Employee.employee_id.ilike(f'%{search_query}%')))
        
    records = query.all()
    return render_template('attendance/records.html', records=records, date_filter=date_filter, search_query=search_query)

@attendance_bp.route('/export')
@login_required
def export():
    fmt = request.args.get('format', 'csv')
    date_filter = request.args.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    
    query = Attendance.query.join(Employee)
    if date_filter:
        query = query.filter(Attendance.attendance_date == date_filter)
        
    records = query.all()
    
    data = []
    for r in records:
        data.append({
            'Employee ID': r.employee.employee_id,
            'Name': r.employee.name,
            'Department': r.employee.department,
            'Date': r.attendance_date,
            'Login Time': r.login_time,
            'Logout Time': r.logout_time,
            'Working Hours': r.working_hours,
            'Status': r.status
        })
        
    df = pd.DataFrame(data)
    
    if fmt == 'csv':
        filename = f"attendance_{date_filter}.csv"
        filepath = os.path.join(Config.REPORTS_DIR, filename)
        df.to_csv(filepath, index=False)
    else:
        filename = f"attendance_{date_filter}.xlsx"
        filepath = os.path.join(Config.REPORTS_DIR, filename)
        df.to_excel(filepath, index=False)
        
    return send_file(filepath, as_attachment=True)
