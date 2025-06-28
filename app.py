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

INDEX_PAGE_TRANSLATIONS = {
    'en': {
        'title': "Anaplian - Research, Applied",
        'meta_desc': "Anaplian - Research, applied.",
        'lang_button': "Language",
        'nav_home': "Home", 
        'nav_who': "Who We Are", 
        'nav_contact': "Contact", 
        'nav_parks': "National Parks",
        'hero_title': "Welcome to Anaplian",
        'hero_subtitle': "Applying state-of-the-art research in geospatial and socio-economic fields to your company needs.",
        'learn_more_button': "Learn More",
        'parks_title': "Mexico Land Parks",
        'parks_subtitle': "Land Cover Analisis for Mexico National Parks",
        'learn_more_parks_button': "Mexico National Parks",
        'indonesia_title': "Indonesia National Parks",
        'indonesia_subtitle': "Land Cover in Indonesia National Parks.",
        'indonesia_button': "Indonesia National Parks",
        'madagascar_title': "Madagascar National Parks",
        'madagascar_subtitle': "Land Cover in Madagascar National Parks.",
        'madagascar_button': "Madagascar National Parks",
        'blog_title': "Blog",
        'blog_subtitle': "Stay updated with our latest insights and developments in applied research and socio-economic solutions.",
        'blog1_title': "National Parks: How Protected Are Our Natural Protected Areas?",
        'blog1_desc': "Motivated by our passion for hiking and alerted by the visible deterioration of some routes, several members of the Anaplian team, together with Mexico en Datos, decided to carry out a diagnosis of the Natural Protected Areas due to the lack of official data.",
        'blog2_title': "Developments in the Automated Dashboard for Monitoring National Parks",
        'blog2_desc': "Anaplian begins the year 2025 with progress on one of our favorite public projects: the development of an automated dashboard for monitoring National Parks.",
        'blog_button_main': "Go to Blog Post",
        'blog_button_all': "View All Blog Posts",
        'who_title': "Who We Are",
        'contact_title': "Get in Touch",
        'contact_subtitle': "We'd love to hear from you. Please reach out with any inquiries at",
        'team': {
            'rodrigo': [
                "With 20 years of experience in data science, economics, and consulting, I created Anaplian to bring practical, data-driven insights to businesses.",
                "My work has spanned various sectors, from economic impact studies to sustainability projects. I've led teams and managed projects for both public and private organizations, always focusing on delivering results that make a difference.",
                "At Anaplian, I bring that same commitment to each client, ensuring our services are tailored to your specific needs and challenges. Anaplian is all about turning data into meaningful insights. Whether you need help with data analysis, financial modeling, or understanding the economic impact of your decisions, we're here to provide straightforward, reliable solutions. With our expertise, we aim to help your business thrive in today's complex, data-driven world."
            ],
            'edgar': [
                "I am an Assistant Professor in the Department of Political Science at the University of Michigan. My research interests include Latin American politics, historical political economy, criminal violence, and indigenous politics. My work received the 2021 Heinz I. Eulau Award for the best article published in the APSR, and the 2022 Mary Parker Follett award for the best article on politics and history.",
                "My research is multi-method and combines statistical analysis, archival research, GIS, text analysis, machine learning, survey experiments, and lab-in-the-field approaches.",
                "I am a co-PI of the Historical Institutions Lab, a faculty associate at the Center for Political Studies, and at the Michigan Institute for Data Science. I collaborate with the Poverty|Violence|Governance Lab (Stanford), the Digging Early Colonial History Project (University of Lancaster), and the Conflict & Peace, Research & Development (University of Michigan)."
            ],
            'juan': [
                "Juan is an energy and environment specialist with years of expertise in policy, program and project development. He has worked with numerous public and private entities, as well as multilateral organizations. Juan has provided consultancy services to governments and international organizations across Latin America. He currently serves as an associate consultant for the World Bank's Carbon Market Unit."
            ],
            'nicolas': [
                "As a bioinformatician and computational biologist with extensive expertise in AI, algorithms, machine learning, and data science, I specialize in delivering innovative, data-driven solutions for the biomedical field. With a proven track record across genomics, epigenomics, transcriptomics, and clinical data analysis, I design and implement advanced computational pipelines that provide clients with clear, impactful insights to accelerate research and development.",
                "My consultancy operates at the intersection of science and technology, bringing together knowledge from highly interdisciplinary fields. With experience collaborating alongside wet-lab scientists, mathematicians, biologists, IT specialists, and clinicians, I act as a bridge to facilitate effective communication and integration across disciplines. This collaborative approach ensures our solutions are not only technically robust but also aligned with scientific and business objectives.",
                "Leveraging experience and publications in leading journals, including Nature Genetics, Nature Methods and Cell, among others, I am committed to translating complex data into strategic insights that propel advancements in personalized medicine, drug discovery, and precision health among other fields. My goal is to help clients unlock the full potential of their data, driving transformative progress in healthcare and beyond."
            ]
        }
    },
    'es': {
        'title': "Anaplian - Investigación Aplicada",
        'meta_desc': "Anaplian - Investigación aplicada.",
        'lang_button': "Idioma",
        'nav_home': "Inicio", 
        'nav_who': "Quiénes Somos", 
        'nav_contact': "Contacto", 
        'nav_parks': "Parques Nacionales",
        'hero_title': "Bienvenido a Anaplian",
        'hero_subtitle': "Aplicando investigación de vanguardia en los campos geoespacial y socioeconómico a las necesidades de su empresa.",
        'learn_more_button': "Conoce Más",
        'parks_title': "Parques Nacionales de México",
        'parks_subtitle': "Análisis de Cobertura del Suelo para Parques Nacionales de México",
        'learn_more_parks_button': "Parques Nacionales de México",
        'indonesia_title': "Parques Nacionales de Indonesia",
        'indonesia_subtitle': "Cobertura del suelo en los Parques Nacionales de Indonesia.",
        'indonesia_button': "Parques Nacionales de Indonesia",
        'madagascar_title': "Parques Nacionales de Madagascar",
        'madagascar_subtitle': "Cobertura del suelo en los Parques Nacionales de Madagascar.",
        'madagascar_button': "Parques Nacionales de Madagascar",
        'blog_title': "Blog",
        'blog_subtitle': "Manténgase actualizado con nuestras últimas ideas y desarrollos en investigación aplicada y soluciones socioeconómicas.",
        'blog1_title': "Parques Nacionales ¿Qué tan protegidas están nuestras Áreas Naturales Protegidas?",
        'blog1_desc': "Motivados por nuestra pasión por el senderismo y alertados por el deterioro visible de algunas rutas, varios integrantes del equipo de Anaplian, junto con México en Datos, decidimos realizar un diagnóstico de las Áreas Naturales Protegidas ante la falta de datos oficiales.",
        'blog2_title': "Avances en el Tablero Automatizado para el Monitoreo de Parques Nacionales",
        'blog2_desc': "Anaplian comienza el año 2025 con avances en uno de nuestros proyectos públicos favoritos: el desarrollo de un tablero automatizado para el monitoreo de Parques Nacionales.",
        'blog_button_main': "Ir a la entrada del blog",
        'blog_button_all': "Ver Todas las Entradas del Blog",
        'who_title': "Quiénes Somos",
        'contact_title': "Ponte en Contacto",
        'contact_subtitle': "Nos encantaría saber de usted. Por favor, póngase en contacto con cualquier consulta en",
        'team': {
            'rodrigo': [
                "Con 20 años de experiencia en ciencia de datos, economía y consultoría, creé Anaplian para brindar información práctica basada en datos a las empresas.",
                "Mi trabajo ha abarcado varios sectores, desde estudios de impacto económico hasta proyectos de sostenibilidad. He liderado equipos y gestionado proyectos para organizaciones públicas y privadas, siempre enfocándome en entregar resultados que marquen la diferencia.",
                "En Anaplian, mantengo ese mismo compromiso con cada cliente, asegurando que nuestros servicios estén adaptados a sus necesidades y desafíos específicos."
            ],
            'edgar': [
                "Soy Profesor Asistente en el Departamento de Ciencias Políticas de la Universidad de Michigan. Mis intereses de investigación incluyen la política latinoamericana, la economía política histórica, la violencia criminal y la política indígena. Mi trabajo recibió el Premio Heinz I. Eulau 2021 al mejor artículo publicado en APSR y el premio Mary Parker Follett 2022 al mejor artículo sobre política e historia.",
                "Mi investigación es multimétodo y combina análisis estadístico, investigación de archivos, SIG, análisis de texto, aprendizaje automático, experimentos de encuestas y enfoques de laboratorio en campo.",
                "Soy co-investigador principal del Laboratorio de Instituciones Históricas, profesor asociado en el Centro de Estudios Políticos y en el Instituto de Ciencia de Datos de Michigan. Colaboro con el Laboratorio de Pobreza|Violencia|Gobernanza (Stanford), el Proyecto de Historia Colonial Temprana (Universidad de Lancaster) y el grupo de Investigación y Desarrollo de Conflicto y Paz (Universidad de Michigan)."
            ],
            'juan': [
                "Juan es un especialista en energía y medio ambiente con años de experiencia en desarrollo de políticas, programas y proyectos. Ha trabajado con numerosas entidades públicas y privadas, así como con organizaciones multilaterales. Juan ha brindado servicios de consultoría a gobiernos y organizaciones internacionales en toda América Latina. Actualmente se desempeña como consultor asociado de la Unidad de Mercado de Carbono del Banco Mundial."
            ],
            'nicolas': [
                "Como bioinformático y biólogo computacional con amplia experiencia en IA, algoritmos, aprendizaje automático y ciencia de datos, me especializo en ofrecer soluciones innovadoras basadas en datos para el campo biomédico. Con una trayectoria probada en genómica, epigenómica, transcriptómica y análisis de datos clínicos, diseño e implemento pipelines computacionales avanzados que proporcionan a los clientes información clara e impactante para acelerar la investigación y el desarrollo.",
                "Mi consultoría opera en la intersección de la ciencia y la tecnología, reuniendo conocimientos de campos altamente interdisciplinarios. Con experiencia en colaboración con científicos de laboratorio, matemáticos, biólogos, especialistas en TI y clínicos, actúo como puente para facilitar la comunicación efectiva y la integración entre disciplinas.",
                "Aprovechando la experiencia y publicaciones en revistas líderes, incluyendo Nature Genetics, Nature Methods y Cell, entre otras, estoy comprometido a traducir datos complejos en información estratégica que impulse avances en medicina personalizada, descubrimiento de fármacos y salud de precisión, entre otros campos."
            ]
        }
    },
    'fr': {
        'title': "Anaplian - Recherche Appliquée",
        'meta_desc': "Anaplian - Recherche appliquée.",
        'lang_button': "Langue",
        'nav_home': "Accueil", 
        'nav_who': "Qui Nous Sommes", 
        'nav_contact': "Contact", 
        'nav_parks': "Parcs Nationaux",
        'hero_title': "Bienvenue chez Anaplian",
        'hero_subtitle': "Appliquer la recherche de pointe dans les domaines géospatial et socio-économique aux besoins de votre entreprise.",
        'learn_more_button': "En Savoir Plus",
        'parks_title': "Parcs Nationaux du Mexique",
        'parks_subtitle': "Analyse de Couverture Terrestre pour les Parcs Nationaux du Mexique",
        'learn_more_parks_button': "Parcs Nationaux du Mexique",
        'indonesia_title': "Parcs Nationaux d'Indonésie",
        'indonesia_subtitle': "Couverture terrestre dans les parcs nationaux d'Indonésie.",
        'indonesia_button': "Parcs Nationaux d'Indonésie",
        'madagascar_title': "Parcs Nationaux de Madagascar",
        'madagascar_subtitle': "Couverture terrestre dans les parcs nationaux de Madagascar.",
        'madagascar_button': "Parcs Nationaux de Madagascar",
        'blog_title': "Blog",
        'blog_subtitle': "Restez à jour avec nos dernières perspectives et développements en recherche appliquée et solutions socio-économiques.",
        'blog1_title': "Parcs Nationaux : Nos aires naturelles protégées sont-elles bien protégées ?",
        'blog1_desc': "Motivés par notre passion pour la randonnée et alertés par la détérioration visible de certains sentiers, plusieurs membres de l'équipe d'Anaplian, en collaboration avec Mexico en Datos, ont décidé de réaliser un diagnostic des Aires Naturelles Protégées face au manque de données officielles.",
        'blog2_title': "Développements du tableau de bord automatisé pour le suivi des parcs nationaux",
        'blog2_desc': "Anaplian commence l'année 2025 avec des progrès sur l'un de nos projets publics préférés : le développement d'un tableau de bord automatisé pour le suivi des Parcs Nationaux.",
        'blog_button_main': "Aller à l'article de blog",
        'blog_button_all': "Voir Tous les Articles du Blog",
        'who_title': "Qui Nous Sommes",
        'contact_title': "Contactez-Nous",
        'contact_subtitle': "Nous serions ravis de vous entendre. Veuillez nous contacter pour toute demande à",
        'team': {
            'rodrigo': [
                "Avec 20 ans d'expérience en science des données, économie et conseil, j'ai créé Anaplian pour apporter des informations pratiques basées sur les données aux entreprises.",
                "Mon travail s'est étendu à divers secteurs, des études d'impact économique aux projets de durabilité. J'ai dirigé des équipes et géré des projets pour des organisations publiques et privées, en me concentrant toujours sur l'obtention de résultats qui font la différence.",
                "Chez Anaplian, je maintiens le même engagement envers chaque client, en veillant à ce que nos services soient adaptés à vos besoins et défis spécifiques."
            ],
            'edgar': [
                "Je suis professeur assistant au Département de Sciences Politiques de l'Université du Michigan. Mes intérêts de recherche incluent la politique latino-américaine, l'économie politique historique, la violence criminelle et la politique autochtone. Mon travail a reçu le prix Heinz I. Eulau 2021 pour le meilleur article publié dans l'APSR et le prix Mary Parker Follett 2022 pour le meilleur article sur la politique et l'histoire.",
                "Ma recherche est multi-méthode et combine analyse statistique, recherche d'archives, SIG, analyse de texte, apprentissage automatique, expériences d'enquête et approches de laboratoire sur le terrain.",
                "Je suis co-chercheur principal du Laboratoire des Institutions Historiques, professeur associé au Centre d'Études Politiques et à l'Institut de Science des Données du Michigan. Je collabore avec le Laboratoire Pauvreté|Violence|Gouvernance (Stanford), le Projet d'Histoire Coloniale Précoce (Université de Lancaster) et le groupe de Recherche et Développement sur les Conflits et la Paix (Université du Michigan)."
            ],
            'juan': [
                "Juan est un spécialiste de l'énergie et de l'environnement avec des années d'expertise dans le développement de politiques, de programmes et de projets. Il a travaillé avec de nombreuses entités publiques et privées, ainsi qu'avec des organisations multilatérales. Juan a fourni des services de conseil aux gouvernements et aux organisations internationales à travers l'Amérique latine. Il est actuellement consultant associé à l'Unité du Marché du Carbone de la Banque mondiale."
            ],
            'nicolas': [
                "En tant que bioinformaticien et biologiste computationnel avec une vaste expertise en IA, algorithmes, apprentissage automatique et science des données, je me spécialise dans la fourniture de solutions innovantes basées sur les données pour le domaine biomédical. Avec une expérience éprouvée en génomique, épigénomique, transcriptomique et analyse de données cliniques, je conçois et implémente des pipelines computationnels avancés.",
                "Mon activité de conseil opère à l'intersection de la science et de la technologie, rassemblant des connaissances de domaines hautement interdisciplinaires. Avec une expérience de collaboration avec des scientifiques de laboratoire, des mathématiciens, des biologistes, des spécialistes en TI et des cliniciens, j'agis comme un pont pour faciliter la communication et l'intégration entre les disciplines.",
                "M'appuyant sur mon expérience et mes publications dans des revues de premier plan, notamment Nature Genetics, Nature Methods et Cell, je m'engage à traduire des données complexes en informations stratégiques qui font progresser la médecine personnalisée, la découverte de médicaments et la santé de précision."
            ]
        }
    }
}


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
    # Get the language from the URL query, defaulting to 'en'
    lang = request.args.get('lang', 'en')
    # Select the correct dictionary of translations, defaulting to English if lang is invalid
    text_content = INDEX_PAGE_TRANSLATIONS.get(lang, INDEX_PAGE_TRANSLATIONS['en'])
    
    # Render the single index.html template, passing the language and text content
    return render_template('index.html', lang=lang, text=text_content)

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