"""Test OpenAQ API v3 connection and parameters."""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAQ_API_KEY')
print(f"API Key found: {bool(api_key)}")
print(f"API Key length: {len(api_key) if api_key else 0}\n")

headers = {
    'X-API-Key': api_key,
    'Accept': 'application/json'
}

# Test 1: Simple locations endpoint without parameters
print("Test 1: GET /v3/locations (no params)")
url = 'https://api.openaq.org/v3/locations'
response = requests.get(url, headers=headers, params={'limit': 5})
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text[:500]}")
else:
    data = response.json()
    print(f"Results: {len(data.get('results', []))} locations found")
print()

# Test 2: Locations with coordinates
print("Test 2: GET /v3/locations with coordinates")
url = 'https://api.openaq.org/v3/locations'
params = {
    'coordinates': '52.5200,13.4050',
    'radius': 20000,
    'limit': 5
}
response = requests.get(url, headers=headers, params=params)
print(f"Status: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.text[:500]}")
else:
    data = response.json()
    print(f"Results: {len(data.get('results', []))} locations found")
    if data.get('results'):
        print(f"First location: {data['results'][0]}")
print()

# Test 3: Check available parameters endpoint
print("Test 3: GET /v3/parameters")
url = 'https://api.openaq.org/v3/parameters'
response = requests.get(url, headers=headers, params={'limit': 10})
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Available parameters: {[p.get('id') for p in data.get('results', [])]}")
else:
    print(f"Error: {response.text[:500]}")

