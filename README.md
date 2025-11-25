# Air Quality Data Preparation Project

This project prepares data for analyzing how weather conditions and traffic density affect air pollution in major German cities.

> **📖 For detailed team documentation, see [TEAM_DOCUMENTATION.md](TEAM_DOCUMENTATION.md)**

## Research Question
How do weather conditions (temperature, humidity, wind) and traffic density relate to air pollutants (NO2, PM2.5, PM10, O3) in major German cities?

## Target Cities
- Berlin
- Munich (München)
- Hamburg
- Cologne (Köln)
- Frankfurt am Main

## Time Period
2023-2024 (or maximum available data)

## Project Structure

```
DataAnalyticsHAW/
├── data/
│   ├── raw/              # Raw data from APIs
│   └── processed/        # Cleaned and merged datasets
├── scripts/
│   ├── collect/          # Data collection scripts
│   ├── clean/            # Data cleaning scripts
│   ├── transform/        # Data transformation scripts
│   └── integrate/        # Data integration scripts
├── outputs/
│   ├── reports/          # Data quality reports
│   └── datasets/         # Final datasets
├── config.example.env     # Configuration template
└── requirements.txt      # Python dependencies
```

## Setup

### 1. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Or use the provided setup scripts:
- **Windows**: Run `setup_venv.bat`
- **Linux/Mac**: Run `chmod +x setup_venv.sh && ./setup_venv.sh`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

```bash
# Windows
copy config.example.env .env

# Linux/Mac
cp config.example.env .env
```

Then edit `.env` and add your API keys.

### 4. Run the Pipeline

**Run full pipeline:**
```bash
python scripts/main.py --all
```

**Or run step by step:**
```bash
python scripts/main.py --collect
python scripts/main.py --clean
python scripts/main.py --transform
python scripts/main.py --integrate
python scripts/main.py --features
python scripts/main.py --report
```

## Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Comprehensive guide to all APIs, data formats, and usage examples
- **[Team Documentation](TEAM_DOCUMENTATION.md)** - Project structure and team guidelines
- **[Quick Start Guide](QUICKSTART.md)** - Get started quickly

## Data Sources

### 1. Meteostat API
- **Purpose**: Historical weather data (temperature, humidity, wind speed, precipitation)
- **API Key**: Not required (free service)
- **Note**: Meteostat provides free access to historical weather data from weather stations worldwide
- **Website**: https://meteostat.net/

### 2. European Environment Agency (EEA)
- **Purpose**: Air quality data (NO2, PM2.5, PM10, O3, CO) from monitoring stations
- **Access**: Data portal at https://www.eea.europa.eu/data-and-maps/data/air-quality-observations
- **Note**: May require manual CSV download. The script includes a `download_from_csv()` method for loading manually downloaded files.

### 3. TomTom Traffic Index
- **Purpose**: Traffic congestion levels for German cities
- **API Key**: Optional (get from https://developer.tomtom.com/)
- **Note**: If API is unavailable, the script can generate synthetic traffic data based on realistic patterns.

## Workflow

### Step 1: Data Collection
```bash
python scripts/main.py --collect
```
- Fetches weather data from OpenWeatherMap
- Attempts to download air quality data from EEA
- Collects traffic data from TomTom (or generates synthetic data)

**Output**: Raw data files in `data/raw/`

### Step 2: Data Cleaning
```bash
python scripts/main.py --clean
```
- Handles missing values
- Detects and removes outliers (IQR method)
- Removes duplicates
- Validates data ranges

**Output**: Cleaned data files in `data/processed/`

### Step 3: Data Transformation
```bash
python scripts/main.py --transform
```
- Standardizes units (temperature to °C, pollution to μg/m³, etc.)
- Aligns temporal resolution (hourly)
- Converts timestamps to CET/CEST
- Creates categorical variables (season, day type, etc.)

**Output**: Transformed data files in `data/processed/`

### Step 4: Data Integration
```bash
python scripts/main.py --integrate
```
- Merges weather, air quality, and traffic datasets
- Handles geographic matching between stations
- Creates city-specific datasets

**Output**: Merged dataset in `data/processed/merged_dataset.parquet`

### Step 5: Feature Engineering
```bash
python scripts/main.py --features
```
- Creates time-based features (hour, day, season, etc.)
- Calculates rolling averages (7-day, 30-day)
- Creates interaction terms
- Generates lag features

**Output**: Final dataset in `outputs/datasets/final_dataset.parquet`

### Step 6: Report Generation
```bash
python scripts/main.py --report
```
- Generates summary statistics
- Creates data quality visualizations
- Documents missing data patterns
- Creates data dictionary

**Output**: Reports in `outputs/reports/` and data dictionary in `outputs/data_dictionary.md`

### Run Full Pipeline
```bash
python scripts/main.py --all
```

## Manual Data Collection

### EEA Air Quality Data
If automatic collection fails, manually download CSV files from the EEA portal:

1. Visit: https://www.eea.europa.eu/data-and-maps/data/air-quality-observations
2. Select Germany, your city, and pollutants
3. Download CSV files
4. Use the `download_from_csv()` method in `air_quality_collector.py`

### Alternative Weather Data
For historical weather data, consider using Meteostat (free):

```python
from meteostat import Point, Daily
from datetime import datetime

# Example for Berlin
location = Point(52.5200, 13.4050)
data = Daily(location, datetime(2023, 1, 1), datetime(2024, 12, 31))
data = data.fetch()
```

## Configuration

Edit `.env` file with your settings:

```env
# API Keys
OPENWEATHERMAP_API_KEY=your_key_here
TOMTOM_API_KEY=your_key_here  # Optional

# Date Range
START_DATE=2023-01-01
END_DATE=2024-12-31

# City Coordinates (already configured, but can be adjusted)
CITY_BERLIN=52.5200,13.4050
CITY_MUNICH=48.1351,11.5820
CITY_HAMBURG=53.5511,10.0000
CITY_COLOGNE=50.9375,6.9603
CITY_FRANKFURT=50.1109,8.6821
```

## Output Files

### Datasets
- `outputs/datasets/final_dataset.parquet` - Complete merged dataset
- `outputs/datasets/final_dataset.csv` - CSV version
- `outputs/datasets/{city}_data.parquet` - City-specific datasets

### Reports
- `outputs/reports/data_quality_report.md` - Markdown report
- `outputs/reports/data_quality_report_summary_stats.csv` - Summary statistics
- `outputs/reports/data_quality_report_missing_data.csv` - Missing data analysis
- `outputs/reports/*.png` - Visualization files

### Documentation
- `outputs/data_dictionary.md` - Complete variable documentation

## Troubleshooting

### API Rate Limiting
- The scripts include rate limiting delays
- If you encounter 429 errors, increase delays in collector scripts

### Missing Data
- Check data quality reports for missing data patterns
- Consider imputation strategies documented in reports
- Some time periods may have incomplete coverage

### EEA Data Access
- EEA data may require manual download
- Use the `download_from_csv()` method after manual download
- Ensure CSV files follow EEA format

### Memory Issues
- For large date ranges, process data in chunks
- Use parquet format for efficient storage
- Consider processing cities separately

## Data Quality

The pipeline includes comprehensive data quality checks:
- Outlier detection (IQR method)
- Range validation
- Missing data analysis
- Temporal completeness checks
- Unit standardization verification

All quality issues are documented in the generated reports.

