"""
Collect historical weather data from Meteostat API.

Meteostat provides free access to historical weather data from weather stations worldwide.
No API key required.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from meteostat import Point, Daily, Stations
except ImportError:
    print("ERROR: meteostat package not installed. Please run: pip install meteostat")
    sys.exit(1)

from scripts.utils.config import get_cities, get_date_range, ensure_data_directories
from scripts.utils.helpers import save_dataframe, convert_to_cet

class WeatherCollector:
    """Collect weather data from Meteostat API."""
    
    def __init__(self):
        """Initialize weather collector."""
        self.cities = get_cities()
        
        # Meteostat station IDs for major German cities (will be auto-detected if not specified)
        # You can find station IDs at: https://meteostat.net/en/stations
        self.station_ids = {
            'berlin': None,  # Will auto-detect nearest station
            'munich': None,
            'hamburg': None,
            'cologne': None,
            'frankfurt': None
        }
        
    def find_nearest_station(self, city_key: str) -> Optional[str]:
        """
        Find the nearest weather station to a city.
        
        Args:
            city_key: City key (e.g., 'berlin')
            
        Returns:
            Station ID or None
        """
        city = self.cities[city_key]
        lat = city['lat']
        lon = city['lon']
        
        try:
            # Get nearby stations
            stations = Stations()
            stations = stations.nearby(lat, lon)
            stations = stations.fetch(1)  # Get the nearest station
            
            if not stations.empty:
                station_id = stations.index[0]
                station_name = stations.iloc[0]['name']
                print(f"  Found nearest station for {city['name']}: {station_name} (ID: {station_id})")
                return station_id
            else:
                print(f"  Warning: No nearby station found for {city['name']}")
                return None
        except Exception as e:
            print(f"  Error finding station for {city['name']}: {e}")
            return None
    
    def get_weather_data(self, city_key: str, start_date: datetime, 
                        end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Get historical weather data for a city over a date range.
        
        Args:
            city_key: City key (e.g., 'berlin')
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with weather data or None if error
        """
        city = self.cities[city_key]
        lat = city['lat']
        lon = city['lon']
        
        # Find nearest station if not already cached
        if self.station_ids[city_key] is None:
            self.station_ids[city_key] = self.find_nearest_station(city_key)
        
        station_id = self.station_ids[city_key]
        
        if station_id is None:
            # Use coordinates directly (Meteostat will find nearest station)
            location = Point(lat, lon)
        else:
            # Use specific station
            location = Point(lat, lon, alt=0)  # Can add altitude if known
        
        try:
            # Get daily weather data
            data = Daily(location, start_date, end_date)
            data = data.fetch()
            
            if data.empty:
                print(f"  Warning: No weather data available for {city['name']} from {start_date.date()} to {end_date.date()}")
                return None
            
            # Reset index to get date as column
            data = data.reset_index()
            
            # Add city information
            data['city'] = city['name']
            data['city_key'] = city_key
            data['lat'] = lat
            data['lon'] = lon
            
            # Rename columns to match our standard format
            column_mapping = {
                'time': 'date',
                'tavg': 'temperature',  # Average temperature
                'tmin': 'temp_min',
                'tmax': 'temp_max',
                'prcp': 'precipitation',  # Precipitation in mm
                'wspd': 'wind_speed',  # Wind speed (km/h, will convert to m/s)
                'pres': 'pressure',  # Pressure in hPa
                'rhum': 'humidity'  # Relative humidity (%)
            }
            
            # Rename columns that exist
            for old_col, new_col in column_mapping.items():
                if old_col in data.columns:
                    data = data.rename(columns={old_col: new_col})
            
            # Convert wind speed from km/h to m/s if present
            if 'wind_speed' in data.columns:
                data['wind_speed'] = data['wind_speed'] / 3.6
            
            # Convert date to datetime if it's not already
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                data['datetime'] = data['date']  # For consistency
            
            # Fill missing temperature with average if min/max available
            if 'temperature' not in data.columns or data['temperature'].isna().all():
                if 'temp_min' in data.columns and 'temp_max' in data.columns:
                    data['temperature'] = (data['temp_min'] + data['temp_max']) / 2
            
            return data
            
        except Exception as e:
            print(f"  Error fetching weather data for {city['name']}: {e}")
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
        
        print(f"Collecting weather data from {start_date.date()} to {end_date.date()}")
        print(f"Cities: {', '.join([self.cities[k]['name'] for k in city_keys])}")
        print(f"\nUsing Meteostat API (free historical weather data)")
        print(f"Finding nearest weather stations...\n")
        
        for city_key in city_keys:
            city_name = self.cities[city_key]['name']
            print(f"Fetching weather data for {city_name}...")
            
            weather_df = self.get_weather_data(city_key, start_date, end_date)
            
            if weather_df is not None and not weather_df.empty:
                all_data.append(weather_df)
                print(f"  ✓ Collected {len(weather_df)} days of data for {city_name}")
            else:
                print(f"  ⚠ No data collected for {city_name}")
        
        if not all_data:
            print("\nWarning: No weather data collected!")
            return pd.DataFrame()
        
        df = pd.concat(all_data, ignore_index=True)
        return df
    
    def save_weather_data(self, df: pd.DataFrame, filename: Optional[str] = None):
        """
        Save weather data to file (both CSV and Parquet formats).
        
        Args:
            df: DataFrame with weather data
            filename: Output filename base (auto-generated if None)
        """
        ensure_data_directories()
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"data/raw/weather/weather_data_{timestamp}"
        else:
            # Remove extension if provided
            filename_base = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Save as Parquet (efficient storage)
        parquet_file = f"{filename_base}.parquet"
        save_dataframe(df, parquet_file, format='parquet')
        
        # Save as CSV (easy to view in Excel/text editors)
        csv_file = f"{filename_base}.csv"
        save_dataframe(df, csv_file, format='csv')
        
        print(f"\nWeather data saved:")
        print(f"  CSV (for viewing): {csv_file}")
        print(f"  Parquet (for processing): {parquet_file}")
        print(f"  Total records: {len(df)}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")

def main():
    """Main function for standalone execution."""
    collector = WeatherCollector()
    start_date, end_date = get_date_range()
    
    print("=" * 60)
    print("Meteostat Weather Data Collection")
    print("=" * 60)
    print("\nMeteostat provides free historical weather data.")
    print("No API key required!\n")
    
    df = collector.collect_weather_data(start_date, end_date)
    
    if not df.empty:
        collector.save_weather_data(df)
        print(f"\nSummary:")
        print(f"  Cities: {df['city'].nunique()}")
        print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"  Total records: {len(df)}")
    else:
        print("\nNo data collected. Please check your date range and network connection.")

if __name__ == "__main__":
    main()
