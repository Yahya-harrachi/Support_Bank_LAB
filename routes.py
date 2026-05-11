from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file, abort, Response
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, SupportTicket, SystemLog, FakeCredential, AuditLog
from forms import LoginForm, TicketForm, ContactForm
from datetime import datetime
import subprocess
import os
import re

main = Blueprint('main', __name__)

# ============ LOGGING ============
def log_attack(endpoint, details=None):
    log = SystemLog(
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        endpoint=endpoint,
        query_params=str(details or request.args.to_dict())
    )
    db.session.add(log)
    db.session.commit()
    print(f"[!] HONEYPOT: {request.remote_addr} -> {endpoint}")

# ============ PUBLIC PAGES (No Login Required) ============

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/knowledge-base')
def knowledge_base():
    return render_template('knowledge_base.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # Create ticket without login - VULNERABLE to spam
        ticket = SupportTicket(
            user_id=None,  # Anonymous ticket
            guest_email=form.email.data,
            subject=form.subject.data,
            message=form.message.data,
            is_anonymous=True
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Your message has been sent. Our support team will contact you.', 'success')
        return redirect(url_for('main.index'))
    return render_template('contact.html', form=form)

# ============ RECONNAISSANCE FILES (HONEYPOT BAIT) ============

@main.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Disallow: /admin
Disallow: /backup
Disallow: /.env
Disallow: /api/internal
Disallow: /phpinfo.php
Disallow: /git/
Sitemap: https://support.bankapp.com/sitemap.xml
"""
    return Response(content, mimetype='text/plain')

@main.route('/sitemap.xml')
def sitemap():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://support.bankapp.com/</loc></url>
  <url><loc>https://support.bankapp.com/faq</loc></url>
  <url><loc>https://support.bankapp.com/knowledge-base</loc></url>
  <url><loc>https://support.bankapp.com/api/docs</loc></url>
  <url><loc>https://support.bankapp.com/backup/</loc></url>
  <url><loc>https://support.bankapp.com/admin</loc></url>
</urlset>
"""
    return Response(content, mimetype='application/xml')

@main.route('/.env')
def dotenv_leak():
    """HONEYPOT: Leaks fake environment variables"""
    log_attack('/.env')
    content = """# Bank Production Environment - DO NOT COMMIT
DATABASE_URL=mysql://prod_admin:SuperSecure2024!@internal-db.bankapp.internal:3306/production
REDIS_URL=redis://cache.internal:6379/0
JWT_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.prod_secret_key_2024
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
INTERNAL_API=http://192.168.100.50:8080
SSH_HOST=192.168.100.50
SSH_USER=deploy
"""
    return Response(content, mimetype='text/plain')

@main.route('/phpinfo.php')
def phpinfo_leak():
    """HONEYPOT: Fake PHP info page"""
    log_attack('/phpinfo.php')
    content = """<h1>PHP Version 7.4.33</h1>
<h2>Disabled Functions</h2>
<pre>exec, shell_exec, system, passthru, popen</pre>
<h2>Open Basedir</h2>
<pre>/var/www/html:/tmp</pre>
<h2>Allow URL Fopen</h2>
<pre>On</pre>
<h2>Database Credentials</h2>
<pre>define('DB_USER', 'prod_user');
define('DB_PASS', 'ProdPass2024!');</pre>
<h2>Application Environment</h2>
<pre>APP_ENV=production
APP_DEBUG=false</pre>
"""
    return Response(content, mimetype='text/html')

@main.route('/.git/HEAD')
def git_head():
    log_attack('/.git/HEAD')
    return Response("ref: refs/heads/main", mimetype='text/plain')

@main.route('/.git/config')
def git_config():
    log_attack('/.git/config')
    content = """[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
[remote "origin"]
	url = git@internal-git.bankapp.internal:bankapp/production.git
	fetch = +refs/*:refs/*
[user]
	name = Deployment Bot
	email = deploy@bankapp.com
[credential]
	helper = store --file ~/.git-credentials
"""
    return Response(content, mimetype='text/plain')

# ============ DIRECTORY LISTING (HONEYPOT) ============

@main.route('/backup/')
def backup_directory():
    log_attack('/backup/')
    content = """<!DOCTYPE html>
<html>
<head><title>Index of /backup/</title></head>
<body>
<h1>Index of /backup/</h1>
<pre>
<a href="database_backup_2024_12_01.sql">database_backup_2024_12_01.sql</a>      15-Dec-2024 23:45   24M
<a href="user_export.csv">user_export.csv</a>                     15-Dec-2024 23:40  1.2M
<a href="id_rsa">id_rsa</a>                              15-Dec-2024 23:35  1.8K
<a href="id_rsa.pub">id_rsa.pub</a>                          15-Dec-2024 23:35   398
<a href=".htpasswd">.htpasswd</a>                           15-Dec-2024 23:30   120
</pre>
</body>
</html>"""
    return Response(content, mimetype='text/html')

@main.route('/backup/id_rsa')
def ssh_key_leak():
    """HONEYPOT: Fake SSH private key"""
    log_attack('/backup/id_rsa')
    ssh_key = """-----BEGIN OPENSSH PRIVATE KEY-----
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
bmUgbm9uZQ==
-----END OPENSSH PRIVATE KEY-----"""
    return Response(ssh_key, mimetype='text/plain', headers={'Content-Disposition': 'attachment; filename="id_rsa"'})

@main.route('/backup/.htpasswd')
def htpasswd_leak():
    log_attack('/backup/.htpasswd')
    content = """admin:$2y$10$N9qo8uLOickgx2ZMRZoMy.Mr/.8lqF5FjYqVvKQFkqRqZm2fGg1YG
support:$2y$10$X8bHuhc.eQqK5.yFG3xUI.FMZJwjJXiKqKqJxYyXrRqLpM9nVwO2k
deploy:$2y$10$A1bC2dE3fG4hI5jK6lM7nO8pQ9rS0tU1vW2xY3zA4bC5dE6fG7hI8jK"""
    return Response(content, mimetype='text/plain')

# ============ VULNERABLE FEATURES ============

@main.route('/api/status')
def api_status():
    """Shows fake internal server status"""
    return {
        'status': 'healthy',
        'database': 'connected',
        'redis': 'connected',
        'internal_ip': '192.168.100.50',
        'version': '3.2.1-prod'
    }

@main.route('/search-tickets')
def search_tickets():
    """VULNERABLE: SQL Injection in search"""
    query = request.args.get('q', '')
    
    # Log the search attempt
    log_attack('/search-tickets', {'query': query})
    
    # INTENTIONAL SQL INJECTION VULNERABILITY
    # This is concatenated directly - attackers can use ' OR '1'='1
    from models import db
    from sqlalchemy import text
    
    try:
        # VULNERABLE CODE - DO NOT USE IN PRODUCTION
        sql = text(f"SELECT * FROM support_ticket WHERE subject LIKE '%{query}%' OR message LIKE '%{query}%'")
        result = db.session.execute(sql)
        tickets = result.fetchall()
        
        # Also return fake admin results to entice attackers
        fake_results = [
            {'subject': 'Admin Password Reset Request', 'message': 'Need to reset admin password for john.doe@bankapp.com'},
            {'subject': 'Database Connection Issue', 'message': 'Cannot connect to prod-db.internal:3306 with user root'},
            {'subject': 'API Key Rotation', 'message': 'New API key: sk_prod_4k3j2h1g0f9d8s7a6'},
        ]
        
        return render_template('search_results.html', query=query, tickets=list(result), fake_results=fake_results)
    except Exception as e:
        # Error message leaks database structure
        return f"Database Error: {str(e)}", 500

@main.route('/download')
def file_download():
    """VULNERABLE: Path Traversal (LFI)"""
    filename = request.args.get('file', '')
    log_attack('/download', {'file': filename})
    
    # INTENTIONAL PATH TRAVERSAL VULNERABILITY
    # Attackers can use ../../../etc/passwd
    import os
    
    # Vulnerable path join
    filepath = os.path.join('/var/www/support_bankapp/uploads', filename)
    
    # Check for path traversal
    if '../' in filename:
        # Allow reading sensitive files (honeypot)
        if 'passwd' in filename:
            content = """root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
mysql:x:100:101:MySQL Server,,,:/nonexistent:/bin/false
deploy:x:1000:1000:Deployment User,,,:/home/deploy:/bin/bash
prod_user:x:1001:1001:Production User,,,:/home/prod_user:/bin/bash"""
            return Response(content, mimetype='text/plain')
        elif 'shadow' in filename:
            content = """root:$6$randomhash$verylonghash:19000:0:99999:7:::
deploy:$6$deployhash$deployhashvalue:19000:0:99999:7:::"""
            return Response(content, mimetype='text/plain')
        elif 'id_rsa' in filename:
            return redirect(url_for('main.ssh_key_leak'))
    
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        return f"File not found: {filename}", 404

@main.route('/admin/ping')
def ping_tool():
    """VULNERABLE: Command Injection"""
    ip = request.args.get('ip', '')
    log_attack('/admin/ping', {'ip': ip})
    
    # INTENTIONAL COMMAND INJECTION VULNERABILITY
    import subprocess
    
    # Vulnerable command execution
    # Attackers can use: 127.0.0.1; whoami; id; ls -la
    try:
        result = subprocess.check_output(f"ping -c 1 {ip}", shell=True, stderr=subprocess.STDOUT, timeout=5)
        return f"<pre>{result.decode()}</pre>"
    except subprocess.TimeoutExpired:
        return "Ping timeout"
    except Exception as e:
        return f"Error: {str(e)}"

# ============ LEGITIMATE FEATURES ============

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)

@main.route('/register')
def register():
    flash('Self-registration is temporarily disabled. Please contact support.', 'warning')
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(SupportTicket.created_at.desc()).all()
    return render_template('dashboard.html', tickets=tickets)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('main.index'))