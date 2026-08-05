import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-this'
    DATASET_DIR = os.path.join(BASE_DIR, 'datasets')
    ENCODINGS_DIR = os.path.join(BASE_DIR, 'encodings')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')

# Create directories if they don't exist
for d in [Config.DATASET_DIR, Config.ENCODINGS_DIR, Config.REPORTS_DIR, os.path.join(BASE_DIR, 'uploads')]:
    os.makedirs(d, exist_ok=True)
