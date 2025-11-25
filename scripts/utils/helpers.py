"""
Helper functions for data processing.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional
import pytz

# German timezone
CET = pytz.timezone('Europe/Berlin')

def standardize_city_name(city_name: str) -> str:
    """
    Standardize city names to handle variations.
    
    Args:
        city_name: City name in various formats
        
    Returns:
        Standardized city name (lowercase key)
    """
    city_mapping = {
        'münchen': 'munich',
        'munich': 'munich',
        'köln': 'cologne',
        'cologne': 'cologne',
        'frankfurt am main': 'frankfurt',
        'frankfurt': 'frankfurt',
        'berlin': 'berlin',
        'hamburg': 'hamburg'
    }
    
    city_lower = city_name.lower().strip()
    return city_mapping.get(city_lower, city_lower)

def convert_to_cet(dt: datetime, tz_aware: bool = True) -> datetime:
    """
    Convert datetime to CET/CEST timezone.
    
    Args:
        dt: Datetime object
        tz_aware: Whether to return timezone-aware datetime
        
    Returns:
        Datetime in CET/CEST
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.utc.localize(dt)
    
    cet_dt = dt.astimezone(CET)
    
    if not tz_aware:
        return cet_dt.replace(tzinfo=None)
    
    return cet_dt

def parse_date_range(start_date: str, end_date: str) -> List[datetime]:
    """
    Generate list of dates between start and end (inclusive).
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        List of datetime objects
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    dates = []
    current = start
    while current <= end:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates

def save_dataframe(df: pd.DataFrame, filepath: str, format: str = 'parquet'):
    """
    Save dataframe to file in specified format.
    
    Args:
        df: DataFrame to save
        filepath: Output file path
        format: File format ('parquet', 'csv', 'json')
    """
    if format == 'parquet':
        df.to_parquet(filepath, index=False, engine='pyarrow')
    elif format == 'csv':
        df.to_csv(filepath, index=False)
    elif format == 'json':
        df.to_json(filepath, orient='records', date_format='iso')
    else:
        raise ValueError(f"Unsupported format: {format}")

def load_dataframe(filepath: str) -> pd.DataFrame:
    """
    Load dataframe from file (auto-detect format).
    
    Args:
        filepath: Input file path
        
    Returns:
        DataFrame
    """
    if filepath.endswith('.parquet'):
        return pd.read_parquet(filepath)
    elif filepath.endswith('.csv'):
        return pd.read_csv(filepath)
    elif filepath.endswith('.json'):
        return pd.read_json(filepath, orient='records')
    else:
        raise ValueError(f"Cannot determine file format for: {filepath}")

def handle_rate_limit(response, max_retries: int = 3, wait_time: int = 60):
    """
    Handle API rate limiting.
    
    Args:
        response: HTTP response object
        max_retries: Maximum number of retries
        wait_time: Wait time in seconds between retries
        
    Returns:
        Boolean indicating if request should be retried
    """
    if response.status_code == 429:  # Too Many Requests
        return True
    return False

