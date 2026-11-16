import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_NAME = os.environ.get('DB_NAME', 'si_penakerla')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    # Sesi MySQL dipaksa WIB agar NOW()/timestamp konsisten dengan app.utils.waktu
    DB_TIMEZONE = '+07:00'
    # Di luar folder static agar CV (data pribadi) tidak bisa diakses publik lewat URL.
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

    # Feed RSS/Atom yang sudah diperiksa dan disetujui pengelola.
    JOB_FEED_URLS = [u.strip() for u in os.environ.get('JOB_FEED_URLS', '').split(';') if u.strip()]

    # Kunci AI opsional. Tanpa konfigurasi ini, Asisten Karier memakai FAQ lokal.
    AI_API_URL = os.environ.get('AI_API_URL', 'https://api.openai.com/v1/chat/completions')
    AI_API_KEY = os.environ.get('AI_API_KEY', '')
    AI_MODEL = os.environ.get('AI_MODEL', 'gpt-4o-mini')
