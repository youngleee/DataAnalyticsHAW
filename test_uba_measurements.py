"""Test UBA API measurements endpoint to see response format."""
import requests
import json

# Test with a known station (Berlin Neukölln - ID 145)
url = "https://www.umweltbundesamt.de/api/air_data/v2/airquality/json"
params = {
    'station': '145',
    'component': 'NO2',
    'date_from': '2023-01-01',
    'time_from': '1',
    'date_to': '2023-01-02',
    'time_to': '24',
    'lang': 'en'
}

print("Testing UBA measurements API...")
print(f"URL: {url}")
print(f"Params: {params}\n")

response = requests.get(url, params=params, timeout=60)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse type: {type(data)}")
    print(f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    if isinstance(data, dict):
        if 'data' in data:
            measurements = data['data']
            print(f"\nMeasurements type: {type(measurements)}")
            print(f"Number of measurements: {len(measurements) if isinstance(measurements, (list, dict)) else 'N/A'}")
            
            if isinstance(measurements, list) and measurements:
                print(f"\nFirst measurement type: {type(measurements[0])}")
                print(f"First measurement: {measurements[0]}")
            elif isinstance(measurements, dict):
                first_key = list(measurements.keys())[0]
                print(f"\nFirst measurement key: {first_key}")
                print(f"First measurement value: {measurements[first_key]}")
    
    # Save sample
    with open('uba_measurements_sample.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nSample saved to 'uba_measurements_sample.json'")
else:
    print(f"Error: {response.text[:500]}")

