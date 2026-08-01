from models import db

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), db.ForeignKey('employee.employee_id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    login_time = db.Column(db.Time, nullable=False)
    logout_time = db.Column(db.Time, nullable=True)
    working_hours = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Present')
