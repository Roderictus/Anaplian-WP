#!/usr/bin/env python3
"""
Incremental Flask App for Debugging
Gradually uncomment sections to identify the source of 500 errors
"""
import os
import sys
import logging

# Set up error logging to file
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'app_debug.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Basic Flask application
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for
    app = Flask(__name__)
    app.secret_key = 'debug-secret-key-change-in-production'
    
    logging.info("Flask initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Flask: {str(e)}")
    raise

# Basic route for testing
@app.route('/debug')
def debug():
    """Basic debug endpoint to verify the app is running"""
    return "Flask application is responding. Debug mode active."

# =========================================================
# STEP 1: BASIC ROUTES - Uncomment this section first
# =========================================================
@app.route('/')
def index():
    """Homepage route"""
    try:
        return render_template('index.html')
    except Exception as e:
        logging.error(f"Error in index route: {str(e)}")
        return f"Error rendering index: {str(e)}", 500

# Uncomment this after confirming index works
# @app.route('/national-parks')
# def national_parks():
#     """National parks dashboard route"""
#     try:
#         # Just render template without data first
#         return render_template('Dashboard_Parques_Nacionales.html')
#     except Exception as e:
#         logging.error(f"Error in national_parks route: {str(e)}")
#         return f"Error rendering national parks dashboard: {str(e)}", 500

# =========================================================
# STEP 2: DATA IMPORTS - Uncomment after basic routes work
# =========================================================
# try:
#     # Configure matplotlib for non-interactive use (important for cPanel)
#     import matplotlib
#     matplotlib.use('Agg')  # Use non-interactive backend
#     os.environ['MPLCONFIGDIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tmp')
#     os.makedirs(os.environ['MPLCONFIGDIR'], exist_ok=True)
#     logging.info("Matplotlib configured for non-interactive use")
#     
#     # Import pandas - comment out if not using
#     import pandas as pd
#     logging.info("Pandas imported successfully")
#     
#     # Import numpy - comment out if not using
#     import numpy as np
#     logging.info("Numpy imported successfully")
#     
#     # Import other libraries as needed
#     # import other_library
# except Exception as e:
#     logging.error(f"Error importing data libraries: {str(e)}")
#     # Continue without failing - we'll handle errors in the routes

# =========================================================
# STEP 3: DATA LOADING - Uncomment after imports work
# =========================================================
# try:
#     # Example: Load your data using absolute paths
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     
#     # Example: Load CSV file - adjust to your actual data files
#     # df = pd.read_csv(os.path.join(base_dir, 'data', 'parks.csv'))
#     # logging.info(f"Data loaded successfully with {len(df)} records")
# except Exception as e:
#     logging.error(f"Error loading data: {str(e)}")
#     # Create a placeholder/empty dataframe so routes don't fail
#     # df = pd.DataFrame(columns=['Name'])  # Add your column names

# =========================================================
# STEP 4: FULL NATIONAL PARKS ROUTE - Uncomment once data loads
# =========================================================
# @app.route('/national-parks')
# def national_parks():
#     """National parks dashboard with data"""
#     try:
#         # Replace this with your actual data processing
#         # selected_park = request.args.get("park", df["Name"].iloc[0])
#         # parks = df["Name"].tolist()
#         
#         # For testing, use dummy data
#         parks = ["Test Park 1", "Test Park 2"]
#         selected_park = request.args.get("park", parks[0])
#         image_filename = "placeholder.png"  # Update with your logic
#         
#         # Create dummy land cover data for testing
#         land_cover_data = [
#             {"category": "Forest", "percentage": 30, "color": "#00FF00"},
#             {"category": "Water", "percentage": 20, "color": "#0000FF"},
#             {"category": "Urban", "percentage": 10, "color": "#808080"}
#         ]
#         
#         logging.info(f"Rendering dashboard for park: {selected_park}")
#         return render_template(
#             "Dashboard_Parques_Nacionales.html",
#             parks=parks,
#             selected_park=selected_park,
#             image_filename=image_filename,
#             land_cover_data=land_cover_data
#         )
#     except Exception as e:
#         logging.error(f"Error in national_parks route: {str(e)}")
#         return f"Error processing national parks data: {str(e)}", 500

# =========================================================
# STEP 5: YOUR ADDITIONAL ROUTES - Add as needed
# =========================================================
# @app.route('/other-route')
# def other_route():
#     """Add your other routes here"""
#     return "Other route"

# Error handler for 500 errors
@app.errorhandler(500)
def server_error(e):
    logging.error(f"500 error: {str(e)}")
    return f"<h1>500 Internal Server Error</h1><p>Error: {str(e)}</p>", 500

# Error handler for 404 errors
@app.errorhandler(404)
def not_found(e):
    logging.error(f"404 error: {str(e)}")
    return f"<h1>404 Not Found</h1><p>The requested URL was not found on the server.</p>", 404

if __name__ == '__main__':
    app.run(debug=False)