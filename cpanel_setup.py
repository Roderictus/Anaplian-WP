#!/usr/bin/env python3
"""
cPanel Flask Application Setup Script
For Namecheap hosting with cPanel
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path

# CONFIGURATION - MODIFY THESE SETTINGS
APP_NAME = "anaplian"  # Name of your application
PYTHON_VERSION = "3.9"  # Python version to use
REQUIREMENTS = [        # List your dependencies here
    "Flask==3.0.0",
    "pandas==2.1.1",
    "matplotlib==3.8.0", 
    "numpy==1.26.0",
    "Pillow==10.1.0",
    "gunicorn==21.2.0"
]

def print_header(message):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {message}")
    print("=" * 60)

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}"

def main():
    print_header("FLASK APPLICATION SETUP FOR NAMECHEAP CPANEL")
    
    # Step 1: Detect home directory
    home_dir = str(Path.home())
    print(f"Home directory: {home_dir}")
    
    # Step 2: Create application directory
    app_dir = os.path.join(home_dir, APP_NAME)
    if not os.path.exists(app_dir):
        os.makedirs(app_dir)
        print(f"Created application directory: {app_dir}")
    else:
        print(f"Application directory already exists: {app_dir}")
    
    # Step 3: Create UTF-8 requirements.txt file
    req_file = os.path.join(app_dir, "requirements.txt")
    with open(req_file, "w", encoding="utf-8") as f:
        f.write("\n".join(REQUIREMENTS))
    print(f"Created requirements.txt with UTF-8 encoding")
    
    # Step 4: Create passenger_wsgi.py
    passenger_file = os.path.join(app_dir, "passenger_wsgi.py")
    with open(passenger_file, "w", encoding="utf-8") as f:
        f.write("""import sys
import os

# Add application directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask application
from app import app as application
""")
    print(f"Created passenger_wsgi.py file")
    
    # Step 5: Create simple app.py if it doesn't exist
    app_file = os.path.join(app_dir, "app.py")
    if not os.path.exists(app_file):
        with open(app_file, "w", encoding="utf-8") as f:
            f.write("""from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/national-parks')
def national_parks():
    return render_template('Dashboard_Parques_Nacionales.html')

if __name__ == '__main__':
    app.run(debug=False)
""")
        print(f"Created basic app.py file")
    else:
        print(f"app.py already exists, not modifying")
    
    # Step 6: Create directories for static files and templates
    os.makedirs(os.path.join(app_dir, "static", "images"), exist_ok=True)
    os.makedirs(os.path.join(app_dir, "static", "css"), exist_ok=True)
    os.makedirs(os.path.join(app_dir, "static", "js"), exist_ok=True)
    os.makedirs(os.path.join(app_dir, "templates"), exist_ok=True)
    print("Created directory structure for static files and templates")
    
    # Step 7: Create .htaccess file
    htaccess_file = os.path.join(app_dir, ".htaccess")
    with open(htaccess_file, "w", encoding="utf-8") as f:
        f.write("""# Enable rewrite engine
RewriteEngine On

# Serve static files directly
RewriteCond %{REQUEST_URI} ^/static/.*
RewriteRule ^(.*)$ $1 [L]

# Route all other requests to Passenger
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ passenger_wsgi.py/$1 [QSA,L]
""")
    print("Created .htaccess file for URL rewriting")
    
    # Step 8: Set file permissions
    success, output = run_command(f"chmod 755 {app_dir}")
    success, output = run_command(f"find {app_dir} -type d -exec chmod 755 {{}} \\;")
    success, output = run_command(f"find {app_dir} -type f -exec chmod 644 {{}} \\;")
    success, output = run_command(f"chmod 755 {passenger_file}")
    print("Set proper file permissions")
    
    # Step 9: Create Python version file
    with open(os.path.join(app_dir, "runtime.txt"), "w", encoding="utf-8") as f:
        f.write(f"python-{PYTHON_VERSION}")
    print(f"Created runtime.txt specifying Python {PYTHON_VERSION}")
    
    print_header("SETUP COMPLETED")
    print(f"""
Your Flask application has been configured for cPanel.

Next steps:
1. Upload your project files to the {APP_NAME} directory
   - app.py (if you have your own version)
   - static/ (your static files)
   - templates/ (your HTML templates)

2. In cPanel, navigate to "Setup Python App"
   - Create a new application
   - Set Python version to {PYTHON_VERSION}
   - Set Application root to {app_dir}
   - Set Application URL to your domain or subdomain
   - Set Application startup file to passenger_wsgi.py
   - Set Application Entry point to application

3. After creating the app, click "Start Application"

4. Visit your website to test the application
    """)

if __name__ == "__main__":
    main() 