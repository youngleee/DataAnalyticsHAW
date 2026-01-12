"""
Gold Layer - Unified Dataset Creation
Merges cleaned weather, air quality, and traffic data into one analysis-ready file.
"""
import os
import sys
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class GoldLayerBuilder:
    """Creates unified Gold layer dataset from Silver layer files."""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.silver_dir = os.path.join(self.project_root, 'data', 'silver')
        self.gold_dir = os.path.join(self.project_root, 'data', 'gold')
        
        # Ensure gold directory exists
        os.makedirs(self.gold_dir, exist_ok=True)
    
    def load_silver_data(self) -> tuple:
        """Load all cleaned silver layer datasets."""
        print("\n" + "="*60)
        print("LOADING SILVER LAYER DATA")
        print("="*60)
        
        # Load weather
        weather_path = os.path.join(self.silver_dir, 'weather_cleaned.parquet')
        weather_df = pd.read_parquet(weather_path)
        print(f"Weather: {len(weather_df):,} rows, {len(weather_df.columns)} columns")
        
        # Load air quality
        aq_path = os.path.join(self.silver_dir, 'air_quality_cleaned.parquet')
        aq_df = pd.read_parquet(aq_path)
        print(f"Air Quality: {len(aq_df):,} rows, {len(aq_df.columns)} columns")
        
        # Load traffic
        traffic_path = os.path.join(self.silver_dir, 'traffic_cleaned.parquet')
        traffic_df = pd.read_parquet(traffic_path)
        print(f"Traffic: {len(traffic_df):,} rows, {len(traffic_df.columns)} columns")
        
        return weather_df, aq_df, traffic_df
    
    def merge_datasets(self, weather_df: pd.DataFrame, aq_df: pd.DataFrame, 
                       traffic_df: pd.DataFrame) -> pd.DataFrame:
        """Merge all three datasets on city_key and datetime."""
        print("\n" + "="*60)
        print("MERGING DATASETS")
        print("="*60)
        
        # Ensure datetime columns are the same type
        weather_df['datetime'] = pd.to_datetime(weather_df['datetime'])
        aq_df['datetime'] = pd.to_datetime(aq_df['datetime'])
        traffic_df['datetime'] = pd.to_datetime(traffic_df['datetime'])
        
        # Prepare weather data - select relevant columns and rename
        weather_cols = ['city_key', 'datetime', 'city', 'lat', 'lon', 
                       'temperature', 'humidity', 'precipitation', 'wind_speed', 
                       'wind_direction', 'pressure', 'weather_code',
                       'date', 'hour', 'month', 'day_of_week', 'is_night', 'is_weekday']
        weather_cols = [c for c in weather_cols if c in weather_df.columns]
        weather_subset = weather_df[weather_cols].copy()
        
        # Prepare air quality data - select relevant columns
        aq_cols = ['city_key', 'datetime', 'no2', 'pm10', 'o3', 'aqi_avg']
        aq_cols = [c for c in aq_cols if c in aq_df.columns]
        aq_subset = aq_df[aq_cols].copy()
        
        # Prepare traffic data - select relevant columns
        traffic_cols = ['city_key', 'datetime', 'current_speed', 'free_flow_speed',
                       'congestion_level', 'traffic_index', 'is_rush_hour', 
                       'is_weekend', 'is_holiday', 'holiday_name']
        traffic_cols = [c for c in traffic_cols if c in traffic_df.columns]
        traffic_subset = traffic_df[traffic_cols].copy()
        
        print(f"\nMerge keys: city_key + datetime")
        print(f"Weather subset: {len(weather_subset):,} rows")
        print(f"Air quality subset: {len(aq_subset):,} rows")
        print(f"Traffic subset: {len(traffic_subset):,} rows")
        
        # Merge weather + air quality
        print("\nStep 1: Merging weather + air quality...")
        merged = pd.merge(
            weather_subset, 
            aq_subset, 
            on=['city_key', 'datetime'], 
            how='inner'
        )
        print(f"   Result: {len(merged):,} rows")
        
        # Merge with traffic
        print("Step 2: Merging with traffic...")
        merged = pd.merge(
            merged, 
            traffic_subset, 
            on=['city_key', 'datetime'], 
            how='inner'
        )
        print(f"   Result: {len(merged):,} rows")
        
        return merged
    
    def add_gold_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Gold layer specific features."""
        print("\n" + "="*60)
        print("ADDING GOLD LAYER FEATURES")
        print("="*60)
        
        # Time period classification
        def get_time_period(hour):
            if 6 <= hour < 10:
                return 'morning_rush'
            elif 10 <= hour < 16:
                return 'midday'
            elif 16 <= hour < 20:
                return 'evening_rush'
            elif 20 <= hour < 23:
                return 'evening'
            else:
                return 'night'
        
        df['time_period'] = df['hour'].apply(get_time_period)
        print("Added: time_period (morning_rush, midday, evening_rush, evening, night)")
        
        # Season (for Jan-Mar, it's winter/early spring)
        def get_season(month):
            if month in [12, 1, 2]:
                return 'winter'
            elif month in [3, 4, 5]:
                return 'spring'
            elif month in [6, 7, 8]:
                return 'summer'
            else:
                return 'autumn'
        
        df['season'] = df['month'].apply(get_season)
        print("Added: season (winter, spring)")
        
        # Weather severity
        if 'precipitation' in df.columns:
            df['is_rainy'] = df['precipitation'] > 0.5
            print("Added: is_rainy (precipitation > 0.5mm)")
        
        # Temperature categories
        if 'temperature' in df.columns:
            df['temp_category'] = pd.cut(
                df['temperature'], 
                bins=[-50, 0, 10, 20, 50],
                labels=['freezing', 'cold', 'mild', 'warm']
            )
            print("Added: temp_category (freezing, cold, mild, warm)")
        
        # Air quality categories based on AQI average
        if 'aqi_avg' in df.columns:
            df['air_quality_level'] = pd.cut(
                df['aqi_avg'],
                bins=[0, 25, 50, 100, 500],
                labels=['good', 'moderate', 'unhealthy', 'hazardous']
            )
            print("Added: air_quality_level (good, moderate, unhealthy, hazardous)")
        
        # Traffic severity
        if 'congestion_level' in df.columns:
            df['traffic_level'] = pd.cut(
                df['congestion_level'],
                bins=[0, 0.3, 0.6, 1.0],
                labels=['free_flow', 'moderate', 'congested']
            )
            print("Added: traffic_level (free_flow, moderate, congested)")
        
        return df
    
    def validate_gold_data(self, df: pd.DataFrame):
        """Validate the Gold layer dataset."""
        print("\n" + "="*60)
        print("VALIDATING GOLD LAYER DATA")
        print("="*60)
        
        # Check for nulls
        null_counts = df.isnull().sum()
        nulls = null_counts[null_counts > 0]
        if len(nulls) > 0:
            print("\nColumns with nulls:")
            for col, count in nulls.items():
                pct = count / len(df) * 100
                print(f"   {col}: {count:,} ({pct:.1f}%)")
        else:
            print("[OK] No null values")
        
        # Check date range
        print(f"\nDate range: {df['datetime'].min()} to {df['datetime'].max()}")
        
        # Check cities
        cities = df['city_key'].nunique()
        print(f"Cities: {cities}")
        
        # Check records per city
        records_per_city = df.groupby('city_key').size()
        print(f"Records per city: min={records_per_city.min()}, max={records_per_city.max()}, avg={records_per_city.mean():.0f}")
        
        # Data completeness check
        expected_hours = 24 * 91  # 91 days (Jan-Mar)
        completeness = records_per_city.mean() / expected_hours * 100
        print(f"Data completeness: ~{completeness:.1f}% of expected hourly records")
    
    def save_gold_data(self, df: pd.DataFrame):
        """Save the Gold layer dataset."""
        print("\n" + "="*60)
        print("SAVING GOLD LAYER DATA")
        print("="*60)
        
        # Ensure date is string for parquet
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str)
        
        # Convert categorical to string for parquet compatibility
        for col in df.select_dtypes(include=['category']).columns:
            df[col] = df[col].astype(str)
        
        # Save CSV
        csv_path = os.path.join(self.gold_dir, 'unified_data.csv')
        df.to_csv(csv_path, index=False)
        print(f"Saved: unified_data.csv ({len(df):,} rows)")
        
        # Save Parquet
        parquet_path = os.path.join(self.gold_dir, 'unified_data.parquet')
        df.to_parquet(parquet_path, index=False)
        print(f"Saved: unified_data.parquet")
        
        # File sizes
        csv_size = os.path.getsize(csv_path) / (1024 * 1024)
        parquet_size = os.path.getsize(parquet_path) / (1024 * 1024)
        print(f"\nFile sizes:")
        print(f"   CSV: {csv_size:.1f} MB")
        print(f"   Parquet: {parquet_size:.1f} MB")
    
    def print_summary(self, df: pd.DataFrame):
        """Print Gold layer summary."""
        print("\n" + "="*60)
        print("GOLD LAYER SUMMARY")
        print("="*60)
        
        print(f"\nDataset Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
        
        print(f"\nColumn Categories:")
        
        # Identify columns
        id_cols = ['city_key', 'city', 'datetime', 'date']
        geo_cols = ['lat', 'lon']
        time_cols = ['hour', 'month', 'day_of_week', 'is_night', 'is_weekday', 
                    'time_period', 'season', 'is_rush_hour', 'is_weekend', 'is_holiday']
        weather_cols = ['temperature', 'humidity', 'precipitation', 'wind_speed', 
                       'wind_direction', 'pressure', 'weather_code', 'is_rainy', 'temp_category']
        aq_cols = ['no2', 'pm10', 'o3', 'aqi_avg', 'air_quality_level']
        traffic_cols = ['current_speed', 'free_flow_speed', 'congestion_level', 
                       'traffic_index', 'traffic_level', 'holiday_name']
        
        actual_cols = set(df.columns)
        print(f"   Identifiers: {len([c for c in id_cols if c in actual_cols])}")
        print(f"   Geographic: {len([c for c in geo_cols if c in actual_cols])}")
        print(f"   Time features: {len([c for c in time_cols if c in actual_cols])}")
        print(f"   Weather metrics: {len([c for c in weather_cols if c in actual_cols])}")
        print(f"   Air quality metrics: {len([c for c in aq_cols if c in actual_cols])}")
        print(f"   Traffic metrics: {len([c for c in traffic_cols if c in actual_cols])}")
        
        print(f"\nAll columns:")
        for i, col in enumerate(df.columns):
            print(f"   {i+1:2}. {col} ({df[col].dtype})")
    
    def run(self) -> pd.DataFrame:
        """Run the Gold layer creation pipeline."""
        print("="*60)
        print("GOLD LAYER CREATION PIPELINE (Silver -> Gold)")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load silver data
        weather_df, aq_df, traffic_df = self.load_silver_data()
        
        # Merge datasets
        gold_df = self.merge_datasets(weather_df, aq_df, traffic_df)
        
        # Add gold features
        gold_df = self.add_gold_features(gold_df)
        
        # Validate
        self.validate_gold_data(gold_df)
        
        # Save
        self.save_gold_data(gold_df)
        
        # Summary
        self.print_summary(gold_df)
        
        print("\n" + "="*60)
        print("GOLD LAYER CREATION COMPLETE!")
        print("="*60)
        print(f"Output: {self.gold_dir}")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return gold_df


def main():
    builder = GoldLayerBuilder()
    builder.run()


if __name__ == "__main__":
    main()

