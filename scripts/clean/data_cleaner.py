"""
Data cleaning module for air quality, weather, and traffic data.

Handles:
- Missing values
- Outliers
- Duplicates
- Invalid entries
- Data type standardization
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import warnings

warnings.filterwarnings('ignore')

class DataCleaner:
    """Clean and validate data from all sources."""
    
    def __init__(self):
        """Initialize data cleaner."""
        # Define valid ranges for different variables
        self.valid_ranges = {
            'temperature': (-30, 50),  # Celsius
            'humidity': (0, 100),  # Percentage
            'wind_speed': (0, 200),  # m/s
            'pressure': (800, 1100),  # hPa
            'no2': (0, 500),  # μg/m³
            'pm25': (0, 500),  # μg/m³
            'pm10': (0, 1000),  # μg/m³
            'o3': (0, 500),  # μg/m³
            'co': (0, 50),  # mg/m³
            'traffic_index': (0, 100),  # Percentage
            'congestion_level': (0, 1)  # Ratio
        }
        
    def clean_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean weather data.
        
        Args:
            df: Raw weather DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Standardize column names
        column_mapping = {
            'temp': 'temperature',
            'temp_c': 'temperature',
            'humidity_percent': 'humidity',
            'wind_speed_ms': 'wind_speed',
            'windSpeed': 'wind_speed',
            'pressure_hpa': 'pressure',
            'pressure_mb': 'pressure'
        }
        df = df.rename(columns=column_mapping)
        
        # Convert datetime columns
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['city', 'date', 'timestamp'], keep='first')
        
        # Handle missing values - document patterns
        missing_before = df.isnull().sum()
        
        # Remove rows with critical missing values
        critical_cols = ['temperature', 'humidity', 'wind_speed']
        df = df.dropna(subset=critical_cols, how='all')
        
        # Handle outliers
        if 'temperature' in df.columns:
            df = self._remove_outliers(df, 'temperature', method='iqr')
        if 'humidity' in df.columns:
            df = self._remove_outliers(df, 'humidity', method='iqr')
        if 'wind_speed' in df.columns:
            df = self._remove_outliers(df, 'wind_speed', method='iqr')
        
        # Validate ranges
        for col, (min_val, max_val) in self.valid_ranges.items():
            if col in df.columns:
                df = df[(df[col] >= min_val) & (df[col] <= max_val)]
        
        missing_after = df.isnull().sum()
        
        print(f"Weather data cleaning summary:")
        print(f"  Records before: {len(df) + (missing_before.sum() - missing_after.sum())}")
        print(f"  Records after: {len(df)}")
        print(f"  Missing values removed: {missing_before.sum() - missing_after.sum()}")
        
        return df
    
    def clean_air_quality_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean air quality data.
        
        Args:
            df: Raw air quality DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Standardize column names
        column_mapping = {
            'NO2': 'no2',
            'PM2.5': 'pm25',
            'PM25': 'pm25',
            'PM10': 'pm10',
            'O3': 'o3',
            'CO': 'co',
            'Value': 'value',
            'Concentration': 'value'
        }
        df = df.rename(columns=column_mapping)
        
        # Convert datetime columns
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Remove duplicates
        if 'datetime' in df.columns:
            df = df.drop_duplicates(subset=['city', 'datetime', 'station_code'], keep='first')
        else:
            df = df.drop_duplicates(subset=['city', 'date'], keep='first')
        
        # Handle missing values
        missing_before = df.isnull().sum()
        
        # Standardize units (convert to μg/m³ if needed)
        pollutant_cols = ['no2', 'pm25', 'pm10', 'o3']
        for col in pollutant_cols:
            if col in df.columns:
                # If unit column exists, convert accordingly
                if 'unit' in df.columns:
                    # Convert mg/m³ to μg/m³
                    mask = df['unit'].str.contains('mg', case=False, na=False)
                    df.loc[mask, col] = df.loc[mask, col] * 1000
                
                # Remove negative values
                df = df[df[col] >= 0]
        
        # Handle outliers using IQR method
        for col in pollutant_cols:
            if col in df.columns:
                df = self._remove_outliers(df, col, method='iqr')
        
        # Validate ranges
        for col, (min_val, max_val) in self.valid_ranges.items():
            if col in df.columns:
                df = df[(df[col] >= min_val) & (df[col] <= max_val)]
        
        missing_after = df.isnull().sum()
        
        print(f"Air quality data cleaning summary:")
        print(f"  Records before: {len(df) + (missing_before.sum() - missing_after.sum())}")
        print(f"  Records after: {len(df)}")
        print(f"  Missing values removed: {missing_before.sum() - missing_after.sum()}")
        
        return df
    
    def clean_traffic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean traffic data.
        
        Args:
            df: Raw traffic DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Standardize column names
        column_mapping = {
            'trafficIndex': 'traffic_index',
            'congestionLevel': 'congestion_level',
            'currentSpeed': 'current_speed',
            'freeFlowSpeed': 'free_flow_speed'
        }
        df = df.rename(columns=column_mapping)
        
        # Convert datetime columns
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Remove duplicates - check which columns exist
        duplicate_cols = []
        
        # Build subset list based on available columns
        if 'city' in df.columns:
            duplicate_cols.append('city')
        if 'city_key' in df.columns and 'city' not in df.columns:
            duplicate_cols.append('city_key')
        
        if 'datetime' in df.columns:
            duplicate_cols.append('datetime')
        elif 'date' in df.columns:
            duplicate_cols.append('date')
            # Only add 'hour' if it exists
            if 'hour' in df.columns:
                duplicate_cols.append('hour')
        
        # Remove duplicates only if we have columns to check
        if duplicate_cols:
            df = df.drop_duplicates(subset=duplicate_cols, keep='first')
        
        # Handle missing values
        missing_before = df.isnull().sum()
        
        # Calculate traffic_index from congestion_level if missing
        if 'traffic_index' not in df.columns and 'congestion_level' in df.columns:
            df['traffic_index'] = df['congestion_level'] * 100
        
        # Calculate congestion_level from traffic_index if missing
        if 'congestion_level' not in df.columns and 'traffic_index' in df.columns:
            df['congestion_level'] = df['traffic_index'] / 100
        
        # Handle outliers
        if 'traffic_index' in df.columns:
            df = self._remove_outliers(df, 'traffic_index', method='iqr')
        if 'congestion_level' in df.columns:
            df = self._remove_outliers(df, 'congestion_level', method='iqr')
        
        # Validate ranges
        for col, (min_val, max_val) in self.valid_ranges.items():
            if col in df.columns:
                df = df[(df[col] >= min_val) & (df[col] <= max_val)]
        
        missing_after = df.isnull().sum()
        
        print(f"Traffic data cleaning summary:")
        print(f"  Records before: {len(df) + (missing_before.sum() - missing_after.sum())}")
        print(f"  Records after: {len(df)}")
        print(f"  Missing values removed: {missing_before.sum() - missing_after.sum()}")
        
        return df
    
    def _remove_outliers(self, df: pd.DataFrame, column: str, method: str = 'iqr') -> pd.DataFrame:
        """
        Remove outliers from a column.
        
        Args:
            df: DataFrame
            column: Column name
            method: Method to use ('iqr' or 'zscore')
            
        Returns:
            DataFrame with outliers removed
        """
        if column not in df.columns:
            return df
        
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Don't remove if bounds are outside valid range
            if column in self.valid_ranges:
                min_val, max_val = self.valid_ranges[column]
                lower_bound = max(lower_bound, min_val)
                upper_bound = min(upper_bound, max_val)
            
            df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
            
        elif method == 'zscore':
            z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
            df = df[z_scores < 3]
        
        return df
    
    def get_missing_data_report(self, df: pd.DataFrame, name: str = "Dataset") -> Dict:
        """
        Generate missing data report.
        
        Args:
            df: DataFrame
            name: Dataset name
            
        Returns:
            Dictionary with missing data statistics
        """
        total_rows = len(df)
        missing_counts = df.isnull().sum()
        missing_percentages = (missing_counts / total_rows * 100).round(2)
        
        report = {
            'dataset': name,
            'total_rows': total_rows,
            'columns_with_missing': (missing_counts > 0).sum(),
            'missing_by_column': missing_counts[missing_counts > 0].to_dict(),
            'missing_percentages': missing_percentages[missing_percentages > 0].to_dict()
        }
        
        return report

