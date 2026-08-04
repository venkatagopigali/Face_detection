import cv2
import datetime
from face_engine.engine import recognize_face
from models import db
from models.employee import Employee
from models.attendance import Attendance

# Global last-event store: {'type': 'LOGIN'/'LOGOUT', 'name': ..., 'emp_id': ..., 'time': ...}
last_event = {}


class CameraStream:
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_employee_ids = []
        # Throttle: track last time attendance was attempted per employee
        self._last_attempt = {}

    def __del__(self):
        if self.video.isOpened():
            self.video.release()

    def _load_known_faces(self, app):
        """Load all employee face encodings from the database."""
        try:
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
                print(f"[INFO] Loaded {len(self.known_face_encodings)} face(s) from database.")
        except Exception as e:
            print(f"[ERROR] Failed to load faces: {e}")

    def get_frame(self, app):
        global last_event
        # Load known faces once when streaming starts
        if not self.known_face_encodings:
            self._load_known_faces(app)

        while True:
            success, frame = self.video.read()
            if not success:
                break

            # Detect and recognize faces in the current frame
            try:
                face_locations, face_names, confidences = recognize_face(
                    frame, self.known_face_encodings, self.known_face_names
                )
            except Exception as e:
                print(f"[ERROR] Face recognition failed: {e}")
                face_locations, face_names, confidences = [], [], []

            now = datetime.datetime.now()

            for (top, right, bottom, left), name, conf in zip(face_locations, face_names, confidences):
                # Draw box around face
                color = (0, 255, 0) if name != "Unknown Person" else (0, 0, 255)
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                # Draw filled label bar below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                label = f"{name} ({conf}%)" if name != "Unknown Person" else name
                cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

                # Throttle: only attempt attendance every 5 seconds per person
                if name != "Unknown Person":
                    last_attempt_time = self._last_attempt.get(name)
                    if last_attempt_time is None or (now - last_attempt_time).total_seconds() > 5:
                        self._last_attempt[name] = now
                        try:
                            idx = self.known_face_names.index(name)
                            emp_id = self.known_employee_ids[idx]
                            with app.app_context():
                                event = self.mark_attendance(emp_id, name)
                                if event:
                                    last_event = event
                        except Exception as e:
                            print(f"[ERROR] Attendance marking error: {e}")

            # Draw last event banner on frame
            if last_event:
                elapsed = (now - last_event.get('timestamp', now)).total_seconds()
                if elapsed < 5:  # show banner for 5 seconds
                    event_type = last_event.get('type', '')
                    event_name = last_event.get('name', '')
                    event_time = last_event.get('time', '')
                    banner_color = (0, 180, 0) if event_type == 'LOGIN' else (0, 120, 220)
                    banner_text = f"{'LOGGED IN' if event_type == 'LOGIN' else 'LOGGED OUT'}: {event_name} at {event_time}"
                    cv2.rectangle(frame, (0, 0), (frame.shape[1], 50), banner_color, cv2.FILLED)
                    cv2.putText(frame, banner_text, (10, 35),
                                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    def mark_attendance(self, emp_id, emp_name):
        """
        Mark login or update logout for the given employee.
        Returns an event dict {'type', 'name', 'emp_id', 'time', 'timestamp'} or None.
        """
        now = datetime.datetime.now()
        today = now.date()
        current_time = now.time()
        current_time_str = now.strftime('%H:%M:%S')

        try:
            record = Attendance.query.filter_by(
                employee_id=emp_id, attendance_date=today
            ).first()

            if not record:
                # First scan of the day → LOGIN
                new_record = Attendance(
                    employee_id=emp_id,
                    attendance_date=today,
                    login_time=current_time,
                    status='Present'
                )
                db.session.add(new_record)
                db.session.commit()
                print(f"[LOGIN]  {emp_name} ({emp_id}) at {current_time_str}")
                return {
                    'type': 'LOGIN',
                    'name': emp_name,
                    'emp_id': emp_id,
                    'time': current_time_str,
                    'timestamp': now
                }

            else:
                # Already logged in — check for logout
                login_dt = datetime.datetime.combine(today, record.login_time)
                elapsed = (now - login_dt).total_seconds()

                if record.logout_time is None and elapsed > 60:
                    record.logout_time = current_time
                    logout_dt = datetime.datetime.combine(today, current_time)
                    record.working_hours = round((logout_dt - login_dt).total_seconds() / 3600, 2)
                    db.session.commit()
                    print(f"[LOGOUT] {emp_name} ({emp_id}) at {current_time_str} | Hours: {record.working_hours}")
                    return {
                        'type': 'LOGOUT',
                        'name': emp_name,
                        'emp_id': emp_id,
                        'time': current_time_str,
                        'timestamp': now
                    }

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] DB error for {emp_id}: {e}")

        return None
