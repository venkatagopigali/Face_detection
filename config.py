import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-this'

    # Supabase PostgreSQL connection string loaded from .env file
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool settings for reliability:
    # - pool_pre_ping: test connection before using it (detects stale connections)
    # - pool_recycle: recycle connections every 5 minutes
    # - connect_args: set a 10-second connection timeout
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {
            'connect_timeout': 10,
        }
    }

    # Directories
    DATASET_DIR = os.path.join(BASE_DIR, 'datasets')
    ENCODINGS_DIR = os.path.join(BASE_DIR, 'encodings')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

    # Create them if they don't exist
    for d in [DATASET_DIR, ENCODINGS_DIR, REPORTS_DIR]:
        os.makedirs(d, exist_ok=True)
