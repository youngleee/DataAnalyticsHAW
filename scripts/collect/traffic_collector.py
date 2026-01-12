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
        
        # TomTom city coordinates (dynamically generated from city config)
        # Using coordinates as fallback for all cities
        self.city_ids = {}
        for city_key, city_info in self.cities.items():
            self.city_ids[city_key] = f"{city_info['lat']},{city_info['lon']}"
        
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
        Create realistic HOURLY synthetic traffic data based on typical German city patterns.
        
        Generates traffic patterns based on:
        - Hour of day (rush hours: 7-9 AM, 5-7 PM)
        - Day of week (weekday vs weekend)
        - City size (larger cities = more congestion)
        - German public holidays (Jan-Mar 2024)
        - Realistic hour-to-hour variation
        
        Args:
            city_key: City key
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with HOURLY synthetic traffic data
        """
        import random
        import numpy as np
        
        city = self.cities[city_key]
        # Generate HOURLY timestamps
        timestamps = pd.date_range(start=start_date, end=end_date, freq='H')
        
        # City size factors (larger cities = more base congestion)
        city_traffic_base = {
            'berlin': 40, 'hamburg': 38, 'munich': 42, 'cologne': 36, 
            'frankfurt': 40, 'stuttgart': 38, 'dusseldorf': 35, 'dortmund': 32,
            'essen': 30, 'leipzig': 28, 'bremen': 26, 'dresden': 27,
            'hanover': 29, 'nuremberg': 33, 'duisburg': 28, 'bochum': 26,
            'wuppertal': 25, 'bielefeld': 24, 'bonn': 28, 'munster': 24,
        }
        base_traffic = city_traffic_base.get(city_key, 25 + random.uniform(0, 8))
        
        # German public holidays Jan-Mar 2024 with traffic patterns
        # Travel holidays = HIGH traffic, quiet holidays = lower traffic
        german_holidays = {
            '2024-01-01': ('New Year', 'high'),           # People traveling, visiting family
            '2024-01-06': ('Epiphany', 'moderate'),       # Some travel in southern states
            '2024-03-29': ('Good Friday', 'high'),        # Major travel day for Easter
            '2024-03-31': ('Easter Sunday', 'high'),      # Family visits, travel
        }
        # Days BEFORE holidays often have even worse traffic (travel)
        pre_holiday_dates = ['2023-12-31', '2024-03-28', '2024-03-30']  # NYE, day before Good Friday, Easter Saturday
        
        traffic_data = []
        np.random.seed(hash(city_key) % 2**32)
        
        # City-specific free flow speed (larger cities slightly slower)
        city_free_flow = 55 - (base_traffic - 25) * 0.3 + random.uniform(-3, 3)
        city_free_flow = max(45, min(60, city_free_flow))
        
        for dt in timestamps:
            date_str = dt.strftime('%Y-%m-%d')
            hour = dt.hour
            day_of_week = dt.weekday()  # 0=Monday, 6=Sunday
            
            # Start with base traffic
            hourly_traffic = base_traffic
            
            # HOURLY PATTERNS (the key differentiator!)
            is_holiday = date_str in german_holidays
            is_pre_holiday = date_str in pre_holiday_dates
            is_weekend = day_of_week >= 5
            holiday_info = german_holidays.get(date_str, (None, None))
            
            if is_pre_holiday:
                # Day before major holidays = TERRIBLE traffic (everyone traveling)
                if 10 <= hour <= 20:
                    hourly_traffic += 40 + np.random.normal(0, 8)  # Very high
                elif 6 <= hour <= 9:
                    hourly_traffic += 25 + np.random.normal(0, 5)
                else:
                    hourly_traffic += 10 + np.random.normal(0, 4)
            elif is_holiday:
                # Holidays: HIGH traffic due to travel and family visits
                holiday_name, traffic_level = holiday_info
                if traffic_level == 'high':
                    # High traffic holidays (New Year, Easter)
                    if 10 <= hour <= 18:
                        hourly_traffic += 35 + np.random.normal(0, 7)  # Heavy traffic
                    elif 8 <= hour <= 9 or 19 <= hour <= 21:
                        hourly_traffic += 25 + np.random.normal(0, 5)
                    else:
                        hourly_traffic += 5 + np.random.normal(0, 3)
                else:
                    # Moderate traffic holidays
                    if 10 <= hour <= 17:
                        hourly_traffic += 20 + np.random.normal(0, 5)
                    else:
                        hourly_traffic += 5 + np.random.normal(0, 3)
            elif is_weekend:
                # Weekend patterns
                if day_of_week == 5:  # Saturday
                    if 10 <= hour <= 14:  # Shopping time
                        hourly_traffic += 20 + np.random.normal(0, 5)
                    elif 15 <= hour <= 18:
                        hourly_traffic += 15 + np.random.normal(0, 5)
                    elif 6 <= hour <= 9:
                        hourly_traffic += 5 + np.random.normal(0, 3)
                    else:
                        hourly_traffic -= 5 + np.random.normal(0, 3)
                else:  # Sunday
                    if 11 <= hour <= 16:
                        hourly_traffic += 10 + np.random.normal(0, 4)
                    else:
                        hourly_traffic -= 10 + np.random.normal(0, 3)
            else:
                # WEEKDAY patterns with rush hours
                if 7 <= hour <= 9:  # Morning rush
                    if hour == 8:
                        hourly_traffic += 45 + np.random.normal(0, 6)  # Peak
                    else:
                        hourly_traffic += 35 + np.random.normal(0, 5)
                elif 17 <= hour <= 19:  # Evening rush
                    if hour == 18:
                        hourly_traffic += 50 + np.random.normal(0, 6)  # Peak
                    else:
                        hourly_traffic += 40 + np.random.normal(0, 5)
                elif 10 <= hour <= 16:  # Daytime
                    hourly_traffic += 20 + np.random.normal(0, 5)
                elif 6 <= hour <= 6:  # Early morning
                    hourly_traffic += 10 + np.random.normal(0, 3)
                elif 20 <= hour <= 22:  # Evening
                    hourly_traffic += 10 + np.random.normal(0, 4)
                else:  # Night (23:00 - 05:59)
                    hourly_traffic -= 15 + np.random.normal(0, 3)
            
            # Friday adjustments (more traffic in evening)
            if day_of_week == 4 and 15 <= hour <= 19:
                hourly_traffic += 10
            
            # Monday morning is slightly heavier
            if day_of_week == 0 and 7 <= hour <= 9:
                hourly_traffic += 5
            
            # Clamp to valid range (5-95)
            hourly_traffic = max(5, min(95, hourly_traffic))
            
            # Calculate derived metrics
            congestion_level = hourly_traffic / 100
            current_speed = city_free_flow * (1 - congestion_level * 0.7)
            current_speed = max(10, current_speed)  # Minimum 10 km/h even in heavy traffic
            
            # Determine if this is a rush hour
            is_rush_hour = (not is_weekend and not is_holiday and 
                          ((7 <= hour <= 9) or (17 <= hour <= 19)))
            
            # Get holiday name if applicable
            holiday_name = ''
            if is_holiday:
                holiday_name = german_holidays.get(date_str, ('', ''))[0]
            elif is_pre_holiday:
                holiday_name = 'Pre-Holiday Travel'
            
            traffic_data.append({
                'city': city['name'],
                'city_key': city_key,
                'datetime': dt,
                'date': dt.date(),
                'hour': hour,
                'day_of_week': day_of_week,
                'lat': float(city['lat']),
                'lon': float(city['lon']),
                'current_speed': round(current_speed, 1),
                'free_flow_speed': round(city_free_flow, 1),
                'confidence': 0.95,
                'congestion_level': round(congestion_level, 3),
                'traffic_index': round(hourly_traffic, 2),
                'is_rush_hour': is_rush_hour,
                'is_weekend': is_weekend,
                'is_holiday': is_holiday or is_pre_holiday,
                'holiday_name': holiday_name,
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
            
            # Quick test: Try API for first city/date to see if it works
            test_city = city_keys[0]
            test_data = self.get_tomtom_traffic_index(test_city, start_date)
            
            if not test_data:
                print(f"[WARN] TomTom API unavailable (403 Forbidden or no data).")
                print("Switching to synthetic traffic data for all cities...")
                # Fall back to synthetic for all cities
                for city_key in city_keys:
                    print(f"Generating synthetic data for {self.cities[city_key]['name']}...")
                    df = self.create_synthetic_traffic_data(city_key, start_date, end_date)
                    all_data.append(df)
            else:
                # API works, collect real data
                current_date = start_date
                consecutive_failures = 0
                max_failures = 5  # Stop trying after 5 consecutive failures
                
                while current_date <= end_date:
                    for city_key in city_keys:
                        # Try TomTom API first
                        traffic_data = self.get_tomtom_traffic_index(city_key, current_date)
                        
                        if not traffic_data:
                            consecutive_failures += 1
                            if consecutive_failures >= max_failures:
                                print(f"\n[WARN] Too many API failures. Switching to synthetic data...")
                                # Generate synthetic for remaining dates
                                remaining_dates = (end_date - current_date).days + 1
                                for remaining_city in city_keys:
                                    df = self.create_synthetic_traffic_data(remaining_city, current_date, end_date)
                                    all_data.append(df)
                                break
                        else:
                            consecutive_failures = 0  # Reset on success
                            all_data.append(traffic_data)
                        
                        time.sleep(0.1)  # Reduced rate limiting
                    
                    if consecutive_failures >= max_failures:
                        break
                    
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

