"""
Main orchestration script for data preparation pipeline.

Usage:
    python scripts/main.py --collect          # Collect data only
    python scripts/main.py --clean            # Clean data only
    python scripts/main.py --transform        # Transform data only
    python scripts/main.py --integrate        # Integrate data only
    python scripts/main.py --features         # Engineer features only
    python scripts/main.py --report           # Generate reports only
    python scripts/main.py --all              # Run full pipeline
"""
import argparse
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scripts.utils.config import get_date_range, ensure_data_directories
from scripts.collect.weather_collector import WeatherCollector
from scripts.collect.air_quality_collector import AirQualityCollector
from scripts.collect.traffic_collector import TrafficCollector
from scripts.clean.data_cleaner import DataCleaner
from scripts.transform.data_transformer import DataTransformer
from scripts.integrate.data_integrator import DataIntegrator
from scripts.features.feature_engineer import FeatureEngineer
from scripts.reports.quality_report import QualityReportGenerator
from scripts.data_dictionary import generate_data_dictionary

def collect_data():
    """Collect data from all sources."""
    print("\n" + "=" * 60)
    print("STEP 1: DATA COLLECTION")
    print("=" * 60)
    
    start_date, end_date = get_date_range()
    ensure_data_directories()
    
    # Collect weather data
    print("\n--- Collecting Weather Data ---")
    weather_collector = WeatherCollector()
    weather_df = weather_collector.collect_weather_data(start_date, end_date)
    if not weather_df.empty:
        weather_collector.save_weather_data(weather_df)
        print("\n✓ Weather data saved. You can inspect the CSV file before running cleaning.")
    else:
        print("⚠ No weather data collected.")
    
    # Collect air quality data
    print("\n--- Collecting Air Quality Data ---")
    aq_collector = AirQualityCollector()
    
    # Use UBA API (official German government source - free, no API key required)
    print("Using UBA (Umweltbundesamt) API - Official German Government Source")
    aq_df = aq_collector.collect_air_quality_data(start_date, end_date, use_uba=True)
    
    if not aq_df.empty:
        aq_collector.save_air_quality_data(aq_df)
        print("\n✓ Air quality data saved. You can inspect the CSV file before running cleaning.")
    else:
        print("\n⚠ No air quality data collected.")
        print("The pipeline will continue without air quality data for now.")
    
    # Collect traffic data
    print("\n--- Collecting Traffic Data ---")
    traffic_collector = TrafficCollector()
    # Use synthetic traffic data (TomTom API doesn't provide historical data on free tier)
    # Synthetic data is based on realistic patterns:
    # - Weekday vs weekend patterns
    # - City size (larger cities = more congestion)
    # - German holidays
    # - Day-to-day variation
    print("Note: Using synthetic traffic data (historical data requires paid API)")
    traffic_df = traffic_collector.collect_traffic_data(start_date, end_date, use_synthetic=True)
    if not traffic_df.empty:
        traffic_collector.save_traffic_data(traffic_df)
        print("\n✓ Traffic data saved (synthetic). You can inspect the CSV file before running cleaning.")
    else:
        print("⚠ No traffic data collected.")
    
    print("\n" + "=" * 60)
    print("Data collection complete!")
    print("=" * 60)
    print("\nRaw data files saved in:")
    print("  - data/raw/weather/ (CSV and Parquet)")
    print("  - data/raw/air_quality/ (CSV and Parquet)")
    print("  - data/raw/traffic/ (CSV and Parquet)")
    print("\nYou can now inspect the CSV files before running the cleaning step.")
    print("Run: python scripts/main.py --clean (or --all to continue)")

def clean_data():
    """Clean collected data."""
    print("\n" + "=" * 60)
    print("STEP 2: DATA CLEANING")
    print("=" * 60)
    
    cleaner = DataCleaner()
    
    # Find latest data files
    from scripts.integrate.data_integrator import DataIntegrator
    integrator = DataIntegrator()
    datasets = integrator.load_raw_datasets()
    
    cleaned_datasets = {}
    
    if 'weather' in datasets and not datasets['weather'].empty:
        print("\n--- Cleaning Weather Data ---")
        cleaned_datasets['weather'] = cleaner.clean_weather_data(datasets['weather'])
        from scripts.utils.helpers import save_dataframe
        save_dataframe(cleaned_datasets['weather'], 'data/processed/weather_cleaned.parquet')
    else:
        print("\n--- Skipping Weather Data Cleaning (no data available) ---")
    
    if 'air_quality' in datasets and not datasets['air_quality'].empty:
        print("\n--- Cleaning Air Quality Data ---")
        cleaned_datasets['air_quality'] = cleaner.clean_air_quality_data(datasets['air_quality'])
        save_dataframe(cleaned_datasets['air_quality'], 'data/processed/air_quality_cleaned.parquet')
    else:
        print("\n--- Skipping Air Quality Data Cleaning (no data available) ---")
        print("NOTE: EEA air quality data requires manual download.")
        print("The pipeline will continue without air quality data.")
    
    if 'traffic' in datasets and not datasets['traffic'].empty:
        print("\n--- Cleaning Traffic Data ---")
        cleaned_datasets['traffic'] = cleaner.clean_traffic_data(datasets['traffic'])
        save_dataframe(cleaned_datasets['traffic'], 'data/processed/traffic_cleaned.parquet')
    else:
        print("\n--- Skipping Traffic Data Cleaning (no data available) ---")
    
    print("\nData cleaning complete!")

def transform_data():
    """Transform cleaned data."""
    print("\n" + "=" * 60)
    print("STEP 3: DATA TRANSFORMATION")
    print("=" * 60)
    
    transformer = DataTransformer()
    from scripts.utils.helpers import load_dataframe, save_dataframe
    
    # Load cleaned data
    datasets = {}
    if os.path.exists('data/processed/weather_cleaned.parquet'):
        datasets['weather'] = load_dataframe('data/processed/weather_cleaned.parquet')
    if os.path.exists('data/processed/air_quality_cleaned.parquet'):
        datasets['air_quality'] = load_dataframe('data/processed/air_quality_cleaned.parquet')
    if os.path.exists('data/processed/traffic_cleaned.parquet'):
        datasets['traffic'] = load_dataframe('data/processed/traffic_cleaned.parquet')
    
    transformed_datasets = {}
    
    if 'weather' in datasets:
        print("\n--- Transforming Weather Data ---")
        df = transformer.standardize_units(datasets['weather'], 'weather')
        df = transformer.convert_timezone(df)
        df = transformer.align_temporal_resolution(df, resolution='hourly')
        df = transformer.create_categories(df)
        transformed_datasets['weather'] = df
        save_dataframe(df, 'data/processed/weather_transformed.parquet')
    
    if 'air_quality' in datasets:
        print("\n--- Transforming Air Quality Data ---")
        df = transformer.standardize_units(datasets['air_quality'], 'air_quality')
        df = transformer.convert_timezone(df)
        df = transformer.align_temporal_resolution(df, resolution='hourly')
        df = transformer.create_categories(df)
        transformed_datasets['air_quality'] = df
        save_dataframe(df, 'data/processed/air_quality_transformed.parquet')
    
    if 'traffic' in datasets:
        print("\n--- Transforming Traffic Data ---")
        df = transformer.standardize_units(datasets['traffic'], 'traffic')
        df = transformer.convert_timezone(df)
        df = transformer.align_temporal_resolution(df, resolution='hourly')
        df = transformer.create_categories(df)
        transformed_datasets['traffic'] = df
        save_dataframe(df, 'data/processed/traffic_transformed.parquet')
    
    print("\nData transformation complete!")

def integrate_data():
    """Integrate transformed datasets."""
    print("\n" + "=" * 60)
    print("STEP 4: DATA INTEGRATION")
    print("=" * 60)
    
    integrator = DataIntegrator()
    
    # Load transformed data
    from scripts.utils.helpers import load_dataframe
    
    weather_df = pd.DataFrame()
    aq_df = pd.DataFrame()
    traffic_df = pd.DataFrame()
    
    if os.path.exists('data/processed/weather_transformed.parquet'):
        weather_df = load_dataframe('data/processed/weather_transformed.parquet')
    if os.path.exists('data/processed/air_quality_transformed.parquet'):
        aq_df = load_dataframe('data/processed/air_quality_transformed.parquet')
    if os.path.exists('data/processed/traffic_transformed.parquet'):
        traffic_df = load_dataframe('data/processed/traffic_transformed.parquet')
    
    if weather_df.empty and aq_df.empty and traffic_df.empty:
        print("No transformed data found. Please run transformation step first.")
        return
    
    # Merge datasets
    merged_df = integrator.merge_datasets(weather_df, aq_df, traffic_df, merge_strategy='outer')
    
    # Save merged dataset
    integrator.save_merged_dataset(merged_df, 'data/processed/merged_dataset.parquet')
    
    # Create city-specific datasets
    integrator.create_city_specific_datasets(merged_df)
    
    print("\nData integration complete!")

def engineer_features():
    """Engineer features from merged dataset."""
    print("\n" + "=" * 60)
    print("STEP 5: FEATURE ENGINEERING")
    print("=" * 60)
    
    from scripts.utils.helpers import load_dataframe, save_dataframe
    
    if not os.path.exists('data/processed/merged_dataset.parquet'):
        print("Merged dataset not found. Please run integration step first.")
        return
    
    merged_df = load_dataframe('data/processed/merged_dataset.parquet')
    
    # Create rolling averages
    transformer = DataTransformer()
    pollution_cols = ['no2', 'pm25', 'pm10', 'o3']
    available_cols = [col for col in pollution_cols if col in merged_df.columns]
    if available_cols:
        merged_df = transformer.create_rolling_averages(merged_df, available_cols + ['temperature', 'traffic_index'])
    
    # Create interaction terms
    merged_df = transformer.create_interaction_terms(merged_df)
    
    # Engineer additional features
    feature_engineer = FeatureEngineer()
    merged_df = feature_engineer.create_all_features(merged_df)
    
    # Save final dataset
    save_dataframe(merged_df, 'outputs/datasets/final_dataset.parquet')
    save_dataframe(merged_df, 'outputs/datasets/final_dataset.csv')
    
    print("\nFeature engineering complete!")
    print(f"Final dataset saved with {len(merged_df.columns)} columns and {len(merged_df)} records.")

def generate_reports():
    """Generate data quality reports and data dictionary."""
    print("\n" + "=" * 60)
    print("STEP 6: REPORT GENERATION")
    print("=" * 60)
    
    from scripts.utils.helpers import load_dataframe
    
    # Load final dataset
    if os.path.exists('outputs/datasets/final_dataset.parquet'):
        final_df = load_dataframe('outputs/datasets/final_dataset.parquet')
    elif os.path.exists('data/processed/merged_dataset.parquet'):
        final_df = load_dataframe('data/processed/merged_dataset.parquet')
    else:
        print("No dataset found for reporting. Please run previous steps first.")
        return
    
    # Generate quality report
    print("\n--- Generating Data Quality Report ---")
    report_generator = QualityReportGenerator()
    report_generator.generate_full_report(final_df, 'data_quality_report')
    
    # Generate data dictionary
    print("\n--- Generating Data Dictionary ---")
    generate_data_dictionary(final_df, 'outputs/data_dictionary.md')
    
    print("\nReport generation complete!")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Air Quality Data Preparation Pipeline')
    parser.add_argument('--collect', action='store_true', help='Collect data from all sources')
    parser.add_argument('--clean', action='store_true', help='Clean collected data')
    parser.add_argument('--transform', action='store_true', help='Transform cleaned data')
    parser.add_argument('--integrate', action='store_true', help='Integrate transformed datasets')
    parser.add_argument('--features', action='store_true', help='Engineer features')
    parser.add_argument('--report', action='store_true', help='Generate reports')
    parser.add_argument('--all', action='store_true', help='Run full pipeline')
    
    args = parser.parse_args()
    
    if args.all:
        collect_data()
        clean_data()
        transform_data()
        integrate_data()
        engineer_features()
        generate_reports()
    else:
        if args.collect:
            collect_data()
        if args.clean:
            clean_data()
        if args.transform:
            transform_data()
        if args.integrate:
            integrate_data()
        if args.features:
            engineer_features()
        if args.report:
            generate_reports()
        
        if not any([args.collect, args.clean, args.transform, 
                   args.integrate, args.features, args.report]):
            parser.print_help()

if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    main()

