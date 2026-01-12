# API Documentation

This document provides comprehensive information about all APIs used in this project, their data formats, and how to use them.

---

## Table of Contents

1. [Air Quality Data - UBA API](#1-air-quality-data---uba-api)
2. [Weather Data - Meteostat API](#2-weather-data---meteostat-api)
3. [Traffic Data - TomTom API](#3-traffic-data---tomtom-api)
4. [Data Format Standards](#4-data-format-standards)
5. [Quick Reference](#5-quick-reference)

---

## 1. Air Quality Data - UBA API

### Overview

**Umweltbundesamt (UBA) API** is the official German government source for air quality data. It provides free, automated access to air quality measurements from over 400 monitoring stations across Germany.

- **Status**: ✅ Active and Working
- **API Key Required**: ❌ No (Free, no registration needed)
- **Official Source**: German Federal Environment Agency
- **Documentation**: https://luftqualitaet.api.bund.dev/
- **Main Portal**: https://luftdaten.umweltbundesamt.de/en

### API Endpoints

#### Base URL
```
https://www.umweltbundesamt.de/api/air_data/v2 
```

#### Key Endpoints

1. **Get Stations List**
   ```
   GET /stations/json
   ```
   - Parameters:
     - `use=airquality` (required)
     - `lang=en` (language)
     - `date_from=YYYY-MM-DD` (start date)
     - `time_from=1` (hour 1 = 00:00-00:59)
     - `date_to=YYYY-MM-DD` (end date)
     - `time_to=24` (hour 24 = 23:00-23:59)

2. **Get Air Quality Measurements**
   ```
   GET /airquality/json
   ```
   - Parameters:
     - `station=<station_id>` (required)
     - `component=<pollutant>` (NO2, PM10, O3, PM2.5, CO)
     - `date_from=YYYY-MM-DD` (required)
     - `time_from=1` (hour 1 = 00:00-00:59)
     - `date_to=YYYY-MM-DD` (required)
     - `time_to=24` (hour 24 = 23:00-23:59)
     - `lang=en` (optional)

### Supported Pollutants

| Pollutant | Code | Unit | Description |
|-----------|------|------|-------------|
| Nitrogen Dioxide | NO2 | µg/m³ | Traffic-related pollutant |
| Particulate Matter 10 | PM10 | µg/m³ | Coarse particles |
| Ozone | O3 | µg/m³ | Ground-level ozone |
| Particulate Matter 2.5 | PM2.5 | µg/m³ | Fine particles (limited availability) |
| Carbon Monoxide | CO | µg/m³ | Limited availability |

**Note**: We currently collect **NO2, PM10, and O3** as these are the most reliably available pollutants across all stations.

### Data Collection Process

1. **Station Discovery**: Automatically finds all stations for each city
2. **Pollutant Collection**: Queries each station for each pollutant
3. **Data Aggregation**: Combines data from multiple stations per city
4. **Pivoting**: Transforms data from long format (one row per measurement) to wide format (pollutants as columns)

### Example API Request

```python
import requests

url = "https://www.umweltbundesamt.de/api/air_data/v2/airquality/json"
params = {
    'station': '158',  # Berlin Buch station
    'component': 'NO2',
    'date_from': '2024-01-01',
    'time_from': '1',
    'date_to': '2024-01-08',
    'time_to': '24',
    'lang': 'en'
}

response = requests.get(url, params=params)
data = response.json()
```

### Response Structure

The UBA API returns data in a nested dictionary structure:

```json
{
  "data": {
    "158": {
      "2024-01-01 01:00:00": [
        "2024-01-01 01:59:59",
        1,
        0,
        [1, 20, 0, "1"],      // PM10: [component_id, value, quality_flag, normalized_value]
        [3, 21, 0, "0.35"],   // O3: [component_id, value, quality_flag, normalized_value]
        [5, 27, 1, "1.316"]   // NO2: [component_id, value, quality_flag, normalized_value]
      ]
    }
  }
}
```

**Component ID Mapping**:
- `1` = PM10
- `2` = PM2.5
- `3` = O3
- `4` = CO
- `5` = NO2

### Output Data Format

**CSV/Parquet Structure**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `city` | string | City name | "Berlin" |
| `city_key` | string | City identifier | "berlin" |
| `datetime` | datetime | Measurement timestamp | "2024-01-01 00:00:00" |
| `date` | date | Date only | "2024-01-01" |
| `hour` | integer | Hour of day (0-23) | 0 |
| `station_name` | string | Station name | "Berlin Buch" |
| `station_id` | integer | Station ID | 158 |
| `no2` | float | NO2 concentration (µg/m³) | 27.0 |
| `pm10` | float | PM10 concentration (µg/m³) | 20.0 |
| `o3` | float | O3 concentration (µg/m³) | 21.0 |

**Note**: Missing values are represented as `NaN` in the CSV.

### Usage Example

```python
from scripts.collect.air_quality_collector import AirQualityCollector
from datetime import datetime

collector = AirQualityCollector()
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 8)

# Collect data for all cities
df = collector.collect_air_quality_data(start_date, end_date)

# Collect for specific cities
df = collector.collect_air_quality_data(
    start_date, 
    end_date, 
    city_keys=['berlin', 'munich']
)

# Save to file
collector.save_air_quality_data(df)
```

### Rate Limiting

- **Recommended**: 0.5 second delay between requests
- **No official limit**: But be respectful of server resources
- **Best practice**: Process stations sequentially with small delays

---

## 2. Weather Data - Meteostat API

### Overview

**Meteostat** provides free access to historical weather data from weather stations worldwide. It aggregates data from various meteorological services.

- **Status**: ✅ Active and Working
- **API Key Required**: ❌ No (Free, no registration needed)
- **Documentation**: https://dev.meteostat.net/
- **Python Package**: `meteostat` (install via `pip install meteostat`)

### Data Sources

Meteostat aggregates data from:
- National Oceanic and Atmospheric Administration (NOAA)
- Deutscher Wetterdienst (DWD) - German Weather Service
- Other national meteorological services

### Available Data Fields

| Field | Unit | Description |
|-------|------|-------------|
| `temperature` | °C | Average daily temperature |
| `temp_min` | °C | Minimum daily temperature |
| `temp_max` | °C | Maximum daily temperature |
| `precipitation` | mm | Total daily precipitation |
| `snow` | mm | Snow depth |
| `wdir` | degrees | Wind direction (0-360°) |
| `wind_speed` | km/h | Average wind speed |
| `wpgt` | km/h | Peak wind gust |
| `pressure` | hPa | Sea-level pressure |
| `tsun` | minutes | Total sunshine duration |

### Station Discovery

The collector automatically finds the nearest weather station to each city using coordinates:

```python
from meteostat import Point, Stations

# Find nearest station to Berlin
location = Point(52.52, 13.405)  # Berlin coordinates
stations = Stations()
stations = stations.nearby(location.latitude, location.longitude)
station = stations.fetch(1)  # Get nearest station
```

### Data Collection Process

1. **Station Discovery**: Finds nearest weather station to city coordinates
2. **Data Retrieval**: Fetches daily historical data for date range
3. **Data Standardization**: Adds city information and standardizes column names
4. **Time Zone Conversion**: Converts to CET (Central European Time)

### Output Data Format

**CSV/Parquet Structure**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | date | Date | "2024-01-01" |
| `temperature` | float | Average temperature (°C) | 14.8 |
| `temp_min` | float | Minimum temperature (°C) | 10.8 |
| `temp_max` | float | Maximum temperature (°C) | 16.5 |
| `precipitation` | float | Precipitation (mm) | 0.0 |
| `snow` | float | Snow depth (mm) | 0.0 |
| `wdir` | float | Wind direction (degrees) | 180.0 |
| `wind_speed` | float | Wind speed (km/h) | 4.69 |
| `wpgt` | float | Peak wind gust (km/h) | 49.0 |
| `pressure` | float | Sea-level pressure (hPa) | 1015.3 |
| `tsun` | float | Sunshine duration (minutes) | 105.0 |
| `city` | string | City name | "Berlin" |
| `city_key` | string | City identifier | "berlin" |
| `lat` | float | Latitude | 52.52 |
| `lon` | float | Longitude | 13.405 |
| `datetime` | datetime | Date as datetime | "2024-01-01 00:00:00" |

### Usage Example

```python
from scripts.collect.weather_collector import WeatherCollector
from datetime import datetime

collector = WeatherCollector()
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 8)

# Collect data for all cities
df = collector.collect_weather_data(start_date, end_date)

# Collect for specific cities
df = collector.collect_weather_data(
    start_date, 
    end_date, 
    city_keys=['berlin', 'munich']
)

# Save to file
collector.save_weather_data(df)
```

### Data Availability

- **Historical Data**: Available from ~1950s to present (varies by station)
- **Update Frequency**: Daily (data typically available 1-2 days after measurement)
- **Coverage**: Global, with best coverage in developed countries

### Limitations

- Some fields may be missing for older dates or certain stations
- Data quality varies by station and time period
- Real-time data requires different endpoints (not used in this project)

---

## 3. Traffic Data - TomTom API

### Overview

**TomTom Traffic API** provides real-time and historical traffic congestion data. However, access to historical data typically requires a paid subscription.

- **Status**: ⚠️ Limited (Synthetic data used as fallback)
- **API Key Required**: ✅ Yes (for real data)
- **Registration**: https://developer.tomtom.com/
- **Fallback**: Synthetic data generation (used by default)

### API Endpoints

#### Base URL
```
https://api.tomtom.com
```

#### Traffic Flow API
```
GET /traffic/services/4/flowSegmentData/absolute/{format}
```
- Requires coordinates and zoom level
- Provides real-time traffic flow data
- Historical data requires subscription

### Synthetic Data Generation

When TomTom API is unavailable or no API key is provided, the system generates realistic synthetic traffic data based on:

1. **Day of Week Patterns**:
   - Weekdays: Higher congestion during rush hours
   - Weekends: Generally lower congestion

2. **Time of Day Patterns**:
   - Morning rush: 7:00-9:00 AM
   - Evening rush: 5:00-7:00 PM
   - Night: Minimal congestion

3. **City-Specific Baselines**:
   - Each city has a baseline traffic index
   - Larger cities typically have higher baseline congestion

4. **Random Variation**:
   - Adds realistic day-to-day variation
   - Simulates weather impact, events, etc.

### Output Data Format

**CSV/Parquet Structure**:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `city` | string | City name | "Berlin" |
| `city_key` | string | City identifier | "berlin" |
| `date` | date | Date | "2024-01-01" |
| `timestamp` | datetime | Collection timestamp | "2024-01-01 12:00:00" |
| `lat` | float | Latitude | 52.52 |
| `lon` | float | Longitude | 13.405 |
| `current_speed` | integer | Current speed (km/h) | 20 |
| `free_flow_speed` | integer | Free flow speed (km/h) | 20 |
| `confidence` | integer | Data confidence (0-1) | 1 |
| `congestion_level` | float | Congestion level (0-1) | 0.0 |
| `traffic_index` | float | Traffic index (0-100) | 0.0 |
| `data_source` | string | Source identifier | "synthetic" |

### Traffic Metrics Explained

- **Current Speed**: Actual average speed on roads (km/h)
- **Free Flow Speed**: Speed when there's no congestion (km/h)
- **Congestion Level**: Ratio of speed reduction (0 = no congestion, 1 = complete standstill)
  - Formula: `(free_flow_speed - current_speed) / free_flow_speed`
- **Traffic Index**: Overall traffic congestion score (0-100)
  - 0-20: Free flow
  - 21-40: Light congestion
  - 41-60: Moderate congestion
  - 61-80: Heavy congestion
  - 81-100: Severe congestion

### Usage Example

```python
from scripts.collect.traffic_collector import TrafficCollector
from datetime import datetime

collector = TrafficCollector()  # Uses synthetic data by default
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 8)

# Try real data first, fallback to synthetic
df = collector.collect_traffic_data(start_date, end_date, use_synthetic=False)

# Force synthetic data
df = collector.collect_traffic_data(start_date, end_date, use_synthetic=True)

# Save to file
collector.save_traffic_data(df)
```

### Using Real TomTom Data

To use real TomTom data:

1. **Register for API Key**:
   - Visit: https://developer.tomtom.com/
   - Create account and get API key

2. **Add to `.env` file**:
   ```
   TOMTOM_API_KEY=your_api_key_here
   ```

3. **Note**: Historical data typically requires a paid subscription. The free tier usually only provides real-time data.

---

## 4. Data Format Standards

### Common Columns Across All Datasets

All datasets include these common columns for easy merging:

| Column | Type | Description |
|--------|------|-------------|
| `city` | string | City name (standardized) |
| `city_key` | string | City identifier (lowercase, no spaces) |
| `date` | date | Date (YYYY-MM-DD format) |
| `datetime` | datetime | Full timestamp (when applicable) |

### File Naming Convention

All data files follow this naming pattern:

```
<data_type>_data_<YYYYMMDD>_<HHMMSS>.<ext>
```

Examples:
- `air_quality_data_20241126_001315.csv`
- `weather_data_20241125_202252.parquet`
- `traffic_data_20241125_202326.csv`

### File Formats

1. **CSV Format**:
   - UTF-8 encoding
   - Comma-separated values
   - Header row included
   - Missing values as empty or `NaN`

2. **Parquet Format**:
   - Binary columnar format
   - Preserves data types
   - More efficient for large datasets
   - Used for data processing pipeline

### Data Storage Locations

```
data/
├── raw/
│   ├── air_quality/     # UBA API data
│   ├── weather/         # Meteostat API data
│   └── traffic/         # TomTom/synthetic data
└── processed/           # Cleaned and integrated data
```

### Data Quality Notes

- **Missing Values**: Represented as `NaN` in CSV, `null` in Parquet
- **Data Completeness**: Varies by source and date range
- **Time Zones**: All timestamps converted to CET (Central European Time)
- **Units**: Standardized units across all datasets (metric system)

---

## 5. Quick Reference

### API Summary Table

| Data Type | API | Key Required | Status | Documentation |
|-----------|-----|--------------|--------|---------------|
| Air Quality | UBA | ❌ No | ✅ Active | https://luftqualitaet.api.bund.dev/ |
| Weather | Meteostat | ❌ No | ✅ Active | https://dev.meteostat.net/ |
| Traffic | TomTom | ✅ Yes* | ⚠️ Limited | https://developer.tomtom.com/ |

*Synthetic data used as fallback (no key needed)

### Collection Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/collect/air_quality_collector.py` | Collect air quality data | `python scripts/collect/air_quality_collector.py` |
| `scripts/collect/weather_collector.py` | Collect weather data | `python scripts/collect/weather_collector.py` |
| `scripts/collect/traffic_collector.py` | Collect traffic data | `python scripts/collect/traffic_collector.py` |
| `scripts/main.py` | Collect all data | `python scripts/main.py` |

### Common Data Collection Patterns

```python
from datetime import datetime
from scripts.collect.air_quality_collector import AirQualityCollector
from scripts.collect.weather_collector import WeatherCollector
from scripts.collect.traffic_collector import TrafficCollector

# Define date range
start_date = datetime(2024, 1, 1)
end_date = datetime(2024, 1, 8)

# Collect air quality
aq_collector = AirQualityCollector()
aq_df = aq_collector.collect_air_quality_data(start_date, end_date)
aq_collector.save_air_quality_data(aq_df)

# Collect weather
weather_collector = WeatherCollector()
weather_df = weather_collector.collect_weather_data(start_date, end_date)
weather_collector.save_weather_data(weather_df)

# Collect traffic
traffic_collector = TrafficCollector()
traffic_df = traffic_collector.collect_traffic_data(start_date, end_date, use_synthetic=True)
traffic_collector.save_traffic_data(traffic_df)
```

### Troubleshooting

#### Air Quality Data Issues

**Problem**: No data returned
- **Solution**: Check date range (data may not be available for very recent dates)
- **Solution**: Verify station IDs are correct
- **Solution**: Check API endpoint is accessible

**Problem**: Missing pollutants
- **Solution**: Some stations don't measure all pollutants
- **Solution**: Check which pollutants are available for your date range

#### Weather Data Issues

**Problem**: Missing weather station
- **Solution**: System auto-detects nearest station, but may fail for remote locations
- **Solution**: Manually specify station ID in `weather_collector.py`

**Problem**: Missing data fields
- **Solution**: Some fields may not be available for older dates
- **Solution**: Check station data availability at https://meteostat.net/en/stations

#### Traffic Data Issues

**Problem**: Only synthetic data available
- **Solution**: This is expected if no TomTom API key is provided
- **Solution**: Synthetic data is realistic and suitable for analysis
- **Solution**: For real data, register at https://developer.tomtom.com/

---

## Additional Resources

- **UBA API Documentation**: https://luftqualitaet.api.bund.dev/
- **Meteostat Documentation**: https://dev.meteostat.net/
- **TomTom Developer Portal**: https://developer.tomtom.com/
- **Project Repository**: See `README.md` for project setup and usage

---

**Last Updated**: November 2024  
**Maintained By**: DataAnalyticsHAW Team

