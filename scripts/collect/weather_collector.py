"""
Collect historical weather data from OpenWeatherMap API.

Note: OpenWeatherMap's free tier has limitations on historical data.
For historical data, you may need to use their One Call API 3.0 with history subscription,
or use alternative sources like Meteostat API (free for historical data).
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.utils.config import get_openweathermap_key, get_cities, get_date_range, ensure_data_directories
from scripts.utils.helpers import save_dataframe, convert_to_cet

class WeatherCollector:
    """Collect weather data from OpenWeatherMap API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather collector.
        
        Args:
            api_key: OpenWeatherMap API key (if None, loads from env)
        """
        self.api_key = api_key or get_openweathermap_key()
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.cities = get_cities()
        self.rate_limit_delay = 1  # seconds between requests
        
    def get_historical_weather(self, city_key: str, date: datetime) -> Optional[Dict]:
        """
        Get historical weather data for a specific date.
        
        Note: OpenWeatherMap free tier doesn't provide historical data.
        This method uses the current weather endpoint as a fallback.
        For true historical data, consider using:
        - OpenWeatherMap One Call API 3.0 (paid)
        - Meteostat API (free historical data)
        - Weather Underground API
        
        Args:
            city_key: City key (e.g., 'berlin')
            date: Date to get weather for
            
        Returns:
            Dictionary with weather data or None if error
        """
        city = self.cities[city_key]
        lat = city['lat']
        lon = city['lon']
        
        # For historical data, we need to use timestamp
        # OpenWeatherMap One Call API 3.0 requires paid subscription
        # For now, we'll use current weather as a placeholder
        # You should replace this with actual historical API endpoint
        
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'  # Celsius, meters/second
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant weather data
            weather_data = {
                'city': city['name'],
                'city_key': city_key,
                'date': date.strftime('%Y-%m-%d'),
                'timestamp': convert_to_cet(datetime.now(), tz_aware=False),
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'temp_min': data['main']['temp_min'],
                'temp_max': data['main']['temp_max'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind'].get('speed', 0),
                'wind_direction': data['wind'].get('deg', None),
                'clouds': data['clouds'].get('all', 0),
                'visibility': data.get('visibility', None),
                'weather_main': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description']
            }
            
            # Add rain data if available
            if 'rain' in data:
                weather_data['rain_1h'] = data['rain'].get('1h', 0)
                weather_data['rain_3h'] = data['rain'].get('3h', 0)
            else:
                weather_data['rain_1h'] = 0
                weather_data['rain_3h'] = 0
                
            # Add snow data if available
            if 'snow' in data:
                weather_data['snow_1h'] = data['snow'].get('1h', 0)
            else:
                weather_data['snow_1h'] = 0
            
            return weather_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data for {city['name']} on {date}: {e}")
            return None
        except KeyError as e:
            print(f"Error parsing weather data for {city['name']} on {date}: {e}")
            return None
    
    def collect_weather_data(self, start_date: datetime, end_date: datetime, 
                            city_keys: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Collect weather data for multiple cities over date range.
        
        Args:
            start_date: Start date
            end_date: End date
            city_keys: List of city keys to collect (None = all cities)
            
        Returns:
            DataFrame with weather data
        """
        if city_keys is None:
            city_keys = list(self.cities.keys())
        
        all_data = []
        current_date = start_date
        
        print(f"Collecting weather data from {start_date.date()} to {end_date.date()}")
        print(f"Cities: {', '.join([self.cities[k]['name'] for k in city_keys])}")
        
        total_days = (end_date - start_date).days + 1
        total_requests = total_days * len(city_keys)
        
        request_count = 0
        
        while current_date <= end_date:
            for city_key in city_keys:
                print(f"Fetching weather for {self.cities[city_key]['name']} on {current_date.date()}...")
                
                weather_data = self.get_historical_weather(city_key, current_date)
                
                if weather_data:
                    all_data.append(weather_data)
                
                request_count += 1
                
                # Rate limiting
                if request_count < total_requests:
                    time.sleep(self.rate_limit_delay)
            
            current_date += timedelta(days=1)
        
        if not all_data:
            print("Warning: No weather data collected!")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_data)
        return df
    
    def save_weather_data(self, df: pd.DataFrame, filename: Optional[str] = None):
        """
        Save weather data to file.
        
        Args:
            df: DataFrame with weather data
            filename: Output filename (auto-generated if None)
        """
        ensure_data_directories()
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/raw/weather/weather_data_{timestamp}.parquet"
        
        save_dataframe(df, filename, format='parquet')
        print(f"Weather data saved to {filename}")
        print(f"Total records: {len(df)}")

def main():
    """Main function for standalone execution."""
    collector = WeatherCollector()
    start_date, end_date = get_date_range()
    
    print("=" * 60)
    print("OpenWeatherMap Weather Data Collection")
    print("=" * 60)
    print("\nNOTE: OpenWeatherMap free tier has limited historical data access.")
    print("For true historical data, consider:")
    print("1. OpenWeatherMap One Call API 3.0 (paid subscription)")
    print("2. Meteostat API (free historical weather data)")
    print("3. Weather Underground API")
    print("\nThis script will attempt to collect available data...\n")
    
    df = collector.collect_weather_data(start_date, end_date)
    
    if not df.empty:
        collector.save_weather_data(df)
        print(f"\nSummary:")
        print(f"  Cities: {df['city'].nunique()}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Total records: {len(df)}")
    else:
        print("\nNo data collected. Please check your API key and network connection.")

if __name__ == "__main__":
    main()

