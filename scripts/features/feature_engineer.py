"""
Feature engineering module.

Creates derived variables and aggregations for analysis.
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import datetime

class FeatureEngineer:
    """Engineer features from merged dataset."""
    
    def __init__(self):
        """Initialize feature engineer."""
        pass
    
    def create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based features.
        
        Args:
            df: DataFrame with datetime column
            
        Returns:
            DataFrame with time features
        """
        df = df.copy()
        
        if 'datetime' not in df.columns:
            raise ValueError("datetime column required")
        
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Basic time features
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        df['day'] = df['datetime'].dt.day
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['day_of_year'] = df['datetime'].dt.dayofyear
        df['week_of_year'] = df['datetime'].dt.isocalendar().week
        
        # Cyclical encoding for periodic features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    def create_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create weather-derived features.
        
        Args:
            df: DataFrame with weather columns
            
        Returns:
            DataFrame with weather features
        """
        df = df.copy()
        
        # Heat index (feels like temperature)
        if 'temperature' in df.columns and 'humidity' in df.columns:
            # Simplified heat index calculation
            T = df['temperature']
            H = df['humidity']
            df['heat_index'] = (
                -8.78469475556 +
                1.61139411 * T +
                2.33854883889 * H +
                -0.14611605 * T * H +
                -0.012308094 * (T ** 2) +
                -0.0164248277778 * (H ** 2) +
                0.002211732 * (T ** 2) * H +
                0.00072546 * T * (H ** 2) +
                -0.000003582 * (T ** 2) * (H ** 2)
            )
        
        # Wind chill (for cold temperatures)
        if 'temperature' in df.columns and 'wind_speed' in df.columns:
            T = df['temperature']
            V = df['wind_speed']
            # Wind chill formula (valid for T < 10°C and V > 4.8 km/h)
            mask = (T < 10) & (V > 1.33)  # 1.33 m/s = 4.8 km/h
            df['wind_chill'] = T.copy()
            df.loc[mask, 'wind_chill'] = (
                13.12 + 0.6215 * T[mask] - 11.37 * (V[mask] ** 0.16) +
                0.3965 * T[mask] * (V[mask] ** 0.16)
            )
        
        # Temperature difference (max - min)
        if 'temp_max' in df.columns and 'temp_min' in df.columns:
            df['temp_range'] = df['temp_max'] - df['temp_min']
        
        # Pressure change rate (if multiple timestamps)
        if 'pressure' in df.columns and 'datetime' in df.columns:
            df = df.sort_values('datetime')
            df['pressure_change'] = df.groupby('city_key')['pressure'].diff()
            df['pressure_change_rate'] = df.groupby('city_key')['pressure'].diff() / df.groupby('city_key')['datetime'].diff().dt.total_seconds() * 3600
        
        return df
    
    def create_pollution_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create pollution-derived features.
        
        Args:
            df: DataFrame with pollution columns
            
        Returns:
            DataFrame with pollution features
        """
        df = df.copy()
        
        # Air Quality Index (AQI) - simplified version
        # Real AQI calculations are more complex and vary by country
        if 'pm25' in df.columns:
            # PM2.5 AQI (US EPA scale)
            df['pm25_aqi'] = df['pm25'].apply(self._calculate_pm25_aqi)
        
        if 'pm10' in df.columns:
            # PM10 AQI
            df['pm10_aqi'] = df['pm10'].apply(self._calculate_pm10_aqi)
        
        # Combined pollution index
        pollution_cols = ['no2', 'pm25', 'pm10', 'o3']
        available_cols = [col for col in pollution_cols if col in df.columns]
        
        if available_cols:
            # Normalize each pollutant (0-1 scale) and average
            normalized = pd.DataFrame()
            for col in available_cols:
                col_max = df[col].quantile(0.95)  # Use 95th percentile as max
                normalized[col] = df[col] / col_max
                normalized[col] = normalized[col].clip(0, 1)
            
            df['pollution_index'] = normalized.mean(axis=1)
        
        # Pollution ratios
        if 'pm25' in df.columns and 'pm10' in df.columns:
            df['pm25_pm10_ratio'] = df['pm25'] / (df['pm10'] + 1e-6)  # Avoid division by zero
        
        return df
    
    def _calculate_pm25_aqi(self, pm25: float) -> float:
        """Calculate PM2.5 AQI (US EPA scale)."""
        if pd.isna(pm25):
            return np.nan
        
        if pm25 <= 12:
            return (50 / 12) * pm25
        elif pm25 <= 35.4:
            return 50 + ((100 - 50) / (35.4 - 12)) * (pm25 - 12)
        elif pm25 <= 55.4:
            return 100 + ((150 - 100) / (55.4 - 35.4)) * (pm25 - 35.4)
        elif pm25 <= 150.4:
            return 150 + ((200 - 150) / (150.4 - 55.4)) * (pm25 - 55.4)
        elif pm25 <= 250.4:
            return 200 + ((300 - 200) / (250.4 - 150.4)) * (pm25 - 150.4)
        else:
            return 300 + ((400 - 300) / (500 - 250.4)) * (pm25 - 250.4)
    
    def _calculate_pm10_aqi(self, pm10: float) -> float:
        """Calculate PM10 AQI (US EPA scale)."""
        if pd.isna(pm10):
            return np.nan
        
        if pm10 <= 54:
            return (50 / 54) * pm10
        elif pm10 <= 154:
            return 50 + ((100 - 50) / (154 - 54)) * (pm10 - 54)
        elif pm10 <= 254:
            return 100 + ((150 - 100) / (254 - 154)) * (pm10 - 154)
        elif pm10 <= 354:
            return 150 + ((200 - 150) / (354 - 254)) * (pm10 - 254)
        elif pm10 <= 424:
            return 200 + ((300 - 200) / (424 - 354)) * (pm10 - 354)
        else:
            return 300 + ((400 - 300) / (604 - 424)) * (pm10 - 424)
    
    def create_lag_features(self, df: pd.DataFrame, 
                           columns: List[str],
                           lags: List[int] = [1, 2, 3, 6, 12, 24]) -> pd.DataFrame:
        """
        Create lagged features.
        
        Args:
            df: DataFrame
            columns: Columns to create lags for
            lags: List of lag periods (in hours)
            
        Returns:
            DataFrame with lag features
        """
        df = df.copy()
        
        if 'datetime' not in df.columns or 'city_key' not in df.columns:
            raise ValueError("datetime and city_key columns required for lag features")
        
        df = df.sort_values(['city_key', 'datetime'])
        
        for col in columns:
            if col not in df.columns:
                continue
            
            for lag in lags:
                df[f'{col}_lag_{lag}h'] = df.groupby('city_key')[col].shift(lag)
        
        return df
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features.
        
        Args:
            df: Merged DataFrame
            
        Returns:
            DataFrame with all engineered features
        """
        print("Creating time features...")
        df = self.create_time_features(df)
        
        print("Creating weather features...")
        df = self.create_weather_features(df)
        
        print("Creating pollution features...")
        df = self.create_pollution_features(df)
        
        # Create lag features for key variables
        print("Creating lag features...")
        lag_columns = ['no2', 'pm25', 'pm10', 'o3', 'temperature', 'traffic_index']
        available_lag_cols = [col for col in lag_columns if col in df.columns]
        if available_lag_cols:
            df = self.create_lag_features(df, available_lag_cols, lags=[1, 6, 24])
        
        print(f"Feature engineering complete. Total columns: {len(df.columns)}")
        
        return df

