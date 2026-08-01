import cv2
import datetime
from face_engine.engine import recognize_face
from models import db
from models.employee import Employee
from models.attendance import Attendance


class CameraStream:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_employee_ids = []

    def __del__(self):
        if self.video.isOpened():
            self.video.release()

    def _load_known_faces(self, app):
        """Load all employee face encodings from the database."""
        with app.app_context():
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_employee_ids = []
            employees = Employee.query.all()
            for emp in employees:
                encoding = emp.get_encoding()
                if encoding is not None:
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(emp.name)
                    self.known_employee_ids.append(emp.employee_id)

    def get_frame(self, app):
        # Load known faces once when streaming starts
        if not self.known_face_encodings:
            self._load_known_faces(app)

        while True:
            success, frame = self.video.read()
            if not success:
                break

            # Detect and recognize faces in the current frame
            face_locations, face_names, confidences = recognize_face(
                frame, self.known_face_encodings, self.known_face_names
            )

            for (top, right, bottom, left), name, conf in zip(face_locations, face_names, confidences):
                # Draw a box around the face
                color = (0, 255, 0) if name != "Unknown Person" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Draw a filled label bar below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                label = f"{name} ({conf}%)" if name != "Unknown Person" else name
                cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

                # Log attendance for recognized employees
                if name != "Unknown Person":
                    try:
                        idx = self.known_face_names.index(name)
                        emp_id = self.known_employee_ids[idx]
                        with app.app_context():
                            self.mark_attendance(emp_id)
                    except Exception as e:
                        print(f"Attendance marking error: {e}")

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    def mark_attendance(self, emp_id):
        """Mark login or update logout for the given employee ID."""
        now = datetime.datetime.now()
        today = now.date()
        current_time = now.time()

        try:
            record = Attendance.query.filter_by(
                employee_id=emp_id, attendance_date=today
            ).first()

            if not record:
                # First scan of the day → Login
                new_record = Attendance(
                    employee_id=emp_id,
                    attendance_date=today,
                    login_time=current_time,
                    status='Present'
                )
                db.session.add(new_record)
                db.session.commit()
                print(f"[LOGIN]  {emp_id} at {current_time}")

            else:
                # Subsequent scan → only update logout if ≥ 1 minute after login
                login_dt = datetime.datetime.combine(today, record.login_time)
                elapsed = (now - login_dt).total_seconds()

                if record.logout_time is None and elapsed > 60:
                    record.logout_time = current_time
                    logout_dt = datetime.datetime.combine(today, current_time)
                    record.working_hours = round((logout_dt - login_dt).total_seconds() / 3600, 2)
                    db.session.commit()
                    print(f"[LOGOUT] {emp_id} at {current_time} | Hours: {record.working_hours}")

        except Exception as e:
            db.session.rollback()
            print(f"Database error for {emp_id}: {e}")
