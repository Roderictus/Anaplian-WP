#!/usr/bin/env python
import os
import sys

# Activate your virtual environment, if you are using one.
venv_path = os.path.join(os.path.dirname(__file__), "venv")
activate_this = os.path.join(venv_path, "bin", "activate_this.py")
if os.path.exists(activate_this):
    with open(activate_this) as file_:
        exec(file_.read(), dict(__file__=activate_this))

# Add the current directory to sys.path to ensure modules are loaded correctly.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import your Flask app as the WSGI application.
from app import app as application 