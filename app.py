import pymysql
pymysql.install_as_MySQLdb()
from flask import Flask, send_from_directory
from config import Config
from models import db
from flask_login import LoginManager
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Vulnerable static file serving (path traversal)
    @app.route('/static/<path:filename>')
    def vulnerable_static(filename):
        # VULNERABLE: Allows ../../../etc/passwd
        return send_from_directory('static', filename)

    with app.app_context():
        db.create_all()
        # Create demonstration accounts
        create_demo_data()

    return app

def create_demo_data():
    from models import User, SupportTicket, FakeCredential, SystemLog
    
    # Create regular support user
    user = User.query.filter_by(email='customer@example.com').first()
    if not user:
        user = User(
            full_name='Regular Customer',
            email='customer@example.com',
            account_number='CUST123456',
            is_admin=False
        )
        user.set_password('Customer123!')
        db.session.add(user)
    
    # Create fake "admin" account that attackers can compromise
    admin = User.query.filter_by(email='admin@support.bankapp.com').first()
    if not admin:
        admin = User(
            full_name='Support Administrator',
            email='admin@support.bankapp.com',
            account_number='ADMIN999999',
            is_admin=True
        )
        admin.set_password('Welcome2024!')  # Weak password on purpose
        db.session.add(admin)
    
    db.session.commit()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, host='0.0.0.0', port=5000)