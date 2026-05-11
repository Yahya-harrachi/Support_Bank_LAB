import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'support_honeypot_secret_key_2025'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/support_db'  # Different database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True