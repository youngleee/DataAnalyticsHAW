"""
Collect traffic data from TomTom Traffic Index or alternative sources.

TomTom provides traffic congestion data, but may require API access.
Alternative: Use publicly available traffic data or web scraping.
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.utils.config import get_cities, get_date_range, get_tomtom_key, ensure_data_directories
from scripts.utils.helpers import save_dataframe, convert_to_cet, standardize_city_name

class TrafficCollector:
    """Collect traffic congestion data."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize traffic collector.
        
        Args:
            api_key: TomTom API key (optional)
        """
        self.api_key = api_key or get_tomtom_key()
        self.base_url = "https://api.tomtom.com"
        self.cities = get_cities()
        
        # TomTom city IDs (these may need to be looked up)
        # You can find city IDs using TomTom's Geocoding API
        self.city_ids = {
            'berlin': '52.5200,13.4050',  # Using coordinates as fallback
            'munich': '48.1351,11.5820',
            'hamburg': '53.5511,10.0000',
            'cologne': '50.9375,6.9603',
            'frankfurt': '50.1109,8.6821'
        }
        
    def get_tomtom_traffic_index(self, city_key: str, date: datetime) -> Optional[Dict]:
        """
        Get TomTom Traffic Index for a city on a specific date.
        
        Note: TomTom Traffic Index API may require:
        1. API key registration
        2. Specific endpoint access
        3. Historical data subscription
        
        Args:
            city_key: City key
            date: Date to get traffic data for
            
        Returns:
            Dictionary with traffic data or None
        """
        if not self.api_key:
            print(f"TomTom API key not provided. Skipping {city_key}.")
            return None
        
        city = self.cities[city_key]
        coords = self.city_ids[city_key]
        lat, lon = coords.split(',')
        
        # TomTom Traffic Flow API endpoint
        # Note: Actual endpoint may vary based on TomTom API version
        url = f"{self.base_url}/traffic/services/4/flowSegmentData/absolute/10/json"
        
        params = {
            'point': f"{lat},{lon}",
            'key': self.api_key,
            'unit': 'KMPH'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract traffic flow data
            # Structure depends on TomTom API response
            traffic_data = {
                'city': city['name'],
                'city_key': city_key,
                'date': date.strftime('%Y-%m-%d'),
                'timestamp': convert_to_cet(datetime.now(), tz_aware=False),
                'lat': float(lat),
                'lon': float(lon)
            }
            
            # Parse TomTom response (structure may vary)
            if 'flowSegmentData' in data:
                flow = data['flowSegmentData']
                traffic_data['current_speed'] = flow.get('currentSpeed', None)
                traffic_data['free_flow_speed'] = flow.get('freeFlowSpeed', None)
                traffic_data['confidence'] = flow.get('confidence', None)
                
                # Calculate congestion level
                if traffic_data['current_speed'] and traffic_data['free_flow_speed']:
                    speed_ratio = traffic_data['current_speed'] / traffic_data['free_flow_speed']
                    traffic_data['congestion_level'] = 1 - speed_ratio  # 0 = no congestion, 1 = max congestion
                    traffic_data['traffic_index'] = (1 - speed_ratio) * 100
                else:
                    traffic_data['congestion_level'] = None
                    traffic_data['traffic_index'] = None
            
            return traffic_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching TomTom data for {city['name']} on {date}: {e}")
            return None
        except (KeyError, ValueError) as e:
            print(f"Error parsing TomTom data for {city['name']} on {date}: {e}")
            return None
    
    def get_traffic_from_alternative_source(self, city_key: str, date: datetime) -> Optional[Dict]:
        """
        Get traffic data from alternative sources.
        
        Alternative sources:
        1. Google Maps Traffic API (requires API key)
        2. HERE Traffic API (requires API key)
        3. OpenStreetMap traffic data
        4. Web scraping from traffic monitoring websites
        
        Args:
            city_key: City key
            date: Date to get traffic data for
            
        Returns:
            Dictionary with traffic data or None
        """
        city = self.cities[city_key]
        
        # Placeholder for alternative data sources
        # You can implement web scraping or use other APIs here
        
        print(f"Alternative traffic source not yet implemented for {city['name']}.")
        return None
    
    def create_synthetic_traffic_data(self, city_key: str, start_date: datetime, 
                                     end_date: datetime) -> pd.DataFrame:
        """
        Create synthetic traffic data based on patterns.
        
        This is a fallback method that generates realistic traffic patterns
        based on day of week, time of day, and seasonal variations.
        Use this only if real traffic data is unavailable.
        
        Args:
            city_key: City key
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with synthetic traffic data
        """
        city = self.cities[city_key]
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        
        traffic_data = []
        
        for dt in dates:
            # Generate traffic index based on patterns
            hour = dt.hour
            day_of_week = dt.weekday()  # 0 = Monday, 6 = Sunday
            
            # Base traffic pattern
            # Rush hours: 7-9 AM and 5-7 PM on weekdays
            if day_of_week < 5:  # Weekday
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    base_traffic = 70 + (hour % 3) * 5  # High traffic
                elif 10 <= hour <= 16:
                    base_traffic = 40 + (hour % 3) * 3  # Medium traffic
                else:
                    base_traffic = 20 + (hour % 3) * 2  # Low traffic
            else:  # Weekend
                if 10 <= hour <= 18:
                    base_traffic = 50 + (hour % 3) * 3  # Medium traffic
                else:
                    base_traffic = 25 + (hour % 3) * 2  # Low traffic
            
            # Add some randomness
            import random
            traffic_index = base_traffic + random.uniform(-5, 5)
            traffic_index = max(0, min(100, traffic_index))  # Clamp to 0-100
            
            traffic_data.append({
                'city': city['name'],
                'city_key': city_key,
                'datetime': dt,
                'date': dt.date(),
                'hour': hour,
                'day_of_week': day_of_week,
                'traffic_index': round(traffic_index, 2),
                'congestion_level': round(traffic_index / 100, 3),
                'data_source': 'synthetic'
            })
        
        return pd.DataFrame(traffic_data)
    
    def collect_traffic_data(self, start_date: datetime, end_date: datetime,
                            city_keys: Optional[List[str]] = None,
                            use_synthetic: bool = False) -> pd.DataFrame:
        """
        Collect traffic data for multiple cities over date range.
        
        Args:
            start_date: Start date
            end_date: End date
            city_keys: List of city keys (None = all cities)
            use_synthetic: Whether to use synthetic data if API fails
            
        Returns:
            DataFrame with traffic data
        """
        if city_keys is None:
            city_keys = list(self.cities.keys())
        
        all_data = []
        
        print(f"Collecting traffic data from {start_date.date()} to {end_date.date()}")
        print(f"Cities: {', '.join([self.cities[k]['name'] for k in city_keys])}")
        
        if use_synthetic:
            print("\nUsing synthetic traffic data (fallback method).")
            for city_key in city_keys:
                print(f"Generating synthetic data for {self.cities[city_key]['name']}...")
                df = self.create_synthetic_traffic_data(city_key, start_date, end_date)
                all_data.append(df)
        else:
            print("\nAttempting to collect real traffic data from TomTom API...")
            current_date = start_date
            
            while current_date <= end_date:
                for city_key in city_keys:
                    print(f"Fetching traffic for {self.cities[city_key]['name']} on {current_date.date()}...")
                    
                    # Try TomTom API first
                    traffic_data = self.get_tomtom_traffic_index(city_key, current_date)
                    
                    if not traffic_data:
                        # Try alternative source
                        traffic_data = self.get_traffic_from_alternative_source(city_key, current_date)
                    
                    if traffic_data:
                        all_data.append(traffic_data)
                    
                    time.sleep(0.5)  # Rate limiting
                
                current_date += timedelta(days=1)
        
        if not all_data:
            print("\nNo traffic data collected. Consider using synthetic data as fallback.")
            return pd.DataFrame()
        
        # Filter out None values and handle both dict and DataFrame inputs
        filtered_data = [d for d in all_data if d is not None]
        
        if not filtered_data:
            print("\nNo valid traffic data collected. Consider using synthetic data as fallback.")
            return pd.DataFrame()
        
        # Check if all items are DataFrames or all are dicts
        if isinstance(filtered_data[0], pd.DataFrame):
            df = pd.concat(filtered_data, ignore_index=True)
        else:
            df = pd.DataFrame(filtered_data)
        return df
    
    def save_traffic_data(self, df: pd.DataFrame, filename: Optional[str] = None):
        """
        Save traffic data to file (both CSV and Parquet formats).
        
        Args:
            df: DataFrame with traffic data
            filename: Output filename base (auto-generated if None)
        """
        ensure_data_directories()
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"data/raw/traffic/traffic_data_{timestamp}"
        else:
            # Remove extension if provided
            filename_base = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Save as Parquet (efficient storage)
        parquet_file = f"{filename_base}.parquet"
        save_dataframe(df, parquet_file, format='parquet')
        
        # Save as CSV (easy to view in Excel/text editors)
        csv_file = f"{filename_base}.csv"
        save_dataframe(df, csv_file, format='csv')
        
        print(f"\nTraffic data saved:")
        print(f"  CSV (for viewing): {csv_file}")
        print(f"  Parquet (for processing): {parquet_file}")
        print(f"  Total records: {len(df)}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")

def main():
    """Main function for standalone execution."""
    collector = TrafficCollector()
    start_date, end_date = get_date_range()
    
    print("=" * 60)
    print("TomTom Traffic Data Collection")
    print("=" * 60)
    print("\nNOTE: TomTom API may require:")
    print("1. API key registration at https://developer.tomtom.com/")
    print("2. Historical data subscription")
    print("3. Specific endpoint access")
    print("\nIf API is unavailable, synthetic data can be generated.\n")
    
    # Try real data first, fallback to synthetic if needed
    df = collector.collect_traffic_data(start_date, end_date, use_synthetic=False)
    
    if df.empty:
        print("\nReal data collection failed. Generating synthetic data...")
        df = collector.collect_traffic_data(start_date, end_date, use_synthetic=True)
    
    if not df.empty:
        collector.save_traffic_data(df)
        print(f"\nSummary:")
        print(f"  Cities: {df['city'].nunique() if 'city' in df.columns else 'N/A'}")
        print(f"  Date range: {df['date'].min() if 'date' in df.columns else 'N/A'} to {df['date'].max() if 'date' in df.columns else 'N/A'}")
        print(f"  Total records: {len(df)}")
        if 'data_source' in df.columns:
            print(f"  Data source: {df['data_source'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()

