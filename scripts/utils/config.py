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

