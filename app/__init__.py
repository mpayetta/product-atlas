import os
from dotenv import load_dotenv

# Load config/settings.env when the app package is imported
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, "config", "settings.env")

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
