from flask import Flask
from config import Config
from models import db
from flask_login import LoginManager

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.admin import Admin
        return Admin.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.employee import employee_bp
    from routes.attendance import attendance_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(attendance_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        from models.admin import Admin
        from werkzeug.security import generate_password_hash
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', password_hash=generate_password_hash('admin'))
            db.session.add(admin)
            db.session.commit()
            print("Default admin created (admin/admin).")

    app.run(debug=True, port=5000)
