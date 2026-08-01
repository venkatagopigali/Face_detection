import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-this'
    
    # Supabase uses PostgreSQL. Your URL will look like:
    # postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'attendance.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Directories
    DATASET_DIR = os.path.join(BASE_DIR, 'datasets')
    ENCODINGS_DIR = os.path.join(BASE_DIR, 'encodings')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    
    # Create them if they don't exist
    for d in [DATASET_DIR, ENCODINGS_DIR, REPORTS_DIR]:
        os.makedirs(d, exist_ok=True)
