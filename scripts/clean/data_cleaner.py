"""
Data Cleaner - Bronze to Silver Layer
Cleans and validates raw data for analysis.
"""
import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class DataCleaner:
    """Cleans raw data and outputs to silver layer."""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.raw_dir = os.path.join(self.project_root, 'data', 'raw')
        self.silver_dir = os.path.join(self.project_root, 'data', 'silver')
        
        # Ensure silver directory exists
        os.makedirs(self.silver_dir, exist_ok=True)
        
        # Quality metrics
        self.metrics = {
            'weather': {},
            'air_quality': {},
            'traffic': {}
        }
    
    def get_latest_file(self, folder: str, pattern: str) -> str:
        """Get the most recent file matching pattern."""
        search_path = os.path.join(self.raw_dir, folder, pattern)
        files = glob.glob(search_path)
        if not files:
            raise FileNotFoundError(f"No files found matching {search_path}")
        return max(files, key=os.path.getmtime)
    
    def clean_weather(self) -> pd.DataFrame:
        """Clean weather data."""
        print("\n" + "="*60)
        print("CLEANING WEATHER DATA")
        print("="*60)
        
        # Load latest weather file
        file_path = self.get_latest_file('weather', 'weather_data_*.csv')
        print(f"Loading: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path)
        
        rows_before = len(df)
        print(f"Rows before: {rows_before:,}")
        
        # 1. Standardize data types
        print("\n[1/7] Standardizing data types...")
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['hour'] = df['hour'].astype('int8')
        
        # 2. Handle missing values
        print("[2/7] Handling missing values...")
        nulls_before = df.isnull().sum().sum()
        
        # Fill snow with 0 (no snow = 0mm)
        if 'snow' in df.columns:
            df['snow'] = df['snow'].fillna(0)
        
        # Drop columns with too many nulls
        cols_to_drop = []
        for col in ['wpgt', 'tsun', 'dwpt']:
            if col in df.columns:
                null_pct = df[col].isnull().sum() / len(df)
                if null_pct > 0.3:  # >30% missing
                    cols_to_drop.append(col)
                    print(f"   Dropping '{col}' ({null_pct*100:.1f}% missing)")
                else:
                    df[col] = df[col].fillna(df[col].median())
        
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        
        # Forward-fill remaining nulls
        df = df.fillna(method='ffill').fillna(method='bfill')
        nulls_after = df.isnull().sum().sum()
        print(f"   Nulls filled: {nulls_before - nulls_after:,}")
        
        # 3. Remove duplicates
        print("[3/7] Removing duplicates...")
        dupes_before = len(df)
        df = df.drop_duplicates(subset=['city_key', 'datetime'], keep='first')
        dupes_removed = dupes_before - len(df)
        print(f"   Duplicates removed: {dupes_removed:,}")
        
        # 4. Validate ranges
        print("[4/7] Validating ranges...")
        outliers_clipped = 0
        
        # Temperature: -40 to 50
        mask = (df['temperature'] < -40) | (df['temperature'] > 50)
        outliers_clipped += mask.sum()
        df['temperature'] = df['temperature'].clip(-40, 50)
        
        # Humidity: 0 to 100
        if 'humidity' in df.columns:
            mask = (df['humidity'] < 0) | (df['humidity'] > 100)
            outliers_clipped += mask.sum()
            df['humidity'] = df['humidity'].clip(0, 100)
        
        # Wind speed: 0 to 50 m/s
        if 'wind_speed' in df.columns:
            mask = df['wind_speed'] < 0
            outliers_clipped += mask.sum()
            df['wind_speed'] = df['wind_speed'].clip(0, 50)
        
        # Precipitation: >= 0
        if 'precipitation' in df.columns:
            mask = df['precipitation'] < 0
            outliers_clipped += mask.sum()
            df['precipitation'] = df['precipitation'].clip(0, None)
        
        print(f"   Outliers clipped: {outliers_clipped:,}")
        
        # 5. Derived features
        print("[5/7] Creating derived features...")
        df['month'] = df['datetime'].dt.month
        df['is_night'] = (df['hour'] < 6) | (df['hour'] >= 22)
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['is_weekday'] = df['day_of_week'] < 5
        
        # 6. Optimize memory
        print("[6/7] Optimizing memory...")
        float_cols = df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            df[col] = df[col].astype('float32')
        
        # 7. Sort and save
        print("[7/7] Sorting and preparing for save...")
        df = df.sort_values(['city_key', 'datetime']).reset_index(drop=True)
        
        rows_after = len(df)
        print(f"\nRows after: {rows_after:,}")
        print(f"Columns: {list(df.columns)}")
        
        # Store metrics
        self.metrics['weather'] = {
            'rows_before': rows_before,
            'rows_after': rows_after,
            'duplicates_removed': dupes_removed,
            'nulls_filled': nulls_before - nulls_after,
            'outliers_clipped': outliers_clipped
        }
        
        return df
    
    def clean_air_quality(self) -> pd.DataFrame:
        """Clean air quality data."""
        print("\n" + "="*60)
        print("CLEANING AIR QUALITY DATA")
        print("="*60)
        
        # Load latest air quality file
        file_path = self.get_latest_file('air_quality', 'air_quality_data_*.csv')
        print(f"Loading: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path)
        
        rows_before = len(df)
        print(f"Rows before: {rows_before:,}")
        
        # 1. Standardize data types
        print("\n[1/7] Standardizing data types...")
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['hour'] = df['hour'].astype('int8')
        
        # 2. Handle missing values
        print("[2/7] Handling missing values...")
        nulls_before = df.isnull().sum().sum()
        
        # Forward-fill pollutant values (they change gradually)
        for col in ['no2', 'pm10', 'o3']:
            if col in df.columns:
                df[col] = df.groupby('city_key')[col].transform(
                    lambda x: x.fillna(method='ffill').fillna(method='bfill')
                )
        
        # Fill any remaining with 0
        df = df.fillna(0)
        nulls_after = df.isnull().sum().sum()
        print(f"   Nulls filled: {nulls_before - nulls_after:,}")
        
        # 3. Remove duplicates
        print("[3/7] Removing duplicates...")
        dupes_before = len(df)
        df = df.drop_duplicates(subset=['city_key', 'datetime'], keep='first')
        dupes_removed = dupes_before - len(df)
        print(f"   Duplicates removed: {dupes_removed:,}")
        
        # 4. Validate ranges
        print("[4/7] Validating ranges...")
        outliers_clipped = 0
        
        for col in ['no2', 'pm10', 'o3']:
            if col in df.columns:
                # Clip to 0-500 µg/m³
                mask = (df[col] < 0) | (df[col] > 500)
                outliers_clipped += mask.sum()
                df[col] = df[col].clip(0, 500)
        
        print(f"   Outliers clipped: {outliers_clipped:,}")
        
        # 5. Drop unnecessary columns
        print("[5/7] Dropping unnecessary columns...")
        cols_to_drop = [c for c in ['station_name', 'station_id'] if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            print(f"   Dropped: {cols_to_drop}")
        
        # 6. Derived features
        print("[6/7] Creating derived features...")
        df['month'] = df['datetime'].dt.month
        df['is_night'] = (df['hour'] < 6) | (df['hour'] >= 22)
        df['day_of_week'] = df['datetime'].dt.dayofweek
        df['is_weekday'] = df['day_of_week'] < 5
        
        # Air Quality Index (simple average)
        pollutant_cols = [c for c in ['no2', 'pm10', 'o3'] if c in df.columns]
        if pollutant_cols:
            df['aqi_avg'] = df[pollutant_cols].mean(axis=1)
        
        # 7. Optimize and sort
        print("[7/7] Optimizing memory and sorting...")
        float_cols = df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            df[col] = df[col].astype('float32')
        
        df = df.sort_values(['city_key', 'datetime']).reset_index(drop=True)
        
        rows_after = len(df)
        print(f"\nRows after: {rows_after:,}")
        print(f"Columns: {list(df.columns)}")
        
        # Store metrics
        self.metrics['air_quality'] = {
            'rows_before': rows_before,
            'rows_after': rows_after,
            'duplicates_removed': dupes_removed,
            'nulls_filled': nulls_before - nulls_after,
            'outliers_clipped': outliers_clipped
        }
        
        return df
    
    def clean_traffic(self) -> pd.DataFrame:
        """Clean traffic data."""
        print("\n" + "="*60)
        print("CLEANING TRAFFIC DATA")
        print("="*60)
        
        # Load latest traffic file
        file_path = self.get_latest_file('traffic', 'traffic_data_*.csv')
        print(f"Loading: {os.path.basename(file_path)}")
        df = pd.read_csv(file_path)
        
        rows_before = len(df)
        print(f"Rows before: {rows_before:,}")
        
        # 1. Standardize data types
        print("\n[1/7] Standardizing data types...")
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['date'] = pd.to_datetime(df['date']).dt.date
        df['hour'] = df['hour'].astype('int8')
        df['day_of_week'] = df['day_of_week'].astype('int8')
        
        # Convert boolean columns
        for col in ['is_rush_hour', 'is_weekend', 'is_holiday']:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        # 2. Handle missing values
        print("[2/7] Handling missing values...")
        nulls_before = df.isnull().sum().sum()
        df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
        nulls_after = df.isnull().sum().sum()
        print(f"   Nulls filled: {nulls_before - nulls_after:,}")
        
        # 3. Remove duplicates
        print("[3/7] Removing duplicates...")
        dupes_before = len(df)
        df = df.drop_duplicates(subset=['city_key', 'datetime'], keep='first')
        dupes_removed = dupes_before - len(df)
        print(f"   Duplicates removed: {dupes_removed:,}")
        
        # 4. Validate ranges
        print("[4/7] Validating ranges...")
        outliers_clipped = 0
        
        # Traffic index: 0 to 100
        if 'traffic_index' in df.columns:
            mask = (df['traffic_index'] < 0) | (df['traffic_index'] > 100)
            outliers_clipped += mask.sum()
            df['traffic_index'] = df['traffic_index'].clip(0, 100)
        
        # Congestion level: 0 to 1
        if 'congestion_level' in df.columns:
            mask = (df['congestion_level'] < 0) | (df['congestion_level'] > 1)
            outliers_clipped += mask.sum()
            df['congestion_level'] = df['congestion_level'].clip(0, 1)
        
        # Speeds: >= 0
        for col in ['current_speed', 'free_flow_speed']:
            if col in df.columns:
                mask = df[col] < 0
                outliers_clipped += mask.sum()
                df[col] = df[col].clip(0, 200)
        
        print(f"   Outliers clipped: {outliers_clipped:,}")
        
        # 5. Drop unnecessary columns
        print("[5/7] Dropping unnecessary columns...")
        cols_to_drop = [c for c in ['data_source', 'confidence'] if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            print(f"   Dropped: {cols_to_drop}")
        
        # 6. Derived features
        print("[6/7] Creating derived features...")
        df['month'] = df['datetime'].dt.month
        df['is_night'] = (df['hour'] < 6) | (df['hour'] >= 22)
        df['is_weekday'] = df['day_of_week'] < 5
        
        # 7. Optimize and sort
        print("[7/7] Optimizing memory and sorting...")
        float_cols = df.select_dtypes(include=['float64']).columns
        for col in float_cols:
            df[col] = df[col].astype('float32')
        
        df = df.sort_values(['city_key', 'datetime']).reset_index(drop=True)
        
        rows_after = len(df)
        print(f"\nRows after: {rows_after:,}")
        print(f"Columns: {list(df.columns)}")
        
        # Store metrics
        self.metrics['traffic'] = {
            'rows_before': rows_before,
            'rows_after': rows_after,
            'duplicates_removed': dupes_removed,
            'nulls_filled': nulls_before - nulls_after,
            'outliers_clipped': outliers_clipped
        }
        
        return df
    
    def align_cities(self, weather_df: pd.DataFrame, aq_df: pd.DataFrame, 
                     traffic_df: pd.DataFrame) -> tuple:
        """Keep only cities that exist in all three datasets."""
        print("\n" + "="*60)
        print("ALIGNING CITIES ACROSS DATASETS")
        print("="*60)
        
        weather_cities = set(weather_df['city_key'].unique())
        aq_cities = set(aq_df['city_key'].unique())
        traffic_cities = set(traffic_df['city_key'].unique())
        
        print(f"Weather cities: {len(weather_cities)}")
        print(f"Air quality cities: {len(aq_cities)}")
        print(f"Traffic cities: {len(traffic_cities)}")
        
        # Find common cities
        common_cities = weather_cities & aq_cities & traffic_cities
        print(f"\nCommon cities: {len(common_cities)}")
        
        # Filter to common cities only
        weather_df = weather_df[weather_df['city_key'].isin(common_cities)]
        aq_df = aq_df[aq_df['city_key'].isin(common_cities)]
        traffic_df = traffic_df[traffic_df['city_key'].isin(common_cities)]
        
        # Report dropped cities
        dropped_weather = weather_cities - common_cities
        dropped_aq = aq_cities - common_cities
        dropped_traffic = traffic_cities - common_cities
        
        if dropped_weather:
            print(f"\nDropped from weather: {len(dropped_weather)} cities")
        if dropped_aq:
            print(f"Dropped from air quality: {len(dropped_aq)} cities")
        if dropped_traffic:
            print(f"Dropped from traffic: {len(dropped_traffic)} cities")
        
        print(f"\nFinal row counts:")
        print(f"  Weather: {len(weather_df):,}")
        print(f"  Air quality: {len(aq_df):,}")
        print(f"  Traffic: {len(traffic_df):,}")
        
        return weather_df, aq_df, traffic_df
    
    def save_cleaned_data(self, df: pd.DataFrame, name: str):
        """Save cleaned dataframe to silver layer."""
        csv_path = os.path.join(self.silver_dir, f'{name}_cleaned.csv')
        parquet_path = os.path.join(self.silver_dir, f'{name}_cleaned.parquet')
        
        # Convert date to string for parquet compatibility
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)
        
        df.to_csv(csv_path, index=False)
        df.to_parquet(parquet_path, index=False)
        
        print(f"Saved: {name}_cleaned.csv ({len(df):,} rows)")
    
    def print_summary(self):
        """Print cleaning summary."""
        print("\n" + "="*60)
        print("CLEANING SUMMARY")
        print("="*60)
        
        for dataset, metrics in self.metrics.items():
            if metrics:
                print(f"\n{dataset.upper()}:")
                print(f"  Rows: {metrics['rows_before']:,} -> {metrics['rows_after']:,}")
                print(f"  Duplicates removed: {metrics['duplicates_removed']:,}")
                print(f"  Nulls filled: {metrics['nulls_filled']:,}")
                print(f"  Outliers clipped: {metrics['outliers_clipped']:,}")
    
    def run(self):
        """Run the full cleaning pipeline."""
        print("="*60)
        print("DATA CLEANING PIPELINE (Bronze -> Silver)")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Clean each dataset
        weather_df = self.clean_weather()
        aq_df = self.clean_air_quality()
        traffic_df = self.clean_traffic()
        
        # Align cities
        weather_df, aq_df, traffic_df = self.align_cities(weather_df, aq_df, traffic_df)
        
        # Save cleaned data
        print("\n" + "="*60)
        print("SAVING CLEANED DATA")
        print("="*60)
        
        self.save_cleaned_data(weather_df, 'weather')
        self.save_cleaned_data(aq_df, 'air_quality')
        self.save_cleaned_data(traffic_df, 'traffic')
        
        # Print summary
        self.print_summary()
        
        print("\n" + "="*60)
        print("CLEANING COMPLETE!")
        print("="*60)
        print(f"Output: {self.silver_dir}")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return weather_df, aq_df, traffic_df


def main():
    cleaner = DataCleaner()
    cleaner.run()


if __name__ == "__main__":
    main()
