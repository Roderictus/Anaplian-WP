#!/usr/bin/env python
import sys
import os

# Add your app directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import your Flask app
from app import app as application 