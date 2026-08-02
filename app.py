from flask import Flask, render_template
from config import Config
from models import db
from flask_login import LoginManager
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

    # Custom error pages
    @app.errorhandler(500)
    def internal_error(e):
        return render_template('error.html', error=str(e)), 500

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error="Page not found."), 404

    return app


def init_db_with_retry(app, retries=5, delay=3):
    """
    Try to connect to the database and create tables.
    Retries up to `retries` times with `delay` seconds between attempts.
    """
    for attempt in range(1, retries + 1):
        try:
            with app.app_context():
                db.create_all()
                logger.info("✅ Database connected and tables created.")

                # Create default admin if not exists
                from models.admin import Admin
                from werkzeug.security import generate_password_hash
                if not Admin.query.filter_by(username='admin').first():
                    admin = Admin(
                        username='admin',
                        password_hash=generate_password_hash('admin')
                    )
                    db.session.add(admin)
                    db.session.commit()
                    logger.info("✅ Default admin created (admin/admin).")
            return True

        except Exception as e:
            logger.warning(
                f"⚠️  Database connection attempt {attempt}/{retries} failed: {e}"
            )
            if attempt < retries:
                logger.info(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(
                    "❌ Could not connect to the database after multiple attempts.\n"
                    "   Please check your internet connection and Supabase credentials in the .env file.\n"
                    "   The server will still start — reconnect by restarting the app."
                )
    return False


if __name__ == '__main__':
    app = create_app()
    init_db_with_retry(app)
    app.run(debug=False, host='0.0.0.0', port=5000)
