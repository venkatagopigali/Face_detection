from models import db
from datetime import datetime
import json

class Employee(db.Model):
    __tablename__ = 'employee'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    joining_date = db.Column(db.Date, nullable=False)
    face_encoding = db.Column(db.Text, nullable=True) # JSON stored array
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    attendance_records = db.relationship('Attendance', backref='employee', lazy=True)

    def set_encoding(self, encoding_array):
        # Store numpy array as JSON string
        if encoding_array is not None:
            self.face_encoding = json.dumps(encoding_array.tolist())
        
    def get_encoding(self):
        import numpy as np
        if self.face_encoding:
            return np.array(json.loads(self.face_encoding))
        return None
