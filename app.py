# app.py - SCALABLE MULTI-COUNTRY VERSION
import os
import re
import io
import json
import math
import pandas as pd
from flask import Flask, render_template, request, abort

# --- 1. APP SETUP & GLOBAL CONSTANTS ---

app = Flask(__name__)

# Universal land cover definitions, mapping codes to English labels
LAND_COVER_DEFINITIONS = {
    10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
    50: "Built-up", 60: "Bare / Sparse vegetation", 70: "Snow and Ice",
    80: "Permanent water bodies", 90: "Herbaceous Wetland", 95: "Mangrove", 100: "Moss & Lichen"
}
# Universal color map for table swatches
LAND_COVER_COLORS = {
    "Tree cover": "#006400", "Shrubland": "#c0c000", "Grassland": "#408000",
    "Cropland": "#e0e000", "Built-up": "#e00000", "Bare / Sparse vegetation": "#ffaa7f",
    "Snow and Ice": "#ffffff", "Permanent water bodies": "#0080ff",
    "Herbaceous Wetland": "#00ffff", "Mangrove": "#009999", "Moss & Lichen": "#bfbfbf"
}
# Translations for land cover labels (used in the template)
LAND_COVER_TRANSLATIONS = {
    'es': {
        "Tree cover": "Cobertura arbórea", "Shrubland": "Zona de arbustos", "Grassland": "Pastizales",
        "Cropland": "Cultivos", "Built-up": "Zona urbanizada", "Bare / Sparse vegetation": "Vegetación escasa o nula",
        "Snow and Ice": "Nieve y hielo", "Permanent water bodies": "Cuerpos de agua permanentes",
        "Herbaceous Wetland": "Humedal herbáceo", "Mangrove": "Manglar", "Moss & Lichen": "Musgo y liquen"
    },
    'fr': {
        "Tree cover": "Couvert arboré", "Shrubland": "Zone arbustive", "Grassland": "Prairie",
        "Cropland": "Terres cultivées", "Built-up": "Zone bâtie", "Bare / Sparse vegetation": "Végétation éparse ou nulle",
        "Snow and Ice": "Neige et glace", "Permanent water bodies": "Plans d'eau permanents",
        "Herbaceous Wetland": "Zone humide herbacée", "Mangrove": "Mangrove", "Moss & Lichen": "Mousse et lichen"
    }
}

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


# --- 2. PRE-COMPUTATION / CACHING LOGIC (RUNS ONLY ONCE AT STARTUP) ---

def load_all_country_data(static_folder_path):
    """
    Reads the master CSV and processes data for ALL countries at once,
    storing it in a structured dictionary for instant access later.
    """
    print("--- Loading and caching data for all countries... ---")
    master_park_data = {}
    try:
        csv_path = os.path.join(static_folder_path, 'data', 'Combined_country_recalculated.csv')
        df = pd.read_csv(csv_path)
        df.fillna({'DESIG': 'N/A', 'GOV_TYPE': 'N/A'}, inplace=True) # Handle potential missing values
    except FileNotFoundError:
        print(f"FATAL ERROR: Master CSV not found at {csv_path}")
        return {}

    for country_name, country_df in df.groupby('Country'):
        print(f"Processing {country_name}...")
        country_park_list = []
        image_folder = os.path.join(static_folder_path, 'images', country_name, "Land_Cover")

        if not os.path.isdir(image_folder):
            print(f"WARNING: Image directory not found for {country_name} at {image_folder}. Skipping.")
            continue

        image_files = {f.split('__')[0].replace('_', ' ').lower(): f for f in os.listdir(image_folder)}
        
        for _, park_row in country_df.iterrows():
            park_name_sanitized = park_row['Name'].lower()
            
            if park_name_sanitized in image_files:
                land_cover_table = []
                for code, label in LAND_COVER_DEFINITIONS.items():
                    percentage_col = f'Percentage_{code}'
                    if percentage_col in park_row and park_row[percentage_col] > 0:
                        land_cover_table.append({
                            "label": label,
                            "percentage": round(park_row[percentage_col], 2),
                            "color": LAND_COVER_COLORS.get(label, '#808080')
                        })
                
                land_cover_table.sort(key=lambda x: x['percentage'], reverse=True)

                country_park_list.append({
                    'name': park_row['Name'],
                    'image_file': image_files[park_name_sanitized],
                    'desig': park_row['DESIG'],
                    'gov_type': park_row['GOV_TYPE'],
                    'gis_area': round(park_row.get('GIS_AREA', 0), 2),
                    'land_cover_table': land_cover_table
                })
        
        master_park_data[country_name] = sorted(country_park_list, key=lambda p: p['name'])
        print(f"-> Cached {len(country_park_list)} parks for {country_name}.")
    
    print("--- Caching complete. ---")
    return master_park_data

# Run the loader function once and store the result in the global cache
CACHED_PARK_DATA = load_all_country_data(app.static_folder)


# --- 3. DYNAMIC ROUTE FOR ALL COUNTRIES ---

@app.route("/country/<string:country_name>")
def show_country(country_name):

    country_key = country_name.capitalize()

    if country_key not in CACHED_PARK_DATA:
        abort(404, description=f"Data for country '{country_key}' not found.")

    lang = request.args.get('lang', 'es')
    page = request.args.get('page', 1, type=int)

    country_data = CACHED_PARK_DATA[country_key]
    
    items_per_page = 20
    total_items = len(country_data)
    total_pages = math.ceil(total_items / items_per_page)
    start_index = (page - 1) * items_per_page
    end_index = start_index + items_per_page
    paginated_parks = country_data[start_index:end_index]

    context = {
        'country_name': country_key,
        'parks_data': paginated_parks,
        'image_folder': f"images/{country_key}/Land_Cover",
        'current_page': page,
        'total_pages': total_pages,
        'lang': lang,
        #'land_cover_translations': json.dumps(LAND_COVER_TRANSLATIONS.get(lang, {})), # may be incorrect
        'land_cover_translations': LAND_COVER_TRANSLATIONS.get(lang, {}), #potential correction
    }

    template_name = f"{country_name.lower()}.html"
    return render_template(template_name, **context)


# --- 4. LEGACY AND OTHER ROUTES  ---


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

# --- 5. APP LAUNCHER ---
if __name__ == "__main__":
    app.run(debug=True)