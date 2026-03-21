"""
CalibPro — Configuration
"""
import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # ── Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'calibpro-dev-secret-2026-change-in-prod')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ── Database
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'calibpro.db')

    # ── Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'photos')
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024   # 20 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ── Email (SMTP — configure with real credentials)
    MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT     =587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = 'e.loayzaz.07@gmail.com'  
    MAIL_PASSWORD = 'abtj bsor zdtx fsvq'
    MAIL_DEFAULT_SENDER = 'e.loayzaz.07@gmail.com'

    # ── App settings
    CERT_DAYS_ALERT = 30          # alert before expiration
    ITEMS_PER_PAGE  = 20

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
