import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Directories needed by the app
for _d in ['datasets', 'encodings', 'reports', 'uploads']:
    os.makedirs(os.path.join(BASE_DIR, _d), exist_ok=True)

DATASET_DIR   = os.path.join(BASE_DIR, 'datasets')
ENCODINGS_DIR = os.path.join(BASE_DIR, 'encodings')
REPORTS_DIR   = os.path.join(BASE_DIR, 'reports')
