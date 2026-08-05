import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Detect if running on Vercel or read-only environment
IS_VERCEL = os.environ.get('VERCEL') == '1' or not os.access(BASE_DIR, os.W_OK)

if IS_VERCEL:
    BASE_STORAGE = '/tmp'
else:
    BASE_STORAGE = BASE_DIR

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-key-change-this'
    DATASET_DIR = os.path.join(BASE_STORAGE, 'datasets')
    ENCODINGS_DIR = os.path.join(BASE_STORAGE, 'encodings')
    REPORTS_DIR = os.path.join(BASE_STORAGE, 'reports')

# Safely attempt to create directories
for d in [Config.DATASET_DIR, Config.ENCODINGS_DIR, Config.REPORTS_DIR]:
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
