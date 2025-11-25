"""Test OpenAQ API v3 measurements endpoint."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAQ_API_KEY')
headers = {
    'X-API-Key': api_key,
    'Accept': 'application/json'
}

# First, get a location ID
print("Step 1: Get location ID for Berlin")
url = 'https://api.openaq.org/v3/locations'
params = {
    'coordinates': '52.5200,13.4050',
    'radius': 20000,
    'limit': 1
}
response = requests.get(url, headers=headers, params=params)
if response.status_code == 200:
    data = response.json()
    if data.get('results'):
        location_id = data['results'][0]['id']
        print(f"Location ID: {location_id}")
        print(f"Location: {data['results'][0]['name']}")
        
        # Check what parameters are available
        sensors = data['results'][0].get('sensors', [])
        print(f"\nAvailable parameters:")
        for sensor in sensors:
            param = sensor.get('parameter', {})
            print(f"  - {param.get('name')} (ID: {param.get('id')})")
        
        # Test measurements endpoint
        print(f"\nStep 2: Get measurements for location {location_id}")
        measurements_url = 'https://api.openaq.org/v3/measurements'
        
        # Try with parameter ID (number)
        print("\nTest A: Using parameter ID (number)")
        params = {
            'locations_id': location_id,
            'parameters_id': 5,  # NO2
            'date_from': '2023-01-01',
            'date_to': '2023-01-02',
            'limit': 10
        }
        response = requests.get(measurements_url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text[:500]}")
        else:
            data = response.json()
            print(f"Results: {len(data.get('results', []))} measurements found")
            if data.get('results'):
                print(f"Sample: {data['results'][0]}")
        
        # Try with parameter name (string)
        print("\nTest B: Using parameter name (string)")
        params = {
            'locations_id': location_id,
            'parameters_id': 'no2',  # NO2 as string
            'date_from': '2023-01-01',
            'date_to': '2023-01-02',
            'limit': 10
        }
        response = requests.get(measurements_url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text[:500]}")
        else:
            data = response.json()
            print(f"Results: {len(data.get('results', []))} measurements found")
        
        # Check the actual error from our current code
        print("\nTest C: Using countries_id parameter (current code)")
        params = {
            'locations_id': location_id,
            'parameters_id': 5,
            'date_from': '2023-01-01',
            'date_to': '2023-01-02',
            'countries_id': 'DE',  # This might be the issue
            'limit': 10
        }
        response = requests.get(measurements_url, headers=headers, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text[:500]}")
    else:
        print("No locations found")
else:
    print(f"Error getting locations: {response.status_code}")
    print(response.text[:500])

