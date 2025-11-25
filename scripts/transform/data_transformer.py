"""
Data transformation module.

Handles:
- Unit standardization
- Temporal alignment
- Timezone conversion
- Category creation
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional
import pytz
import holidays

from scripts.utils.helpers import convert_to_cet

class DataTransformer:
    """Transform and standardize data from all sources."""
    
    def __init__(self):
        """Initialize data transformer."""
        # German holidays
        self.german_holidays = holidays.Germany(years=range(2023, 2025))
        
    def standardize_units(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """
        Standardize units across datasets.
        
        Standard units:
        - Temperature: °C
        - Humidity: %
        - Wind speed: m/s
        - Pressure: hPa
        - Pollution: μg/m³
        - Traffic: index (0-100)
        
        Args:
            df: DataFrame
            data_type: Type of data ('weather', 'air_quality', 'traffic')
            
        Returns:
            DataFrame with standardized units
        """
        df = df.copy()
        
        if data_type == 'weather':
            # Temperature: convert Fahrenheit to Celsius if needed
            if 'temperature' in df.columns:
                if df['temperature'].max() > 100:  # Likely Fahrenheit
                    df['temperature'] = (df['temperature'] - 32) * 5/9
            
            # Wind speed: convert km/h to m/s if needed
            if 'wind_speed' in df.columns:
                if df['wind_speed'].max() > 50:  # Likely km/h
                    df['wind_speed'] = df['wind_speed'] / 3.6
            
            # Pressure: convert various units to hPa
            if 'pressure' in df.columns:
                if df['pressure'].min() < 10:  # Likely in bars
                    df['pressure'] = df['pressure'] * 1000
                elif df['pressure'].min() < 100:  # Likely in kPa
                    df['pressure'] = df['pressure'] * 10
        
        elif data_type == 'air_quality':
            # Pollution: ensure all in μg/m³
            pollutant_cols = ['no2', 'pm25', 'pm10', 'o3', 'co']
            
            for col in pollutant_cols:
                if col in df.columns:
                    # CO is sometimes in mg/m³, others should be μg/m³
                    if col == 'co':
                        # Check if values are in mg/m³ (typically < 10)
                        if df[col].max() < 10:
                            df[col] = df[col] * 1000  # Convert to μg/m³
                    else:
                        # Check if values are in mg/m³ (typically < 1)
                        if df[col].max() < 1:
                            df[col] = df[col] * 1000  # Convert to μg/m³
        
        elif data_type == 'traffic':
            # Traffic index: ensure 0-100 scale
            if 'traffic_index' in df.columns:
                if df['traffic_index'].max() <= 1:
                    df['traffic_index'] = df['traffic_index'] * 100
        
        return df
    
    def align_temporal_resolution(self, df: pd.DataFrame, resolution: str = 'hourly') -> pd.DataFrame:
        """
        Align data to consistent temporal resolution.
        
        Args:
            df: DataFrame with datetime column
            resolution: Target resolution ('hourly', 'daily')
            
        Returns:
            DataFrame with aligned temporal resolution
        """
        df = df.copy()
        
        # Ensure datetime column exists
        if 'datetime' not in df.columns and 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
        else:
            raise ValueError("No datetime or date column found")
        
        # Set datetime as index for resampling
        df = df.set_index('datetime')
        
        if resolution == 'hourly':
            # Resample to hourly (forward fill for missing hours)
            df = df.resample('H').first()
            df = df.fillna(method='ffill', limit=1)
        
        elif resolution == 'daily':
            # Aggregate to daily
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            
            # For weather: use mean for most, max for temp_max, min for temp_min
            agg_dict = {}
            for col in numeric_cols:
                if 'max' in col.lower():
                    agg_dict[col] = 'max'
                elif 'min' in col.lower():
                    agg_dict[col] = 'min'
                else:
                    agg_dict[col] = 'mean'
            
            # For non-numeric columns, take first value
            for col in df.columns:
                if col not in numeric_cols:
                    agg_dict[col] = 'first'
            
            df = df.resample('D').agg(agg_dict)
        
        # Reset index
        df = df.reset_index()
        df['date'] = df['datetime'].dt.date
        
        return df
    
    def convert_timezone(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert all timestamps to CET/CEST.
        
        Args:
            df: DataFrame with datetime column
            
        Returns:
            DataFrame with CET/CEST timestamps
        """
        df = df.copy()
        
        datetime_cols = ['datetime', 'timestamp', 'date']
        
        for col in datetime_cols:
            if col in df.columns:
                if col == 'date':
                    # Convert date to datetime with CET
                    df[col] = pd.to_datetime(df[col])
                    df[col] = df[col].dt.tz_localize('Europe/Berlin', ambiguous='NaT', nonexistent='shift_forward')
                else:
                    # Convert datetime to CET
                    if df[col].dtype == 'object':
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    if df[col].dt.tz is None:
                        # Assume UTC if no timezone
                        df[col] = df[col].dt.tz_localize('UTC')
                    
                    df[col] = df[col].dt.tz_convert('Europe/Berlin')
        
        return df
    
    def create_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create categorical variables.
        
        Categories:
        - Weather conditions: cold/mild/warm
        - Traffic levels: low/medium/high
        - Day type: weekday/weekend
        - Season: winter/spring/summer/autumn
        - Rush hour: morning/evening/none
        
        Args:
            df: DataFrame
            
        Returns:
            DataFrame with categorical variables
        """
        df = df.copy()
        
        # Ensure datetime column
        if 'datetime' not in df.columns and 'date' in df.columns:
            df['datetime'] = pd.to_datetime(df['date'])
        elif 'datetime' not in df.columns:
            raise ValueError("No datetime or date column found")
        
        # Day of week
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['day_type'] = df['is_weekend'].map({0: 'weekday', 1: 'weekend'})
        
        # Season
        df['month'] = df['datetime'].dt.month
        df['season'] = df['month'].map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'autumn', 10: 'autumn', 11: 'autumn'
        })
        
        # Weather categories
        if 'temperature' in df.columns:
            df['weather_condition'] = pd.cut(
                df['temperature'],
                bins=[-np.inf, 5, 20, np.inf],
                labels=['cold', 'mild', 'warm']
            )
        
        # Traffic categories
        if 'traffic_index' in df.columns:
            df['traffic_level'] = pd.cut(
                df['traffic_index'],
                bins=[0, 30, 70, 100],
                labels=['low', 'medium', 'high']
            )
        
        # Rush hour indicator
        if 'hour' not in df.columns:
            df['hour'] = df['datetime'].dt.hour
        
        df['rush_hour'] = 'none'
        df.loc[(df['hour'] >= 7) & (df['hour'] <= 9), 'rush_hour'] = 'morning'
        df.loc[(df['hour'] >= 17) & (df['hour'] <= 19), 'rush_hour'] = 'evening'
        
        # Holiday indicator
        df['is_holiday'] = df['datetime'].dt.date.isin(self.german_holidays).astype(int)
        
        return df
    
    def create_rolling_averages(self, df: pd.DataFrame, 
                                columns: List[str],
                                windows: List[int] = [7, 30]) -> pd.DataFrame:
        """
        Create rolling averages for specified columns.
        
        Args:
            df: DataFrame
            columns: List of column names to create rolling averages for
            windows: List of window sizes in days
            
        Returns:
            DataFrame with rolling average columns
        """
        df = df.copy()
        
        # Ensure sorted by datetime
        if 'datetime' in df.columns:
            df = df.sort_values('datetime')
            df = df.set_index('datetime')
        else:
            raise ValueError("datetime column required for rolling averages")
        
        # Group by city if available
        groupby_col = 'city' if 'city' in df.columns else None
        
        for col in columns:
            if col not in df.columns:
                continue
            
            for window in windows:
                col_name = f"{col}_rolling_{window}d"
                
                if groupby_col:
                    df[col_name] = df.groupby(groupby_col)[col].rolling(
                        window=f'{window}D',
                        min_periods=1
                    ).mean().reset_index(0, drop=True)
                else:
                    df[col_name] = df[col].rolling(
                        window=f'{window}D',
                        min_periods=1
                    ).mean()
        
        df = df.reset_index()
        return df
    
    def create_interaction_terms(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create interaction terms between variables.
        
        Args:
            df: DataFrame
            
        Returns:
            DataFrame with interaction terms
        """
        df = df.copy()
        
        # High temperature + high traffic
        if 'temperature' in df.columns and 'traffic_index' in df.columns:
            temp_high = df['temperature'] > df['temperature'].quantile(0.75)
            traffic_high = df['traffic_index'] > df['traffic_index'].quantile(0.75)
            df['high_temp_high_traffic'] = (temp_high & traffic_high).astype(int)
        
        # Wind speed * pollution (wind can disperse pollution)
        if 'wind_speed' in df.columns and 'no2' in df.columns:
            df['wind_no2_interaction'] = df['wind_speed'] * df['no2']
        
        if 'wind_speed' in df.columns and 'pm25' in df.columns:
            df['wind_pm25_interaction'] = df['wind_speed'] * df['pm25']
        
        # Humidity * temperature (affects perceived temperature)
        if 'humidity' in df.columns and 'temperature' in df.columns:
            df['humidity_temp_interaction'] = df['humidity'] * df['temperature']
        
        return df

