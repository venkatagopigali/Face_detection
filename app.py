from flask import Flask, render_template
from config import Config, FallbackConfig
from models import db
from flask_login import LoginManager
import time
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.admin import Admin
        return Admin.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.employee import employee_bp
    from routes.attendance import attendance_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(attendance_bp)

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('error.html', error=str(e)), 500

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error="Page not found."), 404

    return app


def try_connect(app):
    """Try to connect and initialize the DB. Returns True on success."""
    try:
        with app.app_context():
            db.create_all()
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
        logger.warning(f"⚠️  Connection failed: {e}")
        return False


def init_db_with_fallback(retries=2, delay=2):
    """
    Try Supabase first. If it fails after retries, fall back to local SQLite.
    Returns the Flask app configured with whichever DB worked.
    """
    supabase_url = os.environ.get('DATABASE_URL', '')

    # --- Try Supabase ---
    if supabase_url and 'sqlite' not in supabase_url:
        logger.info("🔄 Trying to connect to Supabase...")
        app = create_app(Config)
        for attempt in range(1, retries + 1):
            logger.info(f"   Attempt {attempt}/{retries}...")
            if try_connect(app):
                logger.info("✅ Connected to Supabase successfully!")
                return app
            if attempt < retries:
                time.sleep(delay)

        logger.warning("⚠️  Supabase unreachable. Your project may be paused.")
        logger.info("   Visit https://supabase.com/dashboard to unpause it.")
        logger.info("🔄 Falling back to local SQLite database...")

    # --- Fall back to SQLite ---
    app = create_app(FallbackConfig)
    if try_connect(app):
        logger.info("✅ Running with local SQLite database (attendance.db).")
        logger.warning("⚠️  Data will be stored LOCALLY — not in Supabase until it's back online.")
    return app


if __name__ == '__main__':
    app = init_db_with_fallback()
    logger.info("🚀 Server starting at http://127.0.0.1:5000")
    app.run(debug=False, host='0.0.0.0', port=5000)
