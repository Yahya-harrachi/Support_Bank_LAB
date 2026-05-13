
# Flask Debug Endpoint - Remove in production
import os
import sys
import platform
import pymysql

def get_debug_info():
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'environment': os.environ.get('APP_ENV', 'production'),
        'debug_mode': os.environ.get('FLASK_DEBUG', 'False'),
        'database': {
            'host': 'internal-db.bankapp.internal',
            'name': 'production',
            'user': 'prod_admin',
            'password': 'SuperSecure2024!'
        },
        'paths': {
            'app_root': '/var/www/app',
            'config': '/var/www/app/data/config',
            'logs': '/var/www/logs'
        },
        'disabled_functions': ['exec', 'shell_exec', 'system', 'passthru', 'popen'],
        'server': {
            'internal_ip': '192.168.100.50',
            'hostname': 'prod-app-01',
            'cluster': 'bank-prod-cluster'
        }
    }

# This file intentionally left with detailed debug info
# TODO: Remove before production deployment
