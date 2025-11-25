"""
Simple script to read and analyze air quality CSV data.
"""

import pandas as pd
from pathlib import Path

# Find the most recent CSV file
air_quality_dir = Path('data/raw/air_quality')
csv_files = list(air_quality_dir.glob('air_quality_data_*.csv'))

if not csv_files:
    print("No air quality CSV files found!")
    exit(1)

# Get the most recent file
latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
print(f"Reading: {latest_file}\n")

# Read the CSV
df = pd.read_csv(latest_file)

# Parse datetime column
df['datetime'] = pd.to_datetime(df['datetime'])
df['date'] = pd.to_datetime(df['date'])

print("=" * 60)
print("AIR QUALITY DATA SUMMARY")
print("=" * 60)
print(f"\nTotal records: {len(df):,}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
print(f"\nCities: {', '.join(df['city'].unique())}")
print(f"Stations: {df['station_name'].nunique()}")
print(f"\nColumns: {', '.join(df.columns.tolist())}")

print("\n" + "=" * 60)
print("SAMPLE DATA (First 10 rows)")
print("=" * 60)
print(df.head(10).to_string())

print("\n" + "=" * 60)
print("STATISTICS BY CITY")
print("=" * 60)
city_stats = df.groupby('city').agg({
    'no2': ['count', 'mean', 'max'],
    'pm10': ['count', 'mean', 'max'],
    'o3': ['count', 'mean', 'max']
}).round(2)
print(city_stats)

print("\n" + "=" * 60)
print("DAILY AVERAGES (Sample)")
print("=" * 60)
daily_avg = df.groupby(['city', 'date']).agg({
    'no2': 'mean',
    'pm10': 'mean',
    'o3': 'mean'
}).round(2)
print(daily_avg.head(15))

print("\n" + "=" * 60)
print("QUICK FILTERING EXAMPLES")
print("=" * 60)

# Example 1: Filter by city
berlin_data = df[df['city'] == 'Berlin']
print(f"\nBerlin records: {len(berlin_data)}")

# Example 2: Filter by date
from datetime import datetime
jan_1 = df[df['date'] == '2024-01-01']
print(f"January 1st records: {len(jan_1)}")

# Example 3: High pollution days
high_no2 = df[df['no2'] > 50]
print(f"High NO2 (>50 µg/m³) records: {len(high_no2)}")

# Example 4: Get specific station
if len(df) > 0:
    station_158 = df[df['station_id'] == 158]
    print(f"Station 158 records: {len(station_158)}")

print("\n" + "=" * 60)
print("Done! You can now use this data for analysis.")
print("=" * 60)

