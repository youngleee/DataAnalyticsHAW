# Where to Get UBA Station Names and IDs

## Method 1: Using the Python Script (Recommended)

Run the provided script to get all stations:

```bash
python get_uba_stations.py
```

This will:
- Fetch all 439 UBA stations from the API
- Filter stations by city (Berlin, Munich, Hamburg, Cologne, Frankfurt)
- Display station IDs, codes, names, and coordinates
- Save results to JSON files:
  - `uba_stations_by_city.json` - Stations organized by city
  - `uba_all_stations.json` - All 439 stations

### Example Output:
```
BERLIN
  ID:    145 | Code:    DEBE034 | Berlin Neukölln
        City: Berlin | Coordinates: 52.4895, 13.4308
  ID:    175 | Code:    DEBE068 | Berlin Mitte
        City: Berlin | Coordinates: 52.5136, 13.4188
```

## Method 2: UBA Web Portal

1. Visit: https://luftdaten.umweltbundesamt.de/en
2. Click on a city (e.g., "Berlin")
3. Click "CSV Export" or view station details
4. The station number/ID is visible in the URL or CSV file

## Method 3: Direct API Query

Query the UBA stations API directly:

```bash
curl "https://www.umweltbundesamt.de/api/air_data/v2/stations/json?use=airquality&lang=en&date_from=2024-01-01&time_from=1&date_to=2024-12-31&time_to=24"
```

The response includes:
- Station IDs (keys in the `data` object)
- Station information as arrays with:
  - [0] Station ID
  - [1] Station Code (e.g., "DEBE034")
  - [2] Station Name (e.g., "Berlin Neukölln")
  - [3] City Name
  - [7] Longitude
  - [8] Latitude

## Method 4: Check Generated JSON Files

After running `get_uba_stations.py`, check:

- **`uba_stations_by_city.json`** - Easy to read, organized by city
- **`uba_all_stations.json`** - Complete list of all 439 stations

## Station Data Structure

Each station has:
- **Station ID**: Numeric ID used in API queries (e.g., `145`)
- **Station Code**: Official code (e.g., `DEBE034`)
- **Station Name**: Full name (e.g., `Berlin Neukölln`)
- **City**: City name
- **Coordinates**: Latitude and longitude

## Using Station IDs in API Queries

Once you have station IDs, use them in measurements queries:

```python
# Example: Get NO2 data for Berlin Neukölln (station 145)
url = "https://www.umweltbundesamt.de/api/air_data/v2/airquality/json"
params = {
    'station': '145',
    'component': 'NO2',
    'date_from': '2024-01-01',
    'time_from': '1',
    'date_to': '2024-01-02',
    'time_to': '24'
}
```

## Quick Reference: Major Cities Station Counts

- **Berlin**: 18 stations
- **Hamburg**: 15 stations  
- **Munich**: 5 stations
- **Cologne**: 4 stations
- **Frankfurt**: 6 stations (includes Frankfurt am Main and Frankfurt Oder)

## Tips

1. **Station IDs are numeric strings**: Use `'145'` not `145` in API calls
2. **Multiple stations per city**: Each city has multiple monitoring stations
3. **Station codes are unique**: Format like `DEBE034` (DE = Germany, BE = Berlin, 034 = station number)
4. **Coordinates available**: Use coordinates to find nearest stations to specific locations

## Need Help?

- Check the generated JSON files for complete station lists
- Visit UBA portal: https://luftdaten.umweltbundesamt.de/en
- Review API documentation in the response `indices` field for field meanings

