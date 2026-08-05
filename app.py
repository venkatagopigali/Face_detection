from flask import Flask, render_template
from models import db
from flask_login import LoginManager
import time
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)s  %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def create_app(db_uri, engine_options=None):
    """Create and configure the Flask application with the given DB URI."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key-change-this')
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if engine_options:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from models.admin import Admin
        try:
            return Admin.query.get(int(user_id))
        except Exception:
            return None

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
        try:
            db.session.rollback()
        except Exception:
            pass
        return render_template('error.html', error=str(e)), 500

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error='Page not found.'), 404

    return app


def setup_admin(app_instance):
    """Create default admin user if not present."""
    try:
        from models.admin import Admin
        from werkzeug.security import generate_password_hash
        with app_instance.app_context():
            if not Admin.query.filter_by(username='admin').first():
                admin = Admin(
                    username='admin',
                    password_hash=generate_password_hash('admin')
                )
                db.session.add(admin)
                db.session.commit()
                logger.info('Default admin created  →  username: admin  |  password: admin')
    except Exception as e:
        logger.warning(f'Could not create default admin: {e}')


def try_db(app_instance):
    """Try to create all tables. Returns True on success."""
    try:
        with app_instance.app_context():
            db.create_all()
        return True
    except Exception as e:
        logger.warning(f'Connection failed: {e}')
        return False


def get_app():
    """Initialize and return top-level Flask app instance for WSGI / Vercel."""
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

    supabase_url = os.environ.get('DATABASE_URL', '')
    sqlite_uri   = 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'attendance.db')

    app_instance = None

    # ── Try Supabase first ──────────────────────────────────────────────────
    if supabase_url and 'sqlite' not in supabase_url:
        logger.info('Connecting to Supabase...')
        supabase_engine_opts = {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'connect_args': {'connect_timeout': 5},
        }
        for attempt in range(1, 3):
            logger.info(f'  Attempt {attempt}/2')
            app_instance = create_app(supabase_url, supabase_engine_opts)
            if try_db(app_instance):
                logger.info('✅  Connected to Supabase!')
                break
            app_instance = None
            if attempt < 2:
                time.sleep(1)

    # ── Fall back to local SQLite ───────────────────────────────────────────
    if app_instance is None:
        if supabase_url:
            logger.warning('⚠️   Supabase unreachable (project may be paused).')
        logger.info('🔄  Using local SQLite database (attendance.db)')
        app_instance = create_app(sqlite_uri, {'pool_pre_ping': True})
        try_db(app_instance)

    # ── Ensure admin user exists ────────────────────────────────────────────
    setup_admin(app_instance)
    return app_instance


# Top-level Flask instance required by Vercel & WSGI servers
app = get_app()

if __name__ == '__main__':
    logger.info('🚀  Server ready  →  http://127.0.0.1:5000')
    app.run(debug=False, host='0.0.0.0', port=5000)
