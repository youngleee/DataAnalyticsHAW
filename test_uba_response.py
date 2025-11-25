"""Test UBA API response structure."""
import requests
import json

url = "https://www.umweltbundesamt.de/api/air_data/v2/stations/json"
params = {
    'use': 'airquality',
    'lang': 'en',
    'date_from': '2024-01-01',
    'time_from': '1',
    'date_to': '2024-12-31',
    'time_to': '24'
}

response = requests.get(url, params=params, timeout=60)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse type: {type(data)}")
    print(f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    if isinstance(data, dict) and 'data' in data:
        stations_data = data['data']
        print(f"\nStations data type: {type(stations_data)}")
        
        if isinstance(stations_data, dict):
            print(f"Number of stations: {len(stations_data)}")
            # Get first station to see structure
            first_key = list(stations_data.keys())[0]
            first_station = stations_data[first_key]
            print(f"\nFirst station ID: {first_key}")
            print(f"First station type: {type(first_station)}")
            print(f"First station structure: {first_station}")
        elif isinstance(stations_data, list):
            print(f"Number of stations: {len(stations_data)}")
            if stations_data:
                print(f"\nFirst station: {stations_data[0]}")
    
    # Save sample to file
    with open('uba_response_sample.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nSample saved to 'uba_response_sample.json'")
else:
    print(f"Error: {response.text[:500]}")

