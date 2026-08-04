import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    """Primary config — uses Supabase PostgreSQL from .env"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-this'

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 5,   # fail fast — 5s max wait
        }
    }

    # Directories
    DATASET_DIR = os.path.join(BASE_DIR, 'datasets')
    ENCODINGS_DIR = os.path.join(BASE_DIR, 'encodings')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

    for d in [DATASET_DIR, ENCODINGS_DIR, REPORTS_DIR]:
        os.makedirs(d, exist_ok=True)


class FallbackConfig(Config):
    """Fallback config — uses local SQLite when Supabase is unavailable"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')

    # SQLite doesn't need pool settings or connect_timeout
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
