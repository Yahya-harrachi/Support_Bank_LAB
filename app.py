import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask
from config import Config
from models import db
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()
        create_demo_data()

    return app

def create_demo_data():
    from models import FakeCredential
    
    # Create fake credentials that attackers will find
    fake_creds = [
        ('admin@bankapp.com', 'Admin2024!', 'Production Admin Account'),
        ('root@bankapp.com', 'RootPass123', 'Database Root User'),
        ('api.gateway', 'ApiKey_secret_2024!', 'API Gateway Service Account'),
        ('deploy@bankapp.com', 'DeployKey2024!', 'Deployment Service'),
    ]
    
    for username, password, desc in fake_creds:
        if not FakeCredential.query.filter_by(username=username).first():
            cred = FakeCredential(username=username, password=password, description=desc)
            db.session.add(cred)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=80)