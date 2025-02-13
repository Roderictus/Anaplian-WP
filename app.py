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


def sanitize_name(name):
    """
    Replace any sequence of non-alphanumeric characters with a single underscore.
    """
    return re.sub(r'[^A-Za-z0-9]+', '_', name)

# def sanitize_name(name):
#     # Normalize Unicode to ASCII (removes accents)
#     nfkd_form = unicodedata.normalize('NFKD', name)
#     ascii_str = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
#     ascii_str = ascii_str.lower()  # Convert to lowercase
#     # Replace all spaces with dashes
#     sanitized = re.sub(r'\s+', '-', ascii_str)
#     # Remove any characters except lowercase letters, digits, and dashes
#     sanitized = re.sub(r'[^a-z0-9\-]', '', sanitized)
#     return sanitized

app = Flask(__name__)

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

@app.route("/national-parks", methods=["GET", "POST"])
def national_parks():
    selected_park = request.args.get("park", df["Name"].iloc[0])
    # Convertir a minúsculas para una comparación consistente
    sanitized = sanitize_name(selected_park).lower()
    # También crear una versión alternativa reemplazando guiones por guiones bajos
    sanitized_alt = sanitized.replace('-', '_')
    image_filename = None

    image_folder = os.path.join(app.root_path, 'static', 'images')
    for filename in os.listdir(image_folder):
        lower_filename = filename.lower()
        print("Checking file:", lower_filename)  # Útil para depurar
        if sanitized in lower_filename or sanitized_alt in lower_filename:
            image_filename = filename
            print("Found image filename:", image_filename)
            break

    # Completar el diccionario con las coberturas para cada categoría
    coverage_data = {
        "Tree cover": df[df["Name"] == selected_park]["Percentage_Tree_Cover"].iloc[0],
        "Shrubland": df[df["Name"] == selected_park]["Percentage_Shrubland"].iloc[0],
        "Grassland": df[df["Name"] == selected_park]["Percentage_Grassland"].iloc[0],
        "Cropland": df[df["Name"] == selected_park]["Percentage_Cropland"].iloc[0],
        "Built-up": df[df["Name"] == selected_park]["Percentage_Built-up"].iloc[0],
        "Bare / Sparse vegetation": df[df["Name"] == selected_park]["Percentage_Bare_Sparse_Vegetation"].iloc[0],
        "Snow and Ice": df[df["Name"] == selected_park]["Percentage_Snow_and_Ice"].iloc[0],
        "Permanent water bodies": df[df["Name"] == selected_park]["Percentage_Permanent_Water_body"].iloc[0],
        "Herbaceous Wetland": df[df["Name"] == selected_park]["Percentage_Herbaceous_Wetland"].iloc[0],
        "Mangrove": df[df["Name"] == selected_park]["Percentage_Mangrove"].iloc[0],
        "Moss & Lichen": df[df["Name"] == selected_park]["Percentage_Moss_and_Lichen"].iloc[0],
    }

    return render_template("Dashboard_Parques_Nacionales.html", 
                           parks=df["Name"].tolist(), 
                           selected_park=selected_park,
                           image_filename=image_filename,
                           coverage_data=coverage_data)


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
        # Convert the RGB tuple (0-255) to normalized RGB (0-1)
        color_norm = tuple(c / 255 for c in worldcover_color_map[key])
        label = worldcover_labels.get(key, land_cover.replace("Percentage_", "").replace("_", " "))
        ax.bar(indices, values, label=label, color=color_norm, bottom=bottom_values)
        bottom_values += values  # Update the bottom values for stacking

    ax.set_xticks(indices)
    ax.set_xticklabels(df_subset["Name"], rotation=45, ha="right")
    ax.set_ylabel("Porcentaje de Cobertura del Suelo")
    ax.set_title(f"Cobertura del Suelo para {park_name}")
    ax.legend(title="Tipo de Cobertura", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)

    return Response(img.getvalue(), mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)

