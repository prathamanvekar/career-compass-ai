import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'

    # Database
    _BASE_DIR = Path(__file__).resolve().parent
    _DB_DIR = _BASE_DIR / 'database'
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{(_DB_DIR / 'job_portal.db').as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload Settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx'}

    # # Gemini API (Free Tier)
    # GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'your-gemini-api-key'
    # GEMINI_MODEL = 'gemini-2.0-flash'  # Free tier model


    # Groq API (FREE - replaces Gemini)
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY') or 'your-groq-api-key'
    GROQ_MODEL = 'llama-3.1-8b-instant'  # Fast and free model
    # Alternative models: 'llama3-70b-8192', 'mixtral-8x7b-32768', 'gemma2-9b-it'


    # Matching Settings
    TOP_JOBS_COUNT = 3
    MINIMUM_MATCH_SCORE = 0  # Set to 0 to ensure at least some jobs are shown
    ALWAYS_SHOW_MIN_JOBS = 1  # Always show at least this many jobs even if low match

    # Job Sources
    SHOW_ONLY_RECRUITER_JOBS = True  # Only show jobs posted by registered recruiters
