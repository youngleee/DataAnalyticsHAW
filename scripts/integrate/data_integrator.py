"""
Data integration module.

Merges weather, air quality, and traffic datasets by city and timestamp.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.utils.helpers import load_dataframe, save_dataframe
from scripts.utils.config import get_cities

class DataIntegrator:
    """Integrate data from multiple sources."""
    
    def __init__(self):
        """Initialize data integrator."""
        self.cities = get_cities()
        
    def load_raw_datasets(self, weather_path: Optional[str] = None,
                         air_quality_path: Optional[str] = None,
                         traffic_path: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Load raw datasets from files.
        
        Args:
            weather_path: Path to weather data file
            air_quality_path: Path to air quality data file
            traffic_path: Path to traffic data file
            
        Returns:
            Dictionary with loaded DataFrames
        """
        datasets = {}
        
        # Load weather data
        if weather_path and os.path.exists(weather_path):
            print(f"Loading weather data from {weather_path}...")
            datasets['weather'] = load_dataframe(weather_path)
        else:
            # Try to find latest weather file
            weather_files = self._find_latest_file('data/raw/weather')
            if weather_files:
                print(f"Loading weather data from {weather_files}...")
                datasets['weather'] = load_dataframe(weather_files)
        
        # Load air quality data
        if air_quality_path and os.path.exists(air_quality_path):
            print(f"Loading air quality data from {air_quality_path}...")
            datasets['air_quality'] = load_dataframe(air_quality_path)
        else:
            air_quality_files = self._find_latest_file('data/raw/air_quality')
            if air_quality_files:
                print(f"Loading air quality data from {air_quality_files}...")
                datasets['air_quality'] = load_dataframe(air_quality_files)
        
        # Load traffic data
        if traffic_path and os.path.exists(traffic_path):
            print(f"Loading traffic data from {traffic_path}...")
            datasets['traffic'] = load_dataframe(traffic_path)
        else:
            traffic_files = self._find_latest_file('data/raw/traffic')
            if traffic_files:
                print(f"Loading traffic data from {traffic_files}...")
                datasets['traffic'] = load_dataframe(traffic_files)
        
        return datasets
    
    def _find_latest_file(self, directory: str) -> Optional[str]:
        """Find the latest file in a directory."""
        if not os.path.exists(directory):
            return None
        
        files = [f for f in os.listdir(directory) if f.endswith(('.parquet', '.csv', '.json'))]
        if not files:
            return None
        
        # Sort by modification time
        files_with_time = [(f, os.path.getmtime(os.path.join(directory, f))) for f in files]
        files_with_time.sort(key=lambda x: x[1], reverse=True)
        
        return os.path.join(directory, files_with_time[0][0])
    
    def prepare_for_merge(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Prepare dataset for merging by standardizing keys.
        
        Args:
            df: DataFrame
            data_type: Type of data ('weather', 'air_quality', 'traffic')
            
        Returns:
            Prepared DataFrame
        """
        df = df.copy()
        
        # Ensure datetime column exists
        if 'datetime' not in df.columns and 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        else:
            raise ValueError(f"No datetime or date column found in {data_type} data")
        
        # Standardize city names
        if 'city' in df.columns:
            df['city_key'] = df['city'].apply(self._standardize_city_key)
        elif 'city_key' in df.columns:
            pass  # Already standardized
        else:
            raise ValueError(f"No city or city_key column found in {data_type} data")
        
        # Round datetime to nearest hour for alignment
        df['datetime_hour'] = df['datetime'].dt.floor('H')
        
        return df
    
    def _standardize_city_key(self, city_name: str) -> str:
        """Standardize city name to key."""
        city_mapping = {
            'berlin': 'berlin',
            'munich': 'munich',
            'münchen': 'munich',
            'hamburg': 'hamburg',
            'cologne': 'cologne',
            'köln': 'cologne',
            'frankfurt': 'frankfurt',
            'frankfurt am main': 'frankfurt'
        }
        
        city_lower = str(city_name).lower().strip()
        return city_mapping.get(city_lower, city_lower)
    
    def merge_datasets(self, weather_df: pd.DataFrame,
                      air_quality_df: pd.DataFrame,
                      traffic_df: pd.DataFrame,
                      merge_strategy: str = 'outer') -> pd.DataFrame:
        """
        Merge weather, air quality, and traffic datasets.
        
        Args:
            weather_df: Weather DataFrame
            air_quality_df: Air quality DataFrame
            traffic_df: Traffic DataFrame
            merge_strategy: Merge strategy ('inner', 'outer', 'left', 'right')
            
        Returns:
            Merged DataFrame
        """
        print("\nMerging datasets...")
        
        # Prepare each dataset
        print("Preparing weather data...")
        weather_df = self.prepare_for_merge(weather_df, 'weather')
        
        print("Preparing air quality data...")
        air_quality_df = self.prepare_for_merge(air_quality_df, 'air_quality')
        
        print("Preparing traffic data...")
        traffic_df = self.prepare_for_merge(traffic_df, 'traffic')
        
        # Aggregate air quality data if multiple stations per city
        if 'station_code' in air_quality_df.columns:
            print("Aggregating air quality data by city (multiple stations)...")
            agg_dict = {
                'no2': 'mean',
                'pm25': 'mean',
                'pm10': 'mean',
                'o3': 'mean',
                'co': 'mean'
            }
            
            # Only aggregate numeric columns that exist
            agg_dict = {k: v for k, v in agg_dict.items() if k in air_quality_df.columns}
            
            air_quality_df = air_quality_df.groupby(['city_key', 'datetime_hour']).agg(agg_dict).reset_index()
        
        # Merge weather and air quality
        print("Merging weather and air quality data...")
        merged = pd.merge(
            weather_df,
            air_quality_df,
            on=['city_key', 'datetime_hour'],
            how=merge_strategy,
            suffixes=('', '_aq')
        )
        
        # Merge with traffic
        print("Merging with traffic data...")
        merged = pd.merge(
            merged,
            traffic_df,
            on=['city_key', 'datetime_hour'],
            how=merge_strategy,
            suffixes=('', '_traffic')
        )
        
        # Clean up duplicate columns
        # Remove duplicate city columns
        if 'city_traffic' in merged.columns:
            merged = merged.drop(columns=['city_traffic'])
        if 'city_aq' in merged.columns:
            merged = merged.drop(columns=['city_aq'])
        
        # Use datetime_hour as main datetime
        if 'datetime_hour' in merged.columns:
            merged['datetime'] = merged['datetime_hour']
            merged = merged.drop(columns=['datetime_hour'])
        
        # Sort by city and datetime
        merged = merged.sort_values(['city_key', 'datetime']).reset_index(drop=True)
        
        print(f"\nMerge complete:")
        print(f"  Total records: {len(merged)}")
        print(f"  Cities: {merged['city_key'].nunique() if 'city_key' in merged.columns else 'N/A'}")
        print(f"  Date range: {merged['datetime'].min()} to {merged['datetime'].max()}")
        
        return merged
    
    def create_city_specific_datasets(self, merged_df: pd.DataFrame, 
                                     output_dir: str = 'outputs/datasets') -> Dict[str, pd.DataFrame]:
        """
        Create separate datasets for each city.
        
        Args:
            merged_df: Merged DataFrame
            output_dir: Output directory
            
        Returns:
            Dictionary of city-specific DataFrames
        """
        os.makedirs(output_dir, exist_ok=True)
        
        city_datasets = {}
        
        if 'city_key' not in merged_df.columns:
            print("No city_key column found. Cannot create city-specific datasets.")
            return city_datasets
        
        for city_key in merged_df['city_key'].unique():
            city_df = merged_df[merged_df['city_key'] == city_key].copy()
            city_name = self.cities[city_key]['name']
            
            city_datasets[city_key] = city_df
            
            # Save to file
            filename = os.path.join(output_dir, f"{city_key}_data.parquet")
            save_dataframe(city_df, filename, format='parquet')
            print(f"Saved {city_name} data to {filename}")
        
        return city_datasets
    
    def save_merged_dataset(self, merged_df: pd.DataFrame,
                           filename: Optional[str] = None,
                           format: str = 'parquet'):
        """
        Save merged dataset to file.
        
        Args:
            merged_df: Merged DataFrame
            filename: Output filename
            format: File format ('parquet', 'csv', 'json')
        """
        os.makedirs('outputs/datasets', exist_ok=True)
        
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"outputs/datasets/merged_dataset_{timestamp}.{format if format != 'parquet' else 'parquet'}"
        
        save_dataframe(merged_df, filename, format=format)
        print(f"\nMerged dataset saved to {filename}")

