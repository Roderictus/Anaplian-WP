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

    return render_template("Dashboard_Parques_Nacionales.html", 
                           parks=df["Name"].tolist(), 
                           selected_park=selected_park,
                           image_filename=image_filename)

@app.route("/plot")
def plot():
    park_name = request.args.get("park", df["Name"].iloc[0])
    start_index = df[df["Name"] == park_name].index[0] if park_name in df["Name"].values else 0
    df_subset = df.iloc[start_index:start_index + 1]

    fig, ax = plt.subplots(figsize=(12, 6))
    indices = range(len(df_subset))
    
    # Initialize as a numpy array for proper element-wise addition
    bottom_values = np.zeros(len(df_subset))
    for land_cover in land_cover_columns:
        values = df_subset[land_cover].values
        ax.bar(indices, values, label=land_cover.replace("Percentage_", "").replace("_", " "), bottom=bottom_values)
        bottom_values += values  # This now performs element-wise addition

    ax.set_xticks(indices)
    ax.set_xticklabels(df_subset["Name"], rotation=45, ha="right")
    ax.set_ylabel("Porcentaje de Cobertura del Suelo")
    ax.set_title(f"Cobertura del Suelo para {park_name} ")
    ax.legend(title="Tipo de Cobertura", bbox_to_anchor=(1.05, 1), loc="upper left")

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close(fig)

    return Response(img.getvalue(), mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)

