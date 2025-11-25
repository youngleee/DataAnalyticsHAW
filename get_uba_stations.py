"""
Get UBA station names and IDs for German cities.

This script queries the UBA API to get all available stations
and filters them by city name.

Station data structure (array format):
[station_id, station_code, station_name, city, state_code, date_from, date_to, 
 longitude, latitude, ...]
"""
import requests
import json
from typing import Dict, List

def get_all_uba_stations() -> Dict:
    """
    Get all UBA stations from the API.
    
    Returns:
        Dictionary with station data
    """
    url = "https://www.umweltbundesamt.de/api/air_data/v2/stations/json"
    
    params = {
        'use': 'airquality',
        'lang': 'en',
        'date_from': '2024-01-01',
        'time_from': '1',
        'date_to': '2024-12-31',
        'time_to': '24'
    }
    
    print("Fetching stations from UBA API...")
    response = requests.get(url, params=params, timeout=60)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])
        return {}

def parse_station_array(station_id: str, station_array: List) -> Dict:
    """
    Parse station array into a dictionary.
    
    Station array format (based on UBA API):
    [0] station_id (string)
    [1] station_code (e.g., 'DEBB021')
    [2] station_name (e.g., 'Potsdam-Zentrum')
    [3] city (e.g., 'Potsdam')
    [4] state_code (e.g., 'PDBA')
    [5] date_from
    [6] date_to
    [7] longitude
    [8] latitude
    [9-19] additional fields
    """
    if len(station_array) < 9:
        return {}
    
    return {
        'station_id': station_id,
        'station_code': station_array[1] if len(station_array) > 1 else '',
        'station_name': station_array[2] if len(station_array) > 2 else '',
        'city': station_array[3] if len(station_array) > 3 else '',
        'state_code': station_array[4] if len(station_array) > 4 else '',
        'date_from': station_array[5] if len(station_array) > 5 else '',
        'date_to': station_array[6] if len(station_array) > 6 else '',
        'longitude': station_array[7] if len(station_array) > 7 else '',
        'latitude': station_array[8] if len(station_array) > 8 else '',
    }

def filter_stations_by_city(stations_data: Dict, city_name: str) -> List[Dict]:
    """
    Filter stations by city name.
    
    Args:
        stations_data: Full stations data from UBA API
        city_name: City name to filter by
        
    Returns:
        List of station dictionaries
    """
    if 'data' not in stations_data:
        return []
    
    city_stations = []
    city_name_lower = city_name.lower()
    
    for station_id, station_array in stations_data['data'].items():
        # Parse the array structure
        station_info = parse_station_array(station_id, station_array)
        
        if not station_info:
            continue
            
        station_city = station_info.get('city', '').lower()
        
        # Match city name (handles variations)
        if (city_name_lower in station_city or 
            station_city in city_name_lower):
            city_stations.append(station_info)
    
    return city_stations

def print_stations_for_cities():
    """Print stations for major German cities."""
    cities = ['Berlin', 'Munich', 'Hamburg', 'Cologne', 'Frankfurt']
    
    # City name variations
    city_variations = {
        'Munich': ['München', 'Munich'],
        'Cologne': ['Köln', 'Cologne'],
        'Frankfurt': ['Frankfurt am Main', 'Frankfurt']
    }
    
    stations_data = get_all_uba_stations()
    
    if not stations_data:
        print("Failed to fetch stations data.")
        return
    
    print("\n" + "="*80)
    print("UBA Stations by City")
    print("="*80)
    
    all_stations_by_city = {}
    
    for city in cities:
        print(f"\n{city.upper()}")
        print("-" * 80)
        
        # Try main city name
        stations = filter_stations_by_city(stations_data, city)
        
        # Try variations if no results
        if not stations and city in city_variations:
            for variation in city_variations[city]:
                stations = filter_stations_by_city(stations_data, variation)
                if stations:
                    break
        
        all_stations_by_city[city] = stations
        
        if stations:
            for station in stations:
                station_id = station.get('station_id', 'N/A')
                station_name = station.get('station_name', 'N/A')
                station_code = station.get('station_code', 'N/A')
                station_city = station.get('city', 'N/A')
                lat = station.get('latitude', 'N/A')
                lon = station.get('longitude', 'N/A')
                
                print(f"  ID: {station_id:>6} | Code: {station_code:>10} | {station_name}")
                print(f"        City: {station_city} | Coordinates: {lat}, {lon}")
        else:
            print(f"  No stations found for {city}")
    
    # Save filtered stations to JSON
    print("\n" + "="*80)
    print("Saving stations by city to 'uba_stations_by_city.json'...")
    with open('uba_stations_by_city.json', 'w', encoding='utf-8') as f:
        json.dump(all_stations_by_city, f, indent=2, ensure_ascii=False)
    print("Done! Check 'uba_stations_by_city.json' for station data by city.")
    
    # Also save all stations
    print("Saving all stations to 'uba_all_stations.json'...")
    with open('uba_all_stations.json', 'w', encoding='utf-8') as f:
        json.dump(stations_data, f, indent=2, ensure_ascii=False)
    print("Done! Check 'uba_all_stations.json' for all station data.")

if __name__ == "__main__":
    print_stations_for_cities()
