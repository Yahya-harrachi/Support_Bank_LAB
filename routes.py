
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, send_file, abort
from models import db, SupportTicket, SystemLog
from forms import TicketForm
from datetime import datetime
import subprocess
import os
import json

main = Blueprint('main', __name__)

# Data directory - looks like normal app data
DATA_DIR = '/var/www/Support_Bank_LAB/data'

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

def serve_file(relative_path, content_type='text/plain', as_attachment=False):
    """Serve files from data directory"""
    full_path = os.path.join(DATA_DIR, relative_path)
    
    if os.path.exists(full_path):
        log_attack(request.path)
        if as_attachment:
            return send_file(full_path, as_attachment=True)
        with open(full_path, 'r') as f:
            return Response(f.read(), mimetype=content_type)
    return Response("", status=404)

# ============ PUBLIC PAGES ============
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/faq')
def faq():
    return render_template('faq.html')

@main.route('/knowledge-base')
def knowledge_base():
    return render_template('knowledge_base.html')

@main.route('/submit-ticket', methods=['GET', 'POST'])
def submit_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        ticket = SupportTicket(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Your ticket has been submitted. We will contact you soon.', 'success')
        return redirect(url_for('main.index'))
    return render_template('submit_ticket.html', form=form)

# ============ RECONNAISSANCE FILES ============
@main.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Disallow: /admin
Disallow: /backup
Disallow: /config
Disallow: /cache
Disallow: /system
Disallow: /temp/.git
Disallow: /public/info
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
  <url><loc>https://support.bankapp.com/submit-ticket</loc></url>
  <url><loc>https://support.bankapp.com/cache/</loc></url>
  <url><loc>https://support.bankapp.com/config/</loc></url>
</urlset>
"""
    return Response(content, mimetype='application/xml')

# ============ REALISTIC FILE LEAKS ============
@main.route('/config/.env')
def env_config():
    return serve_file('config/.env', 'text/plain')

@main.route('/public/info/debug')
def debug_info():
    import json
    debug_file = os.path.join(DATA_DIR, 'public/info/debug.py')
    if os.path.exists(debug_file):
        # Simulate python debug output
        debug_data = {
            "python_version": "3.10.12",
            "platform": "Linux-5.15.0-91-generic-x86_64-with-glibc2.35",
            "environment": "production",
            "debug_mode": "False",
            "database": {
                "host": "internal-db.bankapp.internal",
                "name": "production",
                "user": "prod_admin",
                "password": "SuperSecure2024!"
            },
            "paths": {
                "app_root": "/var/www/app",
                "config": "/var/www/app/data/config",
                "logs": "/var/www/logs"
            },
            "server": {
                "internal_ip": "192.168.100.50",
                "hostname": "prod-app-01"
            }
        }
        return Response(json.dumps(debug_data, indent=2), mimetype='application/json')
    return Response("Debug info unavailable", status=404)

@main.route('/temp/.git/HEAD')
def git_head():
    return serve_file('temp/.git/HEAD', 'text/plain')

@main.route('/temp/.git/config')
def git_config():
    return serve_file('temp/.git/config', 'text/plain')

# ============ DIRECTORY LISTING (Enticing) ============
@main.route('/cache/')
def cache_dir():
    log_attack('/cache/')
    content = """<!DOCTYPE html>
<html>
<head><title>Index of /cache/</title></head>
<body>
<h1>Index of /cache/</h1>
<pre>
<a href="db_dump.sql">db_dump.sql</a>                          15-Dec-2024 23:45   24M
<a href="ssh_keys/">ssh_keys/</a>                            15-Dec-2024 23:35    -
</pre>
</body>
</html>"""
    return Response(content, mimetype='text/html')

@main.route('/cache/ssh_keys/')
def ssh_keys_dir():
    log_attack('/cache/ssh_keys/')
    content = """<!DOCTYPE html>
<html>
<head><title>Index of /cache/ssh_keys/</title></head>
<body>
<h1>Index of /cache/ssh_keys/</h1>
<pre>
<a href="deploy_key">deploy_key</a>                           15-Dec-2024 23:35  1.8K
<a href="deploy_key.pub">deploy_key.pub</a>                       15-Dec-2024 23:35   398
</pre>
</body>
</html>"""
    return Response(content, mimetype='text/html')

@main.route('/config/')
def config_dir():
    log_attack('/config/')
    content = """<!DOCTYPE html>
<html>
<head><title>Index of /config/</title></head>
<body>
<h1>Index of /config/</h1>
<pre>
<a href=".env">.env</a>                                 15-Dec-2024 23:30  1.2K
<a href=".htpasswd">.htpasswd</a>                            15-Dec-2024 23:30   340
</pre>
</body>
</html>"""
    return Response(content, mimetype='text/html')

# ============ FILE DOWNLOADS ============
@main.route('/cache/db_dump.sql')
def db_dump():
    return serve_file('cache/db_dump.sql', 'application/sql', as_attachment=True)

@main.route('/cache/ssh_keys/deploy_key')
def ssh_key():
    return serve_file('cache/ssh_keys/deploy_key', 'text/plain', as_attachment=True)

@main.route('/config/.htpasswd')
def htpasswd():
    return serve_file('config/.htpasswd', 'text/plain')

# ============ API ENDPOINTS ============
@main.route('/system/status')
def system_status():
    log_attack('/system/status')
    status_file = os.path.join(DATA_DIR, 'system/status.json')
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return json.load(f)
    return {'status': 'degraded'}

# ============ VULNERABLE FEATURES ============
@main.route('/search')
def search_tickets():
    """VULNERABLE: SQL Injection"""
    query = request.args.get('q', '')
    log_attack('/search', {'query': query})
    
    from sqlalchemy import text
    
    try:
        sql = text(f"SELECT * FROM support_ticket WHERE subject LIKE '%{query}%' OR message LIKE '%{query}%'")
        result = db.session.execute(sql)
        tickets = result.fetchall()
        
        fake_results = [
            {'subject': 'Admin Password Reset Request', 'message': 'Need to reset admin password for john.doe@bankapp.com'},
            {'subject': 'Database Connection Issue', 'message': 'Cannot connect to prod-db.internal:3306 with user root'},
            {'subject': 'API Key Rotation', 'message': 'New API key: sk_prod_4k3j2h1g0f9d8s7a6'},
            {'subject': 'SSH Key Expiring', 'message': 'Deployment key in /cache/ssh_keys/ needs renewal'},
        ]
        
        return render_template('search_results.html', query=query, tickets=list(tickets), fake_results=fake_results)
    except Exception as e:
        return f"Database Error: {str(e)}", 500

@main.route('/download')
def file_download():
    """VULNERABLE: Path Traversal (LFI)"""
    filename = request.args.get('file', '')
    log_attack('/download', {'file': filename})
    
    if '../' in filename:
        if 'passwd' in filename:
            return serve_file('system/passwd', 'text/plain')
        elif '.env' in filename:
            return serve_file('config/.env', 'text/plain')
        elif 'id_rsa' in filename or 'deploy_key' in filename:
            return serve_file('cache/ssh_keys/deploy_key', 'text/plain', as_attachment=True)
        elif '.htpasswd' in filename:
            return serve_file('config/.htpasswd', 'text/plain')
    
    return f"File not found: {filename}", 404

@main.route('/tools/ping')
def ping_tool():
    """VULNERABLE: Command Injection"""
    ip = request.args.get('ip', '')
    log_attack('/tools/ping', {'ip': ip})
    
    try:
        result = subprocess.check_output(f"ping -c 1 {ip}", shell=True, stderr=subprocess.STDOUT, timeout=5)
        return f"<pre>{result.decode()}</pre>"
    except Exception as e:
        return f"Error: {str(e)}"
