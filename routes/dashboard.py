from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required
from models.employee import Employee
from models.attendance import Attendance
import datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    try:
        today = datetime.date.today()

        total_employees = Employee.query.count()

        today_attendance = Attendance.query.filter_by(attendance_date=today).all()
        present_today = len(today_attendance)
        absent_today = max(total_employees - present_today, 0)

        # Late arrival = login after 09:30 AM
        late_time = datetime.time(9, 30)
        late_arrivals = sum(1 for a in today_attendance if a.login_time > late_time)

        total_records = Attendance.query.count()

        return render_template('dashboard.html',
                               total_employees=total_employees,
                               present_today=present_today,
                               absent_today=absent_today,
                               late_arrivals=late_arrivals,
                               total_records=total_records)

    except Exception as e:
        flash(f'Database error: {str(e)}. Please check your connection.', 'danger')
        return render_template('dashboard.html',
                               total_employees=0,
                               present_today=0,
                               absent_today=0,
                               late_arrivals=0,
                               total_records=0)
