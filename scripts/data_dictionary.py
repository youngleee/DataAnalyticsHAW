"""
Generate data dictionary for the final dataset.
"""
import pandas as pd
from typing import Dict, List
import os

def generate_data_dictionary(df: pd.DataFrame, output_path: str = 'outputs/data_dictionary.md'):
    """
    Generate data dictionary documenting all variables.
    
    Args:
        df: Final merged DataFrame
        output_path: Output file path
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define variable descriptions
    variable_descriptions = {
        # Identifiers
        'city': 'City name',
        'city_key': 'Standardized city identifier (berlin, munich, hamburg, cologne, frankfurt)',
        'datetime': 'Timestamp in CET/CEST timezone',
        'date': 'Date (YYYY-MM-DD)',
        
        # Weather variables
        'temperature': 'Temperature in degrees Celsius (°C)',
        'temp_min': 'Minimum temperature in degrees Celsius (°C)',
        'temp_max': 'Maximum temperature in degrees Celsius (°C)',
        'feels_like': 'Feels like temperature in degrees Celsius (°C)',
        'humidity': 'Relative humidity as percentage (%)',
        'pressure': 'Atmospheric pressure in hectopascals (hPa)',
        'wind_speed': 'Wind speed in meters per second (m/s)',
        'wind_direction': 'Wind direction in degrees (0-360)',
        'clouds': 'Cloud coverage percentage (%)',
        'visibility': 'Visibility in meters (m)',
        'rain_1h': 'Rainfall in last 1 hour in millimeters (mm)',
        'rain_3h': 'Rainfall in last 3 hours in millimeters (mm)',
        'snow_1h': 'Snowfall in last 1 hour in millimeters (mm)',
        'weather_main': 'Main weather condition (e.g., Clear, Clouds, Rain)',
        'weather_description': 'Detailed weather description',
        
        # Air quality variables
        'no2': 'Nitrogen dioxide concentration in micrograms per cubic meter (μg/m³)',
        'pm25': 'PM2.5 (particulate matter < 2.5μm) concentration in micrograms per cubic meter (μg/m³)',
        'pm10': 'PM10 (particulate matter < 10μm) concentration in micrograms per cubic meter (μg/m³)',
        'o3': 'Ozone concentration in micrograms per cubic meter (μg/m³)',
        'co': 'Carbon monoxide concentration in micrograms per cubic meter (μg/m³)',
        'station_code': 'Air quality monitoring station code',
        'station_name': 'Air quality monitoring station name',
        
        # Traffic variables
        'traffic_index': 'Traffic congestion index (0-100, where 100 = maximum congestion)',
        'congestion_level': 'Traffic congestion level (0-1, where 1 = maximum congestion)',
        'current_speed': 'Current traffic speed in km/h',
        'free_flow_speed': 'Free flow speed in km/h',
        'confidence': 'Confidence level of traffic data',
        
        # Time features
        'year': 'Year',
        'month': 'Month (1-12)',
        'day': 'Day of month (1-31)',
        'hour': 'Hour of day (0-23)',
        'day_of_week': 'Day of week (0=Monday, 6=Sunday)',
        'day_of_year': 'Day of year (1-365/366)',
        'week_of_year': 'Week of year (1-52/53)',
        'is_weekend': 'Binary indicator for weekend (1=weekend, 0=weekday)',
        'day_type': 'Day type category (weekday/weekend)',
        'season': 'Season (winter/spring/summer/autumn)',
        'is_holiday': 'Binary indicator for German public holiday (1=holiday, 0=not holiday)',
        
        # Weather categories
        'weather_condition': 'Weather condition category (cold/mild/warm)',
        'heat_index': 'Heat index (feels like temperature considering humidity)',
        'wind_chill': 'Wind chill temperature',
        'temp_range': 'Temperature range (max - min)',
        'pressure_change': 'Change in atmospheric pressure',
        'pressure_change_rate': 'Rate of pressure change per hour',
        
        # Traffic categories
        'traffic_level': 'Traffic level category (low/medium/high)',
        'rush_hour': 'Rush hour indicator (morning/evening/none)',
        
        # Pollution indices
        'pm25_aqi': 'PM2.5 Air Quality Index (US EPA scale)',
        'pm10_aqi': 'PM10 Air Quality Index (US EPA scale)',
        'pollution_index': 'Combined pollution index (normalized 0-1)',
        'pm25_pm10_ratio': 'Ratio of PM2.5 to PM10',
        
        # Interaction terms
        'high_temp_high_traffic': 'Binary indicator for high temperature and high traffic',
        'wind_no2_interaction': 'Interaction term: wind speed × NO2',
        'wind_pm25_interaction': 'Interaction term: wind speed × PM2.5',
        'humidity_temp_interaction': 'Interaction term: humidity × temperature',
        
        # Cyclical encodings
        'hour_sin': 'Cyclical encoding of hour (sine component)',
        'hour_cos': 'Cyclical encoding of hour (cosine component)',
        'day_of_week_sin': 'Cyclical encoding of day of week (sine component)',
        'day_of_week_cos': 'Cyclical encoding of day of week (cosine component)',
        'month_sin': 'Cyclical encoding of month (sine component)',
        'month_cos': 'Cyclical encoding of month (cosine component)',
        
        # Rolling averages
        'no2_rolling_7d': '7-day rolling average of NO2',
        'no2_rolling_30d': '30-day rolling average of NO2',
        'pm25_rolling_7d': '7-day rolling average of PM2.5',
        'pm25_rolling_30d': '30-day rolling average of PM2.5',
        'pm10_rolling_7d': '7-day rolling average of PM10',
        'pm10_rolling_30d': '30-day rolling average of PM10',
        'o3_rolling_7d': '7-day rolling average of O3',
        'o3_rolling_30d': '30-day rolling average of O3',
        'temperature_rolling_7d': '7-day rolling average of temperature',
        'temperature_rolling_30d': '30-day rolling average of temperature',
        'traffic_index_rolling_7d': '7-day rolling average of traffic index',
        'traffic_index_rolling_30d': '30-day rolling average of traffic index',
        
        # Lag features
        'no2_lag_1h': 'NO2 value 1 hour ago',
        'no2_lag_6h': 'NO2 value 6 hours ago',
        'no2_lag_24h': 'NO2 value 24 hours ago',
        'pm25_lag_1h': 'PM2.5 value 1 hour ago',
        'pm25_lag_6h': 'PM2.5 value 6 hours ago',
        'pm25_lag_24h': 'PM2.5 value 24 hours ago',
        'temperature_lag_1h': 'Temperature 1 hour ago',
        'temperature_lag_6h': 'Temperature 6 hours ago',
        'temperature_lag_24h': 'Temperature 24 hours ago',
    }
    
    # Create data dictionary
    dict_data = []
    for col in df.columns:
        description = variable_descriptions.get(col, 'Variable description not available')
        dtype = str(df[col].dtype)
        null_count = df[col].isnull().sum()
        null_pct = (null_count / len(df) * 100).round(2)
        
        if pd.api.types.is_numeric_dtype(df[col]):
            min_val = df[col].min()
            max_val = df[col].max()
            mean_val = df[col].mean()
            value_range = f"{min_val:.2f} to {max_val:.2f} (mean: {mean_val:.2f})"
        else:
            unique_count = df[col].nunique()
            value_range = f"{unique_count} unique values"
        
        dict_data.append({
            'Variable': col,
            'Description': description,
            'Data Type': dtype,
            'Missing Values': f"{null_count} ({null_pct}%)",
            'Value Range/Summary': value_range
        })
    
    dict_df = pd.DataFrame(dict_data)
    
    # Generate markdown
    markdown_content = f"""# Data Dictionary

This document describes all variables in the final merged dataset.

## Dataset Information

- **Total Variables**: {len(df.columns)}
- **Total Records**: {len(df):,}
- **Date Range**: {df['datetime'].min() if 'datetime' in df.columns else 'N/A'} to {df['datetime'].max() if 'datetime' in df.columns else 'N/A'}

## Variables

{dict_df.to_markdown(index=False)}

## Units and Standards

### Temperature
- Unit: Degrees Celsius (°C)
- Standard range: -30°C to 50°C

### Humidity
- Unit: Percentage (%)
- Standard range: 0% to 100%

### Wind Speed
- Unit: Meters per second (m/s)
- Standard range: 0 to 200 m/s

### Atmospheric Pressure
- Unit: Hectopascals (hPa)
- Standard range: 800 to 1100 hPa

### Air Pollutants
- Unit: Micrograms per cubic meter (μg/m³)
- NO2: 0 to 500 μg/m³
- PM2.5: 0 to 500 μg/m³
- PM10: 0 to 1000 μg/m³
- O3: 0 to 500 μg/m³
- CO: 0 to 50,000 μg/m³ (or 0 to 50 mg/m³)

### Traffic Index
- Unit: Index (0-100)
- 0 = No congestion
- 100 = Maximum congestion

## Timezone

All timestamps are in **CET/CEST** (Central European Time / Central European Summer Time).

## Data Sources

1. **Weather Data**: OpenWeatherMap API (or alternative source)
2. **Air Quality Data**: European Environment Agency (EEA)
3. **Traffic Data**: TomTom Traffic Index (or alternative source)

## Notes

- Missing values are documented in the data quality report
- Outliers have been identified and handled according to IQR method
- All units have been standardized during data transformation
- Temporal resolution: Hourly (aligned to hour boundaries)

"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    print(f"Data dictionary saved to {output_path}")

