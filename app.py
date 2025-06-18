import math
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
import json

# Define these mappings globally in your app.py, outside of any function
# This maps the CSV column number to a human-readable label
INDONESIA_LAND_COVER_LABELS = {
    10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
    50: "Built-up", 60: "Bare / Sparse vegetation", 70: "Snow and Ice",
    80: "Permanent water bodies", 90: "Herbaceous Wetland", 95: "Mangrove", 100: "Moss & Lichen"
}
# Pre-defined colors for the chart, matching the WorldCover standard
INDONESIA_CHART_COLORS = [
    '#006400', '#c0c000', '#408000', '#e0e000', '#e00000',
    '#ffaa7f', '#ffffff', '#0080ff', '#00ffff', '#009999', '#bfbfbf'
]


# Funciones externas
# Load data
file_path = os.path.join('static', 'data', 'Parques_Nacionales_with_descriptions.csv')
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
        return render_template('index_fr.html')  
    return render_template('index.html')

@app.route("/national-parks", methods=["GET", "POST"])
def national_parks():
    # Get the current park selection
    df = pd.read_csv('static/data/Parques_Nacionales_with_descriptions.csv')
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

    total_area_ha = park_row["GIS_AREA"]

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

    # Get the description from the new column
    park_description = park_row["Descripcion_esp"]

    return render_template("Dashboard_Parques_Nacionales.html", 
                           parks=df["Name"].tolist(), 
                           selected_park=selected_park,
                           image_filename=image_filename,
                           land_cover_data=land_cover_data,
                           park_description=park_description)







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

@app.route('/blog_post_2_en')
def blog_post_2_en():
    return render_template('blog_post_2_en.html')

@app.route('/blog_post_2_fr')
def blog_post_2_fr():
    return render_template('blog_post_2_fr.html')

@app.route("/national-parks-en", methods=["GET", "POST"])
def national_parks_en():
    # Get the current park selection
    df = pd.read_csv('static/data/Parques_Nacionales_with_descriptions.csv')
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

    total_area_ha = park_row["GIS_AREA"]

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

    # Change to use English description
    park_description = park_row["Description_eng"]

    return render_template("Dashboard_Parques_Nacionales_en.html", 
                           parks=df["Name"].tolist(), 
                           selected_park=selected_park,
                           image_filename=image_filename,
                           land_cover_data=land_cover_data,
                           park_description=park_description)

@app.route("/national-parks-fr", methods=["GET", "POST"])
def national_parks_fr():
    # Get the current park selection
    df = pd.read_csv('static/data/Parques_Nacionales_with_descriptions.csv')
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

    total_area_ha = park_row["GIS_AREA"]

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

    # Change to use French description
    park_description = park_row["Description_fr"]

    return render_template("Dashboard_Parques_Nacionales_fr.html", 
                           parks=df["Name"].tolist(), 
                           selected_park=selected_park,
                           image_filename=image_filename,
                           land_cover_data=land_cover_data,
                           park_description=park_description)


############    INDONESIA#####################

@app.route('/indonesia_parks')
def indonesia_parks():
    # --- 1. SETUP LANGUAGE, PAGINATION, AND LOAD DATA ---
    lang = request.args.get('lang', 'es')
    page = request.args.get('page', 1, type=int)
    
    translations = {
        'es': {'title': 'Parques de Indonesia', 'header': 'Parques Nacionales de Indonesia', 'desc': 'Haga clic en un parque para ver detalles.', 'empty': 'No se encontraron imágenes.', 'area_label': 'Área Total'},
        'en': {'title': 'Indonesian Parks', 'header': 'Indonesian National Parks', 'desc': 'Click a park to see details.', 'empty': 'No images found.', 'area_label': 'Total Area'},
        'fr': {'title': 'Parcs d\'Indonésie', 'header': 'Parcs Nationaux d\'Indonésie', 'desc': 'Cliquez sur un parc pour voir les détails.', 'empty': 'Aucune image trouvée.', 'area_label': 'Zone Totale'}
    }
    text_content = translations.get(lang, translations['es'])

    # Load park statistics from CSV
    try:
        csv_path = os.path.join(app.static_folder, 'images/Indonesia/Indonesia_Land_Cover/Indonesia_worldcover_stats.csv')
        parks_df = pd.read_csv(csv_path)

        # ------------------- FIX IS HERE -------------------
        # This new line removes any rows with duplicate park names, keeping the first one it finds.
        # This guarantees that every park name in the DataFrame is now unique.
        parks_df.drop_duplicates(subset=['Name'], keep='first', inplace=True)
        # ---------------- END OF FIX -------------------

        parks_df.set_index('Name', inplace=True) # Now it's safe to set the index.
    except FileNotFoundError:
        parks_df = pd.DataFrame()

    # --- 2. COMBINE IMAGE FILES WITH CSV DATA ---
    image_folder_path = 'images/Indonesia/Indonesia_Land_Cover'
    full_path = os.path.join(app.static_folder, image_folder_path)
    all_park_data = []

    try:
        image_files = sorted([f for f in os.listdir(full_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        for image_file in image_files:
            park_name_from_file = image_file.split('__')[0].replace('_', ' ')
            
            if not parks_df.empty and park_name_from_file in parks_df.index:
                # Because we removed duplicates, this will now ALWAYS be a single row (a Series).
                park_stats = parks_df.loc[park_name_from_file]

                chart_labels = []
                chart_percentages = []
                for code, label in INDONESIA_LAND_COVER_LABELS.items():
                    percentage_col = f'Percentage_{code}'
                    # The line below will now work correctly without ambiguity.
                    if percentage_col in park_stats and park_stats[percentage_col] > 0:
                        chart_labels.append(label)
                        chart_percentages.append(round(park_stats[percentage_col], 2))

                all_park_data.append({
                    'image_file': image_file,
                    'park_name': park_name_from_file,
                    'gis_area_ha': round(park_stats['GIS_AREA'], 2),
                    'chart_data': {
                        'labels': json.dumps(chart_labels),
                        'percentages': json.dumps(chart_percentages),
                        'colors': json.dumps(INDONESIA_CHART_COLORS)
                    }
                })
    except FileNotFoundError:
        all_park_data = []

    # --- 3. PAGINATION ---
    items_per_page = 20
    total_items = len(all_park_data)
    total_pages = math.ceil(total_items / items_per_page)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_parks = all_park_data[start_index:end_index]

    # --- 4. RENDER ---
    return render_template(
        'indonesia.html',
        parks_data=paginated_parks,
        image_folder=image_folder_path,
        current_page=page,
        total_pages=total_pages,
        lang=lang,
        text=text_content
    )

###################################################################################



if __name__ == "__main__":
    app.run(debug=True)

