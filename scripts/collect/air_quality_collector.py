"""
Collect air quality data from OpenAQ API and EEA.

OpenAQ aggregates air quality data from multiple sources including EEA.
This provides programmatic access to historical air quality data.
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys
from bs4 import BeautifulSoup
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.utils.config import get_cities, get_date_range, ensure_data_directories
from scripts.utils.helpers import save_dataframe, convert_to_cet, standardize_city_name

class AirQualityCollector:
    """Collect air quality data from OpenAQ API (and EEA via manual CSV)."""
    
    def __init__(self):
        """Initialize air quality collector."""
        # OpenAQ API (primary source - free, no API key required)
        # Using v3 as v2 endpoints are deprecated (410 errors)
        self.openaq_base_url = "https://api.openaq.org/v3"
        self.openaq_session = requests.Session()
        self.openaq_session.headers.update({
            'Accept': 'application/json'
        })
        
        # EEA (fallback for manual CSV downloads)
        self.eea_base_url = "https://discomap.eea.europa.eu"
        self.cities = get_cities()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Pollutant mapping: our names -> OpenAQ parameter codes
        self.pollutant_mapping = {
            'NO2': 'no2',
            'PM2.5': 'pm25',
            'PM10': 'pm10',
            'O3': 'o3',
            'CO': 'co'
        }
        
        # City coordinates for OpenAQ location search
        self.city_coords = {
            'berlin': {'lat': 52.5200, 'lon': 13.4050, 'radius': 20000},  # 20km radius
            'munich': {'lat': 48.1351, 'lon': 11.5820, 'radius': 20000},
            'hamburg': {'lat': 53.5511, 'lon': 10.0000, 'radius': 20000},
            'cologne': {'lat': 50.9375, 'lon': 6.9603, 'radius': 20000},
            'frankfurt': {'lat': 50.1109, 'lon': 8.6821, 'radius': 20000}
        }
        
    def get_station_data_url(self, station_code: str, pollutant: str, 
                            start_date: datetime, end_date: datetime) -> str:
        """
        Construct URL for downloading station data.
        
        Args:
            station_code: EEA station code
            pollutant: Pollutant code (NO2, PM2.5, PM10, O3, CO)
            start_date: Start date
            end_date: End date
            
        Returns:
            URL string
        """
        # EEA API endpoint format
        # Note: This is a simplified version. The actual EEA API may require
        # different parameters or authentication
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # EEA data download URL (format may vary)
        url = f"{self.base_url}/mapping/rest/services/AirQualityExport/MapServer/0/query"
        
        return url
    
    def get_openaq_locations(self, city_key: str) -> List[Dict]:
        """
        Find OpenAQ monitoring locations near a city.
        
        Args:
            city_key: City key
            
        Returns:
            List of location dictionaries
        """
        if city_key not in self.city_coords:
            return []
        
        coords = self.city_coords[city_key]
        
        try:
            # Search for locations near the city
            url = f"{self.openaq_base_url}/locations"
            params = {
                'coordinates': f"{coords['lat']},{coords['lon']}",
                'radius': coords['radius'],
                'limit': 50,  # Get up to 50 nearby stations
                'country_id': 'DE'  # Germany only
            }
            
            response = self.openaq_session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            locations = data.get('results', [])
            return locations
            
        except Exception as e:
            print(f"  Error finding OpenAQ locations for {city_key}: {e}")
            return []
    
    def get_openaq_measurements(self, city_key: str, pollutant: str,
                               start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Get air quality measurements from OpenAQ API.
        
        Args:
            city_key: City key
            pollutant: Pollutant name (NO2, PM2.5, PM10, O3, CO)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with air quality data or None
        """
        city = self.cities[city_key]
        coords = self.city_coords[city_key]
        
        # Map pollutant name to OpenAQ parameter code
        openaq_param = self.pollutant_mapping.get(pollutant, pollutant.lower())
        
        try:
            # First, find locations near the city using locations endpoint
            locations_url = f"{self.openaq_base_url}/locations"
            locations_params = {
                'coordinates': f"{coords['lat']},{coords['lon']}",
                'radius': coords['radius'],
                'limit': 50,
                'countries_id': 'DE'  # Note: v3 uses 'countries_id' not 'country_id'
            }
            
            locations_response = self.openaq_session.get(locations_url, params=locations_params, timeout=30)
            
            # Handle 410 (deprecated) or other errors
            if locations_response.status_code == 410:
                print(f"  ⚠ OpenAQ API v3 endpoint not available (410 error)")
                print(f"  OpenAQ API may require authentication or have changed.")
                return None
            
            if locations_response.status_code != 200:
                print(f"  ⚠ OpenAQ API error: {locations_response.status_code}")
                return None
            
            locations_data = locations_response.json()
            locations = locations_data.get('results', [])
            
            if not locations:
                return None
            
            # Get location IDs
            location_ids = [loc.get('id') for loc in locations if loc.get('id')]
            
            if not location_ids:
                return None
            
            # Now get measurements for these locations
            url = f"{self.openaq_base_url}/measurements"
            all_measurements = []
            
            # Query each location (limit to first 5 to avoid too many requests)
            for location_id in location_ids[:5]:
                params = {
                    'locations_id': location_id,  # v3 uses 'locations_id'
                    'parameters_id': openaq_param,
                    'date_from': start_date.strftime('%Y-%m-%d'),
                    'date_to': end_date.strftime('%Y-%m-%d'),
                    'limit': 10000
                }
                
                page = 1
                while True:
                    params['page'] = page
                    response = self.openaq_session.get(url, params=params, timeout=30)
                    
                    if response.status_code == 410:
                        print(f"  ⚠ OpenAQ API endpoint deprecated")
                        return None
                    
                    if response.status_code != 200:
                        break  # Skip this location if error
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    results = data.get('results', [])
                    if not results:
                        break
                    
                    all_measurements.extend(results)
                    
                    # Check if there are more pages
                    meta = data.get('meta', {})
                    found = meta.get('found', 0)
                    limit = meta.get('limit', 10000)
                    if found == 0 or page * limit >= found:
                        break
                    
                    page += 1
                    time.sleep(0.3)  # Rate limiting
                
                time.sleep(0.3)  # Rate limiting between locations
            
            if not all_measurements:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(all_measurements)
            
            # Standardize column names
            column_mapping = {
                'date': 'datetime',
                'date.utc': 'datetime_utc',
                'parameter': 'pollutant',
                'value': 'value',
                'unit': 'unit',
                'location': 'station_name',
                'locationId': 'station_code',
                'coordinates.latitude': 'lat',
                'coordinates.longitude': 'lon'
            }
            
            # Rename columns that exist
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df = df.rename(columns={old_col: new_col})
            
            # Map pollutant codes to our standard names
            pollutant_reverse_map = {v: k for k, v in self.pollutant_mapping.items()}
            if 'pollutant' in df.columns:
                df['pollutant'] = df['pollutant'].map(
                    lambda x: pollutant_reverse_map.get(x, x.upper())
                )
            
            # Add city information
            df['city'] = city['name']
            df['city_key'] = city_key
            
            # Parse datetime
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                df['date'] = df['datetime'].dt.date
                df['hour'] = df['datetime'].dt.hour
            
            # Pivot to have pollutants as columns
            if 'pollutant' in df.columns and 'value' in df.columns:
                # Ensure required index columns exist
                index_cols = ['city', 'city_key', 'datetime', 'date', 'hour']
                available_index_cols = [col for col in index_cols if col in df.columns]
                
                # Add station info if available
                if 'station_name' in df.columns:
                    available_index_cols.append('station_name')
                if 'station_code' in df.columns:
                    available_index_cols.append('station_code')
                
                if available_index_cols:
                    pivot_df = df.pivot_table(
                        index=available_index_cols,
                        columns='pollutant',
                        values='value',
                        aggfunc='mean'  # Average if multiple measurements per hour
                    ).reset_index()
                    
                    # Rename pollutant columns to lowercase
                    pivot_df.columns.name = None
                    for col in pivot_df.columns:
                        if col in ['NO2', 'PM2.5', 'PM10', 'O3', 'CO']:
                            pivot_df = pivot_df.rename(columns={col: col.lower().replace('.', '')})
                    
                    return pivot_df
            
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 410:
                print(f"  ⚠ OpenAQ API endpoint deprecated (410 Gone)")
                print(f"  OpenAQ API structure has changed. Please use manual CSV download.")
            else:
                print(f"  Error fetching OpenAQ data for {city['name']}, {pollutant}: {e}")
            return None
        except Exception as e:
            print(f"  Error fetching OpenAQ data for {city['name']}, {pollutant}: {e}")
            return None
    
    def download_from_csv(self, filepath: str, city_key: str, 
                         save_processed: bool = True) -> Optional[pd.DataFrame]:
        """
        Load air quality data from a manually downloaded CSV file.
        
        If you download CSV files from EEA portal, use this method to load them.
        The processed data will be saved in both CSV and Parquet formats for inspection.
        
        Args:
            filepath: Path to CSV file
            city_key: City key for the data
            save_processed: Whether to save the processed data (default: True)
            
        Returns:
            DataFrame with standardized air quality data
        """
        try:
            print(f"Loading air quality data from {filepath}...")
            df = pd.read_csv(filepath, encoding='utf-8')
            print(f"  Loaded {len(df)} records")
            
            # Standardize column names (EEA format may vary)
            # Common EEA column names:
            # - DatetimeBegin, DatetimeEnd
            # - AirQualityStation, AirQualityStationEoICode
            # - NO2, PM2.5, PM10, O3, CO
            # - Value, UnitOfMeasurement
            
            # Map common EEA column names
            column_mapping = {
                'DatetimeBegin': 'datetime',
                'DatetimeEnd': 'datetime_end',
                'AirQualityStation': 'station_name',
                'AirQualityStationEoICode': 'station_code',
                'NO2': 'no2',
                'PM2.5': 'pm25',
                'PM10': 'pm10',
                'O3': 'o3',
                'CO': 'co',
                'Value': 'value',
                'UnitOfMeasurement': 'unit',
                'Concentration': 'value'
            }
            
            # Rename columns
            df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
            
            # Add city information
            city = self.cities[city_key]
            df['city'] = city['name']
            df['city_key'] = city_key
            
            # Parse datetime if available
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                df['date'] = df['datetime'].dt.date
                df['hour'] = df['datetime'].dt.hour
            
            # Save processed data if requested
            if save_processed and not df.empty:
                self.save_air_quality_data(df)
            
            return df
            
        except Exception as e:
            print(f"Error loading CSV file {filepath}: {e}")
            return None
    
    def load_multiple_csv_files(self, filepaths: Dict[str, str]) -> pd.DataFrame:
        """
        Load multiple CSV files for different cities and combine them.
        
        Args:
            filepaths: Dictionary mapping city_key to CSV file path
                      Example: {'berlin': 'path/to/berlin_data.csv', 
                               'munich': 'path/to/munich_data.csv'}
        
        Returns:
            Combined DataFrame with all air quality data
        """
        all_data = []
        
        for city_key, filepath in filepaths.items():
            if city_key not in self.cities:
                print(f"Warning: Unknown city key '{city_key}'. Skipping.")
                continue
            
            df = self.download_from_csv(filepath, city_key, save_processed=False)
            if df is not None and not df.empty:
                all_data.append(df)
        
        if not all_data:
            print("No data loaded from CSV files.")
            return pd.DataFrame()
        
        # Combine all dataframes
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Save combined data
        if not combined_df.empty:
            self.save_air_quality_data(combined_df)
        
        return combined_df
    
    def collect_air_quality_data(self, start_date: datetime, end_date: datetime,
                                city_keys: Optional[List[str]] = None,
                                pollutants: Optional[List[str]] = None,
                                use_openaq: bool = True) -> pd.DataFrame:
        """
        Collect air quality data for multiple cities and pollutants.
        
        Args:
            start_date: Start date
            end_date: End date
            city_keys: List of city keys (None = all cities)
            pollutants: List of pollutants (None = all: NO2, PM2.5, PM10, O3, CO)
            use_openaq: Whether to use OpenAQ API (default: True)
            
        Returns:
            DataFrame with air quality data
        """
        if city_keys is None:
            city_keys = list(self.cities.keys())
        
        if pollutants is None:
            pollutants = ['NO2', 'PM2.5', 'PM10', 'O3', 'CO']
        
        all_data = []
        
        print(f"Collecting air quality data from {start_date.date()} to {end_date.date()}")
        print(f"Cities: {', '.join([self.cities[k]['name'] for k in city_keys])}")
        print(f"Pollutants: {', '.join(pollutants)}")
        
        if use_openaq:
            print("\n⚠ Attempting OpenAQ API (Note: OpenAQ API v2 is deprecated, v3 may have different structure)")
            print("If this fails, please use manual CSV download from EEA portal.\n")
            
            # Try OpenAQ API first
            for city_key in city_keys:
                city_name = self.cities[city_key]['name']
                print(f"Fetching data for {city_name}...")
                
                # Get all pollutants for this city
                city_data = []
                for pollutant in pollutants:
                    print(f"  Getting {pollutant}...", end=' ')
                    data = self.get_openaq_measurements(city_key, pollutant, start_date, end_date)
                    
                    if data is not None and not data.empty:
                        city_data.append(data)
                        print(f"✓ ({len(data)} records)")
                    else:
                        print("✗ (no data)")
                    
                    time.sleep(0.3)  # Rate limiting
                
                # Combine pollutants for this city
                if city_data:
                    # Merge on common columns
                    from functools import reduce
                    city_df = reduce(lambda left, right: pd.merge(
                        left, right, 
                        on=['city', 'city_key', 'datetime', 'date', 'hour', 'station_name', 'station_code'],
                        how='outer'
                    ), city_data)
                    all_data.append(city_df)
                    print(f"  ✓ Collected data for {city_name}\n")
                else:
                    print(f"  ⚠ No data found for {city_name}\n")
        else:
            print("\nNOTE: OpenAQ disabled. EEA data requires manual CSV download.")
            print("Please download CSV files from EEA portal and use download_from_csv() method.")
        
        if not all_data:
            print("\nNo data collected via API.")
            if use_openaq:
                print("You can try:")
                print("1. Check if OpenAQ has data for your date range")
                print("2. Use download_from_csv() method with manually downloaded EEA CSV files")
            else:
                print("Please download data manually from EEA portal and use download_from_csv() method.")
            return pd.DataFrame()
        
        df = pd.concat(all_data, ignore_index=True)
        return df
    
    def save_air_quality_data(self, df: pd.DataFrame, filename: Optional[str] = None):
        """
        Save air quality data to file (both CSV and Parquet formats).
        
        Args:
            df: DataFrame with air quality data
            filename: Output filename base (auto-generated if None)
        """
        ensure_data_directories()
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"data/raw/air_quality/air_quality_data_{timestamp}"
        else:
            # Remove extension if provided
            filename_base = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Save as Parquet (efficient storage)
        parquet_file = f"{filename_base}.parquet"
        save_dataframe(df, parquet_file, format='parquet')
        
        # Save as CSV (easy to view in Excel/text editors)
        csv_file = f"{filename_base}.csv"
        save_dataframe(df, csv_file, format='csv')
        
        print(f"\nAir quality data saved:")
        print(f"  CSV (for viewing): {csv_file}")
        print(f"  Parquet (for processing): {parquet_file}")
        print(f"  Total records: {len(df)}")
        print(f"  Columns: {', '.join(df.columns.tolist())}")

def main():
    """Main function for standalone execution."""
    collector = AirQualityCollector()
    start_date, end_date = get_date_range()
    
    print("=" * 60)
    print("Air Quality Data Collection")
    print("=" * 60)
    print("\nUsing OpenAQ API (free, aggregates data from EEA and other sources)")
    print("No API key required!\n")
    
    df = collector.collect_air_quality_data(start_date, end_date, use_openaq=True)
    
    if not df.empty:
        collector.save_air_quality_data(df)
        print(f"\nSummary:")
        print(f"  Cities: {df['city'].nunique() if 'city' in df.columns else 'N/A'}")
        print(f"  Total records: {len(df)}")
    else:
        print("\nNo data collected via API.")
        print("Please use download_from_csv() method with manually downloaded files.")

if __name__ == "__main__":
    main()

