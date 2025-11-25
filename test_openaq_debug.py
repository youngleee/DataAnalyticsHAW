"""Debug OpenAQ API v3 measurements endpoint to see exact error."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAQ_API_KEY')
headers = {
    'X-API-Key': api_key,
    'Accept': 'application/json'
}

# Get location ID
url = 'https://api.openaq.org/v3/locations'
params = {
    'coordinates': '52.5200,13.4050',
    'radius': 20000,
    'limit': 1
}
response = requests.get(url, headers=headers, params=params)
location_id = response.json()['results'][0]['id']
print(f"Location ID: {location_id}")

# Test measurements endpoint with exact parameters from our code
measurements_url = 'https://api.openaq.org/v3/measurements'
params = {
    'locations_id': location_id,
    'parameters_id': 'no2',  # This is what our code uses
    'date_from': '2023-01-01',
    'date_to': '2023-01-08',
    'limit': 10000
}

print(f"\nTesting measurements endpoint with parameters:")
print(f"  locations_id: {params['locations_id']}")
print(f"  parameters_id: {params['parameters_id']}")
print(f"  date_from: {params['date_from']}")
print(f"  date_to: {params['date_to']}")

response = requests.get(measurements_url, headers=headers, params=params)
print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text[:1000]}")

# Try with parameter ID instead
print("\n" + "="*60)
print("Trying with parameter ID (number) instead:")
params['parameters_id'] = 5  # NO2 parameter ID
response = requests.get(measurements_url, headers=headers, params=params)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.text[:1000]}")

