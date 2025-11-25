"""Test UBA API measurements response format."""
import requests
import json

# Test with a known station (Berlin Neukölln - ID 145)
url = "https://www.umweltbundesamt.de/api/air_data/v2/airquality/json"
params = {
    'station': '145',
    'component': 'NO2',
    'date_from': '2024-01-01',
    'time_from': '1',
    'date_to': '2024-01-02',
    'time_to': '24',
    'lang': 'en'
}

print("Testing UBA measurements API...")
print(f"URL: {url}")
print(f"Params: {params}\n")

response = requests.get(url, params=params, timeout=60)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse type: {type(data)}")
    print(f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    
    if isinstance(data, dict):
        if 'data' in data:
            measurements = data['data']
            print(f"\nMeasurements type: {type(measurements)}")
            print(f"Number of measurements: {len(measurements) if isinstance(measurements, (list, dict)) else 'N/A'}")
            
            if isinstance(measurements, list):
                print(f"\nFirst measurement (list): {measurements[0] if measurements else 'Empty'}")
            elif isinstance(measurements, dict):
                print(f"\nFirst measurement (dict): {list(measurements.items())[0] if measurements else 'Empty'}")
            else:
                print(f"\nMeasurements: {measurements}")
        
        # Check for other keys
        for key in data.keys():
            if key != 'data':
                print(f"\n{key}: {str(data[key])[:200]}")
    
    # Save sample
    with open('uba_measurements_sample.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("\nSample saved to 'uba_measurements_sample.json'")
else:
    print(f"\nError: {response.status_code}")
    print(f"Response: {response.text[:500]}")

