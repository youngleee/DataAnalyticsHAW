"""
Helper script to load manually downloaded EEA air quality CSV files.

Usage:
    python scripts/load_air_quality_data.py
    
Or use in Python:
    from scripts.collect.air_quality_collector import AirQualityCollector
    
    collector = AirQualityCollector()
    
    # Load single file
    df = collector.download_from_csv('path/to/berlin_data.csv', 'berlin')
    
    # Load multiple files
    filepaths = {
        'berlin': 'data/downloads/berlin_air_quality.csv',
        'munich': 'data/downloads/munich_air_quality.csv',
        'hamburg': 'data/downloads/hamburg_air_quality.csv',
        'cologne': 'data/downloads/cologne_air_quality.csv',
        'frankfurt': 'data/downloads/frankfurt_air_quality.csv'
    }
    df = collector.load_multiple_csv_files(filepaths)
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.collect.air_quality_collector import AirQualityCollector
from scripts.utils.config import get_cities

def main():
    """Interactive script to load EEA air quality CSV files."""
    print("=" * 60)
    print("EEA Air Quality Data Loader")
    print("=" * 60)
    print("\nThis script helps you load manually downloaded EEA air quality CSV files.")
    print("\nSteps:")
    print("1. Download CSV files from EEA portal:")
    print("   https://www.eea.europa.eu/data-and-maps/data/air-quality-observations")
    print("2. Place CSV files in a directory (e.g., data/downloads/)")
    print("3. Run this script and provide the file paths")
    print("\n" + "=" * 60)
    
    collector = AirQualityCollector()
    cities = get_cities()
    
    # Check if downloads directory exists
    downloads_dir = Path('data/downloads')
    if downloads_dir.exists():
        print(f"\nFound downloads directory: {downloads_dir}")
        csv_files = list(downloads_dir.glob('*.csv'))
        if csv_files:
            print(f"Found {len(csv_files)} CSV files:")
            for f in csv_files:
                print(f"  - {f.name}")
    
    print("\n" + "=" * 60)
    print("Option 1: Load files interactively")
    print("=" * 60)
    
    filepaths = {}
    for city_key, city_info in cities.items():
        print(f"\n{city_info['name']} ({city_key}):")
        filepath = input(f"  Enter CSV file path (or press Enter to skip): ").strip()
        if filepath and os.path.exists(filepath):
            filepaths[city_key] = filepath
        elif filepath:
            print(f"  ⚠ File not found: {filepath}")
    
    if not filepaths:
        print("\n⚠ No files provided. Exiting.")
        print("\nExample usage in Python:")
        print("""
from scripts.collect.air_quality_collector import AirQualityCollector

collector = AirQualityCollector()

# Load single file
df = collector.download_from_csv('data/downloads/berlin_air_quality.csv', 'berlin')

# Or load multiple files
filepaths = {
    'berlin': 'data/downloads/berlin_air_quality.csv',
    'munich': 'data/downloads/munich_air_quality.csv'
}
df = collector.load_multiple_csv_files(filepaths)
""")
        return
    
    print(f"\nLoading {len(filepaths)} file(s)...")
    df = collector.load_multiple_csv_files(filepaths)
    
    if not df.empty:
        print(f"\n✓ Successfully loaded and saved air quality data!")
        print(f"  Total records: {len(df)}")
        print(f"  Cities: {df['city'].nunique() if 'city' in df.columns else 'N/A'}")
        print(f"  Date range: {df['date'].min() if 'date' in df.columns else 'N/A'} to {df['date'].max() if 'date' in df.columns else 'N/A'}")
        print(f"\nFiles saved in data/raw/air_quality/ (both CSV and Parquet formats)")
        print("You can now inspect the CSV file before running the cleaning step.")
    else:
        print("\n⚠ No data was loaded. Please check your file paths and formats.")

if __name__ == "__main__":
    main()

