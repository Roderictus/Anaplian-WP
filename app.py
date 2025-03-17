import matplotlib
matplotlib.use('Agg')
from flask import Flask, render_template, request, Response, url_for
import pandas as pd
import matplotlib.pyplot as plt
import io
import numpy as np
import os
import re
import unicodedata

# Funciones externas
# Load data
file_path = "Parques_Nacionales.csv"  
df = pd.read_csv(file_path)

# Define land cover categories
land_cover_columns = [
    "Percentage_Tree_Cover", "Percentage_Shrubland", "Percentage_Grassland",
    "Percentage_Cropland", "Percentage_Built-up", "Percentage_Bare_Sparse_Vegetation",
    "Percentage_Snow_and_Ice", "Percentage_Permanent_Water_body", "Percentage_Herbaceous_Wetland",
    "Percentage_Mangrove", "Percentage_Moss_and_Lichen"
]

def sanitize_name(name):
    """
    Replace any sequence of non-alphanumeric characters with a single underscore.
    """
    return re.sub(r'[^A-Za-z0-9]+', '_', name)

# Flask y renders
app = Flask(__name__)

@app.route('/')
def index():
    lang = request.args.get('lang', 'en')
    if lang == 'es':
        return render_template('index_es.html')
    elif lang == 'fr':
        return render_template('index_fr.html')  # You'll need to create this file
    return render_template('index.html')

@app.route("/national-parks", methods=["GET", "POST"])
def national_parks():
    selected_park = request.args.get("park", df["Name"].iloc[0])
    sanitized = sanitize_name(selected_park).lower()
    sanitized_alt = sanitized.replace('-', '_')
    image_filename = None

    image_folder = os.path.join(app.root_path, 'static', 'images')
    for filename in os.listdir(image_folder):
        lower_filename = filename.lower()
        if sanitized in lower_filename or sanitized_alt in lower_filename:
            image_filename = filename
            break

    if selected_park in df["Name"].values:
        park_row = df[df["Name"] == selected_park].iloc[0]
    else:
        park_row = df.iloc[0]

    land_cover_mapping = {
        "Percentage_Tree_Cover": 10,
        "Percentage_Shrubland": 20,
        "Percentage_Grassland": 30,
        "Percentage_Cropland": 40,
        "Percentage_Built-up": 50,
        "Percentage_Bare_Sparse_Vegetation": 60,
        "Percentage_Snow_and_Ice": 70,
        "Percentage_Permanent_Water_body": 80,
        "Percentage_Herbaceous_Wetland": 90,
        "Percentage_Mangrove": 95,
        "Percentage_Moss_and_Lichen": 100,
    }
    worldcover_labels = {
        10: "Tree cover",
        20: "Shrubland",
        30: "Grassland",
        40: "Cropland",
        50: "Built-up",
        60: "Bare / Sparse vegetation",
        70: "Snow and Ice",
        80: "Permanent water bodies",
        90: "Herbaceous Wetland",
        95: "Mangrove",
        100: "Moss & Lichen"
    }
    worldcover_color_map = { 
        10: (0, 100, 0),       # Tree cover
        20: (192, 192, 0),     # Shrubland
        30: (64, 128, 0),      # Grassland
        40: (224, 224, 0),     # Cropland
        50: (224, 0, 0),       # Built-up
        60: (255, 170, 127),   # Bare / Sparse vegetation
        70: (255, 255, 255),   # Snow and Ice
        80: (0, 128, 255),     # Permanent water bodies
        90: (0, 255, 255),     # Herbaceous Wetland
        95: (0, 153, 153),     # Mangrove
        100: (191, 191, 191),  # Moss & Lichen
    }

    total_area_ha = park_row["Geometry Area (ha)"]

    land_cover_data = {}
    for col in land_cover_columns:
        key = land_cover_mapping[col]
        label = worldcover_labels[key]
        percent = park_row[col]
        area_ha = (percent / 100) * total_area_ha

        # Compute the hex color for the swatch.
        color_rgb = worldcover_color_map[key]  # e.g., (0, 100, 0) for Tree cover
        color_hex = '#{:02x}{:02x}{:02x}'.format(*color_rgb)
        # Compute the rgb string in the format "rgb(x,x,x)"
        rgb_string = "rgb({},{},{})".format(*color_rgb)

        land_cover_data[label] = {
            "percentage": percent,
            "area": area_ha,
            "color": color_hex,
            "rgb_manual": rgb_string
        }

    return render_template("Dashboard_Parques_Nacionales.html", 
                           parks=df["Name"].tolist(), 
                           selected_park=selected_park,
                           image_filename=image_filename,
                           land_cover_data=land_cover_data)

@app.route("/plot")
def plot():
    park_name = request.args.get("park", df["Name"].iloc[0])
    start_index = df[df["Name"] == park_name].index[0] if park_name in df["Name"].values else 0
    df_subset = df.iloc[start_index:start_index + 1]

    fig, ax = plt.subplots(figsize=(12, 6))
    indices = range(len(df_subset))
    
    # Initialize bottom for stacking
    bottom_values = np.zeros(len(df_subset))
    
    # Mapping each land cover column to its corresponding key in the color maps
    land_cover_mapping = {
        "Percentage_Tree_Cover": 10,
        "Percentage_Shrubland": 20,
        "Percentage_Grassland": 30,
        "Percentage_Cropland": 40,
        "Percentage_Built-up": 50,
        "Percentage_Bare_Sparse_Vegetation": 60,
        "Percentage_Snow_and_Ice": 70,
        "Percentage_Permanent_Water_body": 80,
        "Percentage_Herbaceous_Wetland": 90,
        "Percentage_Mangrove": 95,
        "Percentage_Moss_and_Lichen": 100,
    }

    # Your custom color map (RGB values in 0-255) and labels
    worldcover_color_map = { 
        10: (0, 100, 0),       # Tree cover
        20: (192, 192, 0),     # Shrubland
        30: (64, 128, 0),      # Grassland
        40: (224, 224, 0),     # Cropland
        50: (224, 0, 0),       # Built-up
        60: (255, 170, 127),   # Bare / Sparse vegetation
        70: (255, 255, 255),   # Snow and Ice
        80: (0, 128, 255),     # Permanent water bodies
        90: (0, 255, 255),     # Herbaceous Wetland
        95: (0, 153, 153),     # Mangrove
        100: (191, 191, 191),  # Moss & Lichen
    }
    worldcover_labels = {
        10: "Tree cover",
        20: "Shrubland",
        30: "Grassland",
        40: "Cropland",
        50: "Built-up",
        60: "Bare / Sparse vegetation",
        70: "Snow and Ice",
        80: "Permanent water bodies",
        90: "Herbaceous Wetland",
        95: "Mangrove",
        100: "Moss & Lichen"
    }

    # Plot each land cover column as a stacked bar with the corresponding color
    for land_cover in land_cover_columns:
        values = df_subset[land_cover].values
        key = land_cover_mapping[land_cover]
        
        color_norm = tuple(c / 255 for c in worldcover_color_map[key])
        label = worldcover_labels.get(key, land_cover.replace("Percentage_", "").replace("_", " "))
        ax.bar(indices, values, label=label, color=color_norm, bottom=bottom_values)
        bottom_values += values  # Update the bottom values for stacking

    ax.set_xticks(indices)
    ax.set_xticklabels(df_subset["Name"], rotation=45, ha="right")
    ax.set_ylabel("Porcentaje de Cobertura del Suelo")
    ax.set_title(f" {park_name} Cobertura del Suelo")
    ax.legend(title="Tipo de Cobertura", bbox_to_anchor=(1.05, 1), loc="best")
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)

    return Response(img.getvalue(), mimetype="image/png")


@app.route('/blog_post_2')
def blog_post_2():
    return render_template('blog_post_2.html')

@app.route('/blog_post_1')
def blog_post_1():
    return render_template('blog_post_1.html')

@app.route('/blog')
def blog():
    return render_template('blog.html')

if __name__ == "__main__":
    app.run(debug=True)

