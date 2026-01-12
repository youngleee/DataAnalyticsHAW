"""
Collect air quality data from Umweltbundesamt (UBA) API.

UBA is the official German government source for air quality data.
Provides access to over 400 monitoring stations across Germany.
"""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.utils.config import get_cities, get_date_range, ensure_data_directories
from scripts.utils.helpers import save_dataframe, convert_to_cet, standardize_city_name

class AirQualityCollector:
    """Collect air quality data from UBA (Umweltbundesamt) API."""
    
    def __init__(self):
        """Initialize air quality collector."""
        # UBA API (official German government source - free, no API key required)
        # Documentation: https://luftqualitaet.api.bund.dev/
        # Main portal: https://luftdaten.umweltbundesamt.de/en
        # API endpoint: https://www.umweltbundesamt.de/api/air_data/v2/airquality/json
        self.uba_base_url = "https://www.umweltbundesamt.de/api/air_data/v2/airquality/json"
        self.uba_session = requests.Session()
        self.uba_session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'DataAnalyticsHAW/1.0'
        })
        
        self.cities = get_cities()
        
        # Pollutant mapping: our names -> UBA parameter codes
        # UBA uses standard pollutant codes
        # We focus on the 3 most reliably available pollutants
        self.pollutant_mapping = {
            'NO2': 'NO2',
            'PM10': 'PM10',
            'O3': 'O3'
        }
        
        # City to UBA station mapping (we'll discover stations dynamically)
        # UBA uses station codes/IDs
        self.city_stations = {}  # Will be populated when we discover stations
        
    def parse_station_array(self, station_id: str, station_array: List) -> Dict:
        """
        Parse station array into a dictionary.
        
        Station array format (based on UBA API):
        [0] station_id (string)
        [1] station_code (e.g., 'DEBE021')
        [2] station_name (e.g., 'Berlin Neukölln')
        [3] city (e.g., 'Berlin')
        [4] state_code
        [5] date_from
        [6] date_to
        [7] longitude
        [8] latitude
        [9-19] additional fields
        """
        if not isinstance(station_array, list) or len(station_array) < 9:
            return {}
        
        return {
            'station_id': station_id,
            'station_code': station_array[1] if len(station_array) > 1 else '',
            'station_name': station_array[2] if len(station_array) > 2 else '',
            'city': station_array[3] if len(station_array) > 3 else '',
            'state_code': station_array[4] if len(station_array) > 4 else '',
            'date_from': station_array[5] if len(station_array) > 5 else '',
            'date_to': station_array[6] if len(station_array) > 6 else '',
            'longitude': station_array[7] if len(station_array) > 7 else '',
            'latitude': station_array[8] if len(station_array) > 8 else '',
        }
    
    def get_uba_stations(self, city_key: str) -> List[Dict]:
        """
        Get UBA monitoring stations for a city.
        
        Args:
            city_key: City key
            
        Returns:
            List of station dictionaries with station IDs
        """
        city = self.cities[city_key]
        city_name = city['name']
        
        try:
            # UBA API v2 stations endpoint
            # Format: https://www.umweltbundesamt.de/api/air_data/v2/stations/json
            url = "https://www.umweltbundesamt.de/api/air_data/v2/stations/json"
            
            # Get stations for a date range (required parameters)
            params = {
                'use': 'airquality',
                'lang': 'en',
                'date_from': '2024-01-01',
                'time_from': '1',
                'date_to': '2024-12-31',
                'time_to': '24'
            }
            
            response = self.uba_session.get(url, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                # UBA API returns: {'data': {station_id: [station_array], ...}}
                stations_data = data.get('data', {})
                
                # Filter stations by city name
                city_stations = []
                city_name_lower = city_name.lower()
                
                for station_id, station_array in stations_data.items():
                    # Parse the array structure
                    station_info = self.parse_station_array(station_id, station_array)
                    
                    if not station_info:
                        continue
                    
                    station_city = station_info.get('city', '').lower()
                    
                    # Match city name (handles variations like München/Munich)
                    if (city_name_lower in station_city or 
                        station_city in city_name_lower or
                        city.get('eea_name', '').lower() in station_city):
                        city_stations.append(station_info)
                
                return city_stations
            else:
                print(f"  UBA API error: {response.status_code}")
                if response.status_code != 200:
                    print(f"  Response: {response.text[:200]}")
                return []
                
        except Exception as e:
            print(f"  Error finding UBA stations for {city_key}: {e}")
            return []
    
    def get_uba_measurements(self, city_key: str, pollutant: str,
                             start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Get air quality measurements from UBA API.
        
        Args:
            city_key: City key
            pollutant: Pollutant name (NO2, PM2.5, PM10, O3, CO)
            start_date: Start date
            end_date: End date
            
        Returns:
            DataFrame with air quality data or None
        """
        city = self.cities[city_key]
        
        # Map pollutant name to UBA parameter code
        uba_param = self.pollutant_mapping.get(pollutant, pollutant)
        
        try:
            # First, get stations for this city
            stations = self.get_uba_stations(city_key)
            
            if not stations:
                print(f"    (No stations found for {city['name']})")
                return None
            
            print(f"    (Found {len(stations)} stations)", end=' ')
            
            # UBA API v2 endpoint for measurements
            # Format: https://www.umweltbundesamt.de/api/air_data/v2/airquality/json
            url = self.uba_base_url
            
            all_measurements = []
            
            # Query only the first station per city (to keep data size manageable)
            for station in stations[:1]:
                station_id = station.get('station_id')
                if not station_id:
                    continue
                
                # UBA API parameters (required format)
                # time_from and time_to use numbers 1-24, not HH:MM:SS
                params = {
                    'component': uba_param,
                    'station': station_id,
                    'date_from': start_date.strftime('%Y-%m-%d'),
                    'time_from': '1',  # Hour 1 (00:00-00:59)
                    'date_to': end_date.strftime('%Y-%m-%d'),
                    'time_to': '24',  # Hour 24 (23:00-23:59)
                    'lang': 'en'
                }
                
                response = self.uba_session.get(url, params=params, timeout=60)
                
                if response.status_code != 200:
                    continue  # Skip this station if error
                
                data = response.json()
                
                # UBA API response structure: 
                # {'data': {station_id: {datetime: [datetime_end, aqi, incomplete, [comp_data...], ...]}}}
                # comp_data format: [component_id, value, flag, normalized_value]
                stations_data = data.get('data', {})
                
                # Get data for this station
                station_data = stations_data.get(station_id, {})
                
                # Parse each datetime entry
                for datetime_str, measurement_array in station_data.items():
                    if not isinstance(measurement_array, list) or len(measurement_array) < 4:
                        continue
                    
                    # measurement_array structure:
                    # [0] datetime_end
                    # [1] airquality_index
                    # [2] incomplete_flag
                    # [3+] component data arrays: [component_id, value, flag, normalized_value]
                    
                    datetime_end = measurement_array[0] if len(measurement_array) > 0 else ''
                    
                    # Find the component data for our pollutant
                    # Component IDs: 1=PM10, 2=PM2.5, 3=O3, 4=CO, 5=NO2
                    component_id_map = {
                        'NO2': 5,
                        'PM2.5': 2,
                        'PM10': 1,
                        'O3': 3,
                        'CO': 4
                    }
                    target_component_id = component_id_map.get(uba_param, None)
                    
                    # Search through component data arrays
                    value = None
                    for item in measurement_array[3:]:  # Skip first 3 elements
                        if isinstance(item, list) and len(item) >= 2:
                            comp_id = item[0]
                            if comp_id == target_component_id:
                                value = item[1]  # The actual measurement value
                                break
                    
                    if value is not None:
                        measurement_dict = {
                            'datetime': datetime_str,
                            'datetime_end': datetime_end,
                            'value': value,
                            'component': uba_param,
                            'station_id': station_id,
                            'station_name': station.get('station_name', station.get('name', '')),
                            'city': city['name'],
                            'city_key': city_key
                        }
                        all_measurements.append(measurement_dict)
                time.sleep(0.5)  # Rate limiting between stations
            
            if not all_measurements:
                print(f"(No measurements in date range)")
                return None
            
            print(f"({len(all_measurements)} measurements)", end=' ')
            
            # Convert to DataFrame
            df = pd.DataFrame(all_measurements)
            
            if df.empty:
                return None
            
            # Ensure value is numeric
            if 'value' in df.columns:
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
            
            # Parse datetime from datetime column
            if 'datetime' in df.columns:
                df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
                df['date'] = df['datetime'].dt.date
                df['hour'] = df['datetime'].dt.hour
            
            # Map component to pollutant name for pivoting
            if 'component' in df.columns:
                # Create reverse mapping
                component_to_pollutant = {
                    'NO2': 'NO2',
                    'PM10': 'PM10',
                    'O3': 'O3'
                }
                df['pollutant'] = df['component'].map(component_to_pollutant)
            
            # Pivot to have pollutants as columns
            if 'pollutant' in df.columns and 'value' in df.columns:
                # Ensure required index columns exist
                index_cols = ['city', 'city_key', 'datetime', 'date', 'hour']
                available_index_cols = [col for col in index_cols if col in df.columns]
                
                # Add station info if available
                if 'station_name' in df.columns:
                    available_index_cols.append('station_name')
                if 'station_id' in df.columns:
                    available_index_cols.append('station_id')
                
                if available_index_cols and len(df) > 0:
                    # Remove rows with missing required columns
                    df_clean = df.dropna(subset=available_index_cols + ['pollutant', 'value'])
                    
                    if not df_clean.empty:
                        pivot_df = df_clean.pivot_table(
                            index=available_index_cols,
                            columns='pollutant',
                            values='value',
                            aggfunc='mean'  # Average if multiple measurements per hour
                        ).reset_index()
                        
                        # Rename pollutant columns to lowercase
                        pivot_df.columns.name = None
                        for col in pivot_df.columns:
                            if col in ['NO2', 'PM10', 'O3']:
                                pivot_df = pivot_df.rename(columns={col: col.lower()})
                        
                        return pivot_df
            
            # If pivot didn't work, return the original df with proper column names
            return df
            
        except requests.exceptions.HTTPError as e:
            print(f"  Error fetching UBA data for {city['name']}, {pollutant}: {e}")
            return None
        except Exception as e:
            print(f"  Error fetching UBA data for {city['name']}, {pollutant}: {e}")
            return None
    
    def download_from_csv(self, filepath: str, city_key: str, 
                         save_processed: bool = True) -> Optional[pd.DataFrame]:
        """
        Load air quality data from a manually downloaded CSV file.
        
        If you download CSV files from UBA or EEA portal, use this method to load them.
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
            
            # Standardize column names (UBA/EEA format may vary)
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
                                use_uba: bool = True) -> pd.DataFrame:
        """
        Collect air quality data for multiple cities and pollutants.
        
        Args:
            start_date: Start date
            end_date: End date
            city_keys: List of city keys (None = all cities)
            pollutants: List of pollutants (None = all: NO2, PM2.5, PM10, O3, CO)
            use_uba: Whether to use UBA API (default: True)
            
        Returns:
            DataFrame with air quality data
        """
        if city_keys is None:
            city_keys = list(self.cities.keys())
        
        if pollutants is None:
            # Collect only the 3 pollutants that are reliably available: NO2, PM10, O3
            pollutants = ['NO2', 'PM10', 'O3']
        
        all_data = []
        
        print(f"Collecting air quality data from {start_date.date()} to {end_date.date()}")
        print(f"Cities: {', '.join([self.cities[k]['name'] for k in city_keys])}")
        print(f"Pollutants: {', '.join(pollutants)}")
        
        if use_uba:
            print("\nUsing UBA (Umweltbundesamt) API - Official German Government Source")
            print("Documentation: https://luftqualitaet.api.bund.dev/\n")
            
            # Try UBA API
            for city_key in city_keys:
                city_name = self.cities[city_key]['name']
                print(f"Fetching data for {city_name}...")
                
                # Get all pollutants for this city
                city_data = []
                for pollutant in pollutants:
                    print(f"  Getting {pollutant}...", end=' ')
                    data = self.get_uba_measurements(city_key, pollutant, start_date, end_date)
                    
                    if data is not None and not data.empty:
                        city_data.append(data)
                        print(f"OK ({len(data)} records)")
                    else:
                        print("(no data)")
                    
                    time.sleep(0.5)  # Rate limiting
                
                # Combine pollutants for this city
                if city_data:
                    # Merge on common columns that exist in all dataframes
                    from functools import reduce
                    
                    # Find common columns across all dataframes
                    common_cols = set(city_data[0].columns)
                    for df in city_data[1:]:
                        common_cols = common_cols.intersection(set(df.columns))
                    
                    # Use merge keys that exist in all dataframes
                    merge_keys = ['datetime', 'date', 'hour']
                    if 'city' in common_cols:
                        merge_keys.insert(0, 'city')
                    if 'city_key' in common_cols:
                        merge_keys.insert(1, 'city_key')
                    if 'station_name' in common_cols:
                        merge_keys.append('station_name')
                    if 'station_id' in common_cols:
                        merge_keys.append('station_id')
                    if 'station_code' in common_cols:
                        merge_keys.append('station_code')
                    
                    # Filter to only keys that exist in all dataframes
                    merge_keys = [key for key in merge_keys if key in common_cols]
                    
                    if merge_keys:
                        city_df = reduce(lambda left, right: pd.merge(
                            left, right, 
                            on=merge_keys,
                            how='outer'
                        ), city_data)
                    else:
                        # If no common keys, just concatenate
                        city_df = pd.concat(city_data, ignore_index=True)
                    
                    all_data.append(city_df)
                    print(f"  OK Collected data for {city_name}\n")
                else:
                    print(f"  (No data found for {city_name})\n")
        else:
            print("\nNOTE: UBA API disabled. Use download_from_csv() method with manually downloaded files.")
            print("Download data from: https://luftdaten.umweltbundesamt.de/en")
        
        if not all_data:
            print("\nNo data collected via API.")
            if use_uba:
                print("You can try:")
                print("1. Check UBA API documentation: https://luftqualitaet.api.bund.dev/")
                print("2. Use download_from_csv() method with manually downloaded CSV files")
                print("3. Download data from: https://luftdaten.umweltbundesamt.de/en")
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
        
        # Ensure the air_quality directory exists
        air_quality_dir = "data/raw/air_quality"
        os.makedirs(air_quality_dir, exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename_base = f"{air_quality_dir}/air_quality_data_{timestamp}"
        else:
            # Remove extension if provided
            filename_base = filename.rsplit('.', 1)[0] if '.' in filename else filename
            # Ensure it's in the correct directory
            if not filename_base.startswith(air_quality_dir):
                filename_base = f"{air_quality_dir}/{os.path.basename(filename_base)}"
        
        # Save as CSV first (easy to view in Excel/text editors)
        csv_file = f"{filename_base}.csv"
        save_dataframe(df, csv_file, format='csv')
        
        # Save as Parquet (efficient storage) - handle errors gracefully
        parquet_file = f"{filename_base}.parquet"
        try:
            # Convert object columns to string to avoid Parquet type errors
            df_for_parquet = df.copy()
            for col in df_for_parquet.columns:
                if df_for_parquet[col].dtype == 'object':
                    df_for_parquet[col] = df_for_parquet[col].astype(str)
            save_dataframe(df_for_parquet, parquet_file, format='parquet')
        except Exception as e:
            print(f"  Warning: Could not save Parquet file: {e}")
            print(f"  CSV file saved successfully at: {csv_file}")
            parquet_file = None
        
        print(f"\nAir quality data saved:")
        print(f"  CSV (for viewing): {csv_file}")
        if parquet_file:
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
    print("\nUsing UBA (Umweltbundesamt) API")
    print("Official German Government Source - Free, No API Key Required")
    print("Documentation: https://luftqualitaet.api.bund.dev/\n")
    
    df = collector.collect_air_quality_data(start_date, end_date, use_uba=True)
    
    if not df.empty:
        collector.save_air_quality_data(df)
        print(f"\nSummary:")
        print(f"  Cities: {df['city'].nunique() if 'city' in df.columns else 'N/A'}")
        print(f"  Total records: {len(df)}")
    else:
        print("\nNo data collected via API.")
        print("Please check UBA API documentation or use download_from_csv() method.")

if __name__ == "__main__":
    main()
