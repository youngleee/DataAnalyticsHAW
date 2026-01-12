"""
Configuration loader for API keys and project settings.
"""
import os
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, Tuple

# Load environment variables
load_dotenv()

# City mappings with coordinates and name variations
CITIES = {
    'berlin': {
        'name': 'Berlin',
        'name_variations': ['Berlin', 'BERLIN'],
        'lat': 52.5200,
        'lon': 13.4050,
        'eea_name': 'Berlin'
    },
    'munich': {
        'name': 'Munich',
        'name_variations': ['Munich', 'München', 'MUNICH', 'MÜNCHEN'],
        'lat': 48.1351,
        'lon': 11.5820,
        'eea_name': 'München'
    },
    'hamburg': {
        'name': 'Hamburg',
        'name_variations': ['Hamburg', 'HAMBURG'],
        'lat': 53.5511,
        'lon': 10.0000,
        'eea_name': 'Hamburg'
    },
    'cologne': {
        'name': 'Cologne',
        'name_variations': ['Cologne', 'Köln', 'COLOGNE', 'KÖLN'],
        'lat': 50.9375,
        'lon': 6.9603,
        'eea_name': 'Köln'
    },
    'frankfurt': {
        'name': 'Frankfurt am Main',
        'name_variations': ['Frankfurt', 'Frankfurt am Main', 'FRANKFURT'],
        'lat': 50.1109,
        'lon': 8.6821,
        'eea_name': 'Frankfurt am Main'
    },
    'stuttgart': {
        'name': 'Stuttgart',
        'name_variations': ['Stuttgart', 'STUTTGART'],
        'lat': 48.7758,
        'lon': 9.1829,
        'eea_name': 'Stuttgart'
    },
    'dusseldorf': {
        'name': 'Düsseldorf',
        'name_variations': ['Düsseldorf', 'Dusseldorf', 'DÜSSELDORF', 'DUSSELDORF'],
        'lat': 51.2277,
        'lon': 6.7735,
        'eea_name': 'Düsseldorf'
    },
    'dortmund': {
        'name': 'Dortmund',
        'name_variations': ['Dortmund', 'DORTMUND'],
        'lat': 51.5136,
        'lon': 7.4653,
        'eea_name': 'Dortmund'
    },
    'essen': {
        'name': 'Essen',
        'name_variations': ['Essen', 'ESSEN'],
        'lat': 51.4556,
        'lon': 7.0116,
        'eea_name': 'Essen'
    },
    'leipzig': {
        'name': 'Leipzig',
        'name_variations': ['Leipzig', 'LEIPZIG'],
        'lat': 51.3397,
        'lon': 12.3731,
        'eea_name': 'Leipzig'
    },
    'bremen': {
        'name': 'Bremen',
        'name_variations': ['Bremen', 'BREMEN'],
        'lat': 53.0793,
        'lon': 8.8017,
        'eea_name': 'Bremen'
    },
    'dresden': {
        'name': 'Dresden',
        'name_variations': ['Dresden', 'DRESDEN'],
        'lat': 51.0504,
        'lon': 13.7373,
        'eea_name': 'Dresden'
    },
    'hanover': {
        'name': 'Hanover',
        'name_variations': ['Hanover', 'Hannover', 'HANOVER', 'HANNOVER'],
        'lat': 52.3759,
        'lon': 9.7320,
        'eea_name': 'Hannover'
    },
    'nuremberg': {
        'name': 'Nuremberg',
        'name_variations': ['Nuremberg', 'Nürnberg', 'NUREMBERG', 'NÜRNBERG'],
        'lat': 49.4521,
        'lon': 11.0767,
        'eea_name': 'Nürnberg'
    },
    'duisburg': {
        'name': 'Duisburg',
        'name_variations': ['Duisburg', 'DUISBURG'],
        'lat': 51.4344,
        'lon': 6.7623,
        'eea_name': 'Duisburg'
    },
    'bochum': {
        'name': 'Bochum',
        'name_variations': ['Bochum', 'BOCHUM'],
        'lat': 51.4818,
        'lon': 7.2162,
        'eea_name': 'Bochum'
    },
    'wuppertal': {
        'name': 'Wuppertal',
        'name_variations': ['Wuppertal', 'WUPPERTAL'],
        'lat': 51.2562,
        'lon': 7.1508,
        'eea_name': 'Wuppertal'
    },
    'bielefeld': {
        'name': 'Bielefeld',
        'name_variations': ['Bielefeld', 'BIELEFELD'],
        'lat': 52.0200,
        'lon': 8.5325,
        'eea_name': 'Bielefeld'
    },
    'bonn': {
        'name': 'Bonn',
        'name_variations': ['Bonn', 'BONN'],
        'lat': 50.7374,
        'lon': 7.0982,
        'eea_name': 'Bonn'
    },
    'munster': {
        'name': 'Münster',
        'name_variations': ['Münster', 'Munster', 'MÜNSTER', 'MUNSTER'],
        'lat': 51.9607,
        'lon': 7.6261,
        'eea_name': 'Münster'
    },
    'karlsruhe': {
        'name': 'Karlsruhe',
        'name_variations': ['Karlsruhe', 'KARLSRUHE'],
        'lat': 49.0069,
        'lon': 8.4037,
        'eea_name': 'Karlsruhe'
    },
    'mannheim': {
        'name': 'Mannheim',
        'name_variations': ['Mannheim', 'MANNHEIM'],
        'lat': 49.4875,
        'lon': 8.4660,
        'eea_name': 'Mannheim'
    },
    'augsburg': {
        'name': 'Augsburg',
        'name_variations': ['Augsburg', 'AUGSBURG'],
        'lat': 48.3668,
        'lon': 10.8987,
        'eea_name': 'Augsburg'
    },
    'wiesbaden': {
        'name': 'Wiesbaden',
        'name_variations': ['Wiesbaden', 'WIESBADEN'],
        'lat': 50.0782,
        'lon': 8.2398,
        'eea_name': 'Wiesbaden'
    },
    'gelsenkirchen': {
        'name': 'Gelsenkirchen',
        'name_variations': ['Gelsenkirchen', 'GELSENKIRCHEN'],
        'lat': 51.5177,
        'lon': 7.0857,
        'eea_name': 'Gelsenkirchen'
    },
    'mönchengladbach': {
        'name': 'Mönchengladbach',
        'name_variations': ['Mönchengladbach', 'Moenchengladbach', 'MÖNCHENGLADBACH'],
        'lat': 51.1805,
        'lon': 6.4428,
        'eea_name': 'Mönchengladbach'
    },
    'braunschweig': {
        'name': 'Braunschweig',
        'name_variations': ['Braunschweig', 'BRAUNSCHWEIG'],
        'lat': 52.2689,
        'lon': 10.5268,
        'eea_name': 'Braunschweig'
    },
    'chemnitz': {
        'name': 'Chemnitz',
        'name_variations': ['Chemnitz', 'CHEMNITZ'],
        'lat': 50.8278,
        'lon': 12.9214,
        'eea_name': 'Chemnitz'
    },
    'kiel': {
        'name': 'Kiel',
        'name_variations': ['Kiel', 'KIEL'],
        'lat': 54.3233,
        'lon': 10.1394,
        'eea_name': 'Kiel'
    },
    'aachen': {
        'name': 'Aachen',
        'name_variations': ['Aachen', 'AACHEN'],
        'lat': 50.7753,
        'lon': 6.0839,
        'eea_name': 'Aachen'
    },
    'halle': {
        'name': 'Halle',
        'name_variations': ['Halle', 'Halle (Saale)', 'HALLE'],
        'lat': 51.4826,
        'lon': 11.9692,
        'eea_name': 'Halle'
    },
    'magdeburg': {
        'name': 'Magdeburg',
        'name_variations': ['Magdeburg', 'MAGDEBURG'],
        'lat': 52.1205,
        'lon': 11.6276,
        'eea_name': 'Magdeburg'
    },
    'freiburg': {
        'name': 'Freiburg',
        'name_variations': ['Freiburg', 'Freiburg im Breisgau', 'FREIBURG'],
        'lat': 47.9978,
        'lon': 7.8427,
        'eea_name': 'Freiburg'
    },
    'krefeld': {
        'name': 'Krefeld',
        'name_variations': ['Krefeld', 'KREFELD'],
        'lat': 51.3392,
        'lon': 6.5861,
        'eea_name': 'Krefeld'
    },
    'lübeck': {
        'name': 'Lübeck',
        'name_variations': ['Lübeck', 'Luebeck', 'LÜBECK', 'LUEBECK'],
        'lat': 53.8655,
        'lon': 10.6866,
        'eea_name': 'Lübeck'
    },
    'oberhausen': {
        'name': 'Oberhausen',
        'name_variations': ['Oberhausen', 'OBERHAUSEN'],
        'lat': 51.4730,
        'lon': 6.8807,
        'eea_name': 'Oberhausen'
    },
    'erfurt': {
        'name': 'Erfurt',
        'name_variations': ['Erfurt', 'ERFURT'],
        'lat': 50.9848,
        'lon': 11.0299,
        'eea_name': 'Erfurt'
    },
    'mainz': {
        'name': 'Mainz',
        'name_variations': ['Mainz', 'MAINZ'],
        'lat': 50.0012,
        'lon': 8.2763,
        'eea_name': 'Mainz'
    },
    'rostock': {
        'name': 'Rostock',
        'name_variations': ['Rostock', 'ROSTOCK'],
        'lat': 54.0924,
        'lon': 12.0991,
        'eea_name': 'Rostock'
    },
    'kassel': {
        'name': 'Kassel',
        'name_variations': ['Kassel', 'KASSEL'],
        'lat': 51.3127,
        'lon': 9.4797,
        'eea_name': 'Kassel'
    },
    'hagen': {
        'name': 'Hagen',
        'name_variations': ['Hagen', 'HAGEN'],
        'lat': 51.3671,
        'lon': 7.4633,
        'eea_name': 'Hagen'
    },
    'hamm': {
        'name': 'Hamm',
        'name_variations': ['Hamm', 'HAMM'],
        'lat': 51.6739,
        'lon': 7.8160,
        'eea_name': 'Hamm'
    },
    'saarbrücken': {
        'name': 'Saarbrücken',
        'name_variations': ['Saarbrücken', 'Saarbruecken', 'SAARBRÜCKEN'],
        'lat': 49.2402,
        'lon': 7.0097,
        'eea_name': 'Saarbrücken'
    },
    'mülheim': {
        'name': 'Mülheim an der Ruhr',
        'name_variations': ['Mülheim', 'Muelheim', 'Mülheim an der Ruhr', 'MÜLHEIM'],
        'lat': 51.4314,
        'lon': 6.8807,
        'eea_name': 'Mülheim an der Ruhr'
    },
    'potsdam': {
        'name': 'Potsdam',
        'name_variations': ['Potsdam', 'POTSDAM'],
        'lat': 52.3906,
        'lon': 13.0645,
        'eea_name': 'Potsdam'
    },
    'ludwigshafen': {
        'name': 'Ludwigshafen',
        'name_variations': ['Ludwigshafen', 'Ludwigshafen am Rhein', 'LUDWIGSHAFEN'],
        'lat': 49.4812,
        'lon': 8.4462,
        'eea_name': 'Ludwigshafen'
    },
    'oldenburg': {
        'name': 'Oldenburg',
        'name_variations': ['Oldenburg', 'OLDENBURG'],
        'lat': 53.1435,
        'lon': 8.2146,
        'eea_name': 'Oldenburg'
    },
    'leverkusen': {
        'name': 'Leverkusen',
        'name_variations': ['Leverkusen', 'LEVERKUSEN'],
        'lat': 51.0303,
        'lon': 6.9843,
        'eea_name': 'Leverkusen'
    },
    'osnabrück': {
        'name': 'Osnabrück',
        'name_variations': ['Osnabrück', 'Osnabrueck', 'OSNABRÜCK'],
        'lat': 52.2799,
        'lon': 8.0472,
        'eea_name': 'Osnabrück'
    },
    'solingen': {
        'name': 'Solingen',
        'name_variations': ['Solingen', 'SOLINGEN'],
        'lat': 51.1714,
        'lon': 7.0833,
        'eea_name': 'Solingen'
    },
    'heidelberg': {
        'name': 'Heidelberg',
        'name_variations': ['Heidelberg', 'HEIDELBERG'],
        'lat': 49.3988,
        'lon': 8.6724,
        'eea_name': 'Heidelberg'
    },
    'herne': {
        'name': 'Herne',
        'name_variations': ['Herne', 'HERNE'],
        'lat': 51.5369,
        'lon': 7.2260,
        'eea_name': 'Herne'
    },
    'neuss': {
        'name': 'Neuss',
        'name_variations': ['Neuss', 'NEUSS'],
        'lat': 51.2042,
        'lon': 6.6879,
        'eea_name': 'Neuss'
    },
    'darmstadt': {
        'name': 'Darmstadt',
        'name_variations': ['Darmstadt', 'DARMDTADT'],
        'lat': 49.8728,
        'lon': 8.6512,
        'eea_name': 'Darmstadt'
    },
    'paderborn': {
        'name': 'Paderborn',
        'name_variations': ['Paderborn', 'PADERBORN'],
        'lat': 51.7189,
        'lon': 8.7570,
        'eea_name': 'Paderborn'
    },
    'regensburg': {
        'name': 'Regensburg',
        'name_variations': ['Regensburg', 'REGENSBURG'],
        'lat': 49.0134,
        'lon': 12.1016,
        'eea_name': 'Regensburg'
    },
    'ingolstadt': {
        'name': 'Ingolstadt',
        'name_variations': ['Ingolstadt', 'INGOLSTADT'],
        'lat': 48.7665,
        'lon': 11.4258,
        'eea_name': 'Ingolstadt'
    },
    'würzburg': {
        'name': 'Würzburg',
        'name_variations': ['Würzburg', 'Wuerzburg', 'WÜRZBURG'],
        'lat': 49.7913,
        'lon': 9.9534,
        'eea_name': 'Würzburg'
    },
    'fürth': {
        'name': 'Fürth',
        'name_variations': ['Fürth', 'Fuerth', 'FÜRTH'],
        'lat': 49.4771,
        'lon': 10.9887,
        'eea_name': 'Fürth'
    },
    'wolfsburg': {
        'name': 'Wolfsburg',
        'name_variations': ['Wolfsburg', 'WOLFSBURG'],
        'lat': 52.4226,
        'lon': 10.7865,
        'eea_name': 'Wolfsburg'
    },
    'offenbach': {
        'name': 'Offenbach',
        'name_variations': ['Offenbach', 'Offenbach am Main', 'OFFENBACH'],
        'lat': 50.1036,
        'lon': 8.7660,
        'eea_name': 'Offenbach'
    },
    'ulm': {
        'name': 'Ulm',
        'name_variations': ['Ulm', 'ULM'],
        'lat': 48.4011,
        'lon': 9.9876,
        'eea_name': 'Ulm'
    },
    'heilbronn': {
        'name': 'Heilbronn',
        'name_variations': ['Heilbronn', 'HEILBRONN'],
        'lat': 49.1427,
        'lon': 9.2109,
        'eea_name': 'Heilbronn'
    },
    'pforzheim': {
        'name': 'Pforzheim',
        'name_variations': ['Pforzheim', 'PFORZHEIM'],
        'lat': 48.8932,
        'lon': 8.6919,
        'eea_name': 'Pforzheim'
    },
    'göttingen': {
        'name': 'Göttingen',
        'name_variations': ['Göttingen', 'Goettingen', 'GÖTTINGEN'],
        'lat': 51.5413,
        'lon': 9.9158,
        'eea_name': 'Göttingen'
    },
    'bottrop': {
        'name': 'Bottrop',
        'name_variations': ['Bottrop', 'BOTTROP'],
        'lat': 51.5232,
        'lon': 6.9253,
        'eea_name': 'Bottrop'
    },
    'trier': {
        'name': 'Trier',
        'name_variations': ['Trier', 'TRIER'],
        'lat': 49.7499,
        'lon': 6.6371,
        'eea_name': 'Trier'
    },
    'recklinghausen': {
        'name': 'Recklinghausen',
        'name_variations': ['Recklinghausen', 'RECKLINGHAUSEN'],
        'lat': 51.6144,
        'lon': 7.1979,
        'eea_name': 'Recklinghausen'
    },
    'reutlingen': {
        'name': 'Reutlingen',
        'name_variations': ['Reutlingen', 'REUTLINGEN'],
        'lat': 48.4914,
        'lon': 9.2115,
        'eea_name': 'Reutlingen'
    },
    'bremerhaven': {
        'name': 'Bremerhaven',
        'name_variations': ['Bremerhaven', 'BREMERHAVEN'],
        'lat': 53.5396,
        'lon': 8.5809,
        'eea_name': 'Bremerhaven'
    },
    'koblenz': {
        'name': 'Koblenz',
        'name_variations': ['Koblenz', 'KOBLENZ'],
        'lat': 50.3569,
        'lon': 7.5890,
        'eea_name': 'Koblenz'
    },
    'bergisch_gladbach': {
        'name': 'Bergisch Gladbach',
        'name_variations': ['Bergisch Gladbach', 'BERGISCH GLADBACH'],
        'lat': 50.9916,
        'lon': 7.1233,
        'eea_name': 'Bergisch Gladbach'
    },
    'jena': {
        'name': 'Jena',
        'name_variations': ['Jena', 'JENA'],
        'lat': 50.9271,
        'lon': 11.5862,
        'eea_name': 'Jena'
    },
    'remscheid': {
        'name': 'Remscheid',
        'name_variations': ['Remscheid', 'REMSCHEID'],
        'lat': 51.1784,
        'lon': 7.1997,
        'eea_name': 'Remscheid'
    },
    'erlangen': {
        'name': 'Erlangen',
        'name_variations': ['Erlangen', 'ERLANGEN'],
        'lat': 49.5897,
        'lon': 11.0039,
        'eea_name': 'Erlangen'
    },
    'moers': {
        'name': 'Moers',
        'name_variations': ['Moers', 'MÖRS', 'MOERS'],
        'lat': 51.4514,
        'lon': 6.6314,
        'eea_name': 'Moers'
    },
    'siegen': {
        'name': 'Siegen',
        'name_variations': ['Siegen', 'SIEGEN'],
        'lat': 50.8750,
        'lon': 8.0167,
        'eea_name': 'Siegen'
    },
    'hildesheim': {
        'name': 'Hildesheim',
        'name_variations': ['Hildesheim', 'HILDESHEIM'],
        'lat': 52.1508,
        'lon': 9.9513,
        'eea_name': 'Hildesheim'
    },
    'salzgitter': {
        'name': 'Salzgitter',
        'name_variations': ['Salzgitter', 'SALZGITTER'],
        'lat': 52.1500,
        'lon': 10.3333,
        'eea_name': 'Salzgitter'
    }
}

def get_api_key(key_name: str) -> str:
    """Get API key from environment variables."""
    key = os.getenv(key_name)
    if not key:
        raise ValueError(f"API key {key_name} not found in environment variables. Please set it in .env file.")
    return key

def get_openweathermap_key() -> str:
    """Get OpenWeatherMap API key (deprecated - using Meteostat now)."""
    return os.getenv('OPENWEATHERMAP_API_KEY', '')

def get_tomtom_key() -> str:
    """Get TomTom API key (optional)."""
    return os.getenv('TOMTOM_API_KEY', '')

def get_openaq_key() -> str:
    """Get OpenAQ API key (deprecated - using UBA API now)."""
    return os.getenv('OPENAQ_API_KEY', '')

def get_date_range() -> Tuple[datetime, datetime]:
    """Get start and end dates from environment or use defaults."""
    start_str = os.getenv('START_DATE', '2023-01-01')
    end_str = os.getenv('END_DATE', '2024-12-31')
    
    start_date = datetime.strptime(start_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_str, '%Y-%m-%d')
    
    return start_date, end_date

def get_cities() -> Dict:
    """Get city configuration."""
    return CITIES

def ensure_data_directories():
    """Create necessary data directories if they don't exist."""
    directories = [
        'data/raw/weather',
        'data/raw/air_quality',
        'data/raw/traffic',
        'data/processed',
        'outputs/reports',
        'outputs/datasets'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

