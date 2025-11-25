# Air Quality Data Preparation Project - Team Documentation

## Project Overview

This project prepares data for analyzing how weather conditions and traffic density affect air pollution in major German cities.

**Research Question:** How do weather conditions (temperature, humidity, wind) and traffic density relate to air pollutants (NO2, PM2.5, PM10, O3) in major German cities?

**Target Cities:**
- Berlin
- Munich (München)
- Hamburg
- Cologne (Köln)
- Frankfurt am Main

**Time Period:** January 1-7, 2023 (configurable in `.env` file)

---

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Settings

```bash
# Copy configuration template
copy config.example.env .env  # Windows
# or
cp config.example.env .env    # Linux/Mac

# Edit .env file - currently no API keys needed!
# Just set your date range:
START_DATE=2023-01-01
END_DATE=2023-01-07
```

### 3. Run the Pipeline

```bash
# Run full pipeline
python scripts/main.py --all

# Or run step by step
python scripts/main.py --collect    # Collect data
python scripts/main.py --clean      # Clean data
python scripts/main.py --transform  # Transform data
python scripts/main.py --integrate  # Integrate datasets
python scripts/main.py --features   # Engineer features
python scripts/main.py --report     # Generate reports
```

---

## Data Sources

### 1. Weather Data - Meteostat API ✅

- **Status:** Working
- **API Key:** Not required (free service)
- **Source:** https://meteostat.net/
- **Data Collected:**
  - Temperature (°C)
  - Humidity (%)
  - Wind speed (m/s)
  - Atmospheric pressure (hPa)
  - Precipitation (mm)
- **How it works:** Automatically finds nearest weather stations to each city and retrieves historical data

### 2. Air Quality Data - OpenAQ/EEA ⚠️

- **Status:** OpenAQ API deprecated, manual download recommended
- **API Key:** Not required (but API doesn't work reliably)
- **Sources:**
  - OpenAQ API (attempted, but v2 deprecated, v3 may have issues)
  - EEA Portal (manual CSV download - **RECOMMENDED**)
- **Data Needed:**
  - NO2 (μg/m³)
  - PM2.5 (μg/m³)
  - PM10 (μg/m³)
  - O3 (μg/m³)
  - CO (μg/m³)

**How to get air quality data:**

1. **Manual Download (Recommended):**
   - Visit: https://www.eea.europa.eu/data-and-maps/data/air-quality-observations
   - Select: Germany → Your city → Pollutants → Date range
   - Download CSV files
   - Use helper script:
     ```bash
     python scripts/load_air_quality_data.py
     ```
   - Or in Python:
     ```python
     from scripts.collect.air_quality_collector import AirQualityCollector
     collector = AirQualityCollector()
     df = collector.download_from_csv('path/to/file.csv', 'berlin')
     ```

2. **Files will be saved in:** `data/raw/air_quality/` (both CSV and Parquet)

### 3. Traffic Data - Synthetic Generation ✅

- **Status:** Working (synthetic data)
- **API Key:** Optional (TomTom API, but synthetic data is used by default)
- **Data Generated:**
  - Traffic index (0-100)
  - Congestion level (0-1)
  - Realistic patterns based on:
    - Day of week (weekday vs weekend)
    - Time of day (rush hours: 7-9 AM, 5-7 PM)
    - Seasonal variations

---

## Project Structure

```
DataAnalyticsHAW/
├── data/
│   ├── raw/                    # Raw data from APIs (CSV + Parquet)
│   │   ├── weather/
│   │   ├── air_quality/
│   │   └── traffic/
│   └── processed/              # Cleaned and transformed data
├── scripts/
│   ├── collect/                # Data collection scripts
│   │   ├── weather_collector.py      # Meteostat API
│   │   ├── air_quality_collector.py  # OpenAQ/EEA
│   │   └── traffic_collector.py      # Synthetic data
│   ├── clean/                  # Data cleaning
│   │   └── data_cleaner.py
│   ├── transform/              # Data transformation
│   │   └── data_transformer.py
│   ├── integrate/              # Data integration
│   │   └── data_integrator.py
│   ├── features/               # Feature engineering
│   │   └── feature_engineer.py
│   ├── reports/                # Quality reports
│   │   └── quality_report.py
│   ├── utils/                  # Helper functions
│   ├── main.py                 # Main pipeline orchestrator
│   ├── load_air_quality_data.py  # Helper for manual CSV loading
│   └── data_dictionary.py     # Generate data dictionary
├── outputs/
│   ├── reports/                # Data quality reports
│   └── datasets/               # Final datasets
├── config.example.env          # Configuration template
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview
```

---

## Data Pipeline Workflow

### Step 1: Data Collection

**Command:** `python scripts/main.py --collect`

**What it does:**
- Collects weather data from Meteostat
- Attempts OpenAQ API (usually fails)
- Generates synthetic traffic data
- Saves all data in `data/raw/` (both CSV and Parquet)

**Output files:**
- `data/raw/weather/weather_data_TIMESTAMP.csv`
- `data/raw/weather/weather_data_TIMESTAMP.parquet`
- `data/raw/traffic/traffic_data_TIMESTAMP.csv`
- `data/raw/traffic/traffic_data_TIMESTAMP.parquet`

**Note:** Air quality CSV files need to be loaded manually (see above)

### Step 2: Data Cleaning

**Command:** `python scripts/main.py --clean`

**What it does:**
- Handles missing values
- Removes outliers (IQR method)
- Removes duplicates
- Validates data ranges
- Standardizes column names

**Output files:**
- `data/processed/weather_cleaned.parquet`
- `data/processed/air_quality_cleaned.parquet` (if available)
- `data/processed/traffic_cleaned.parquet`

### Step 3: Data Transformation

**Command:** `python scripts/main.py --transform`

**What it does:**
- Standardizes units (temperature to °C, pollution to μg/m³, etc.)
- Aligns temporal resolution (hourly)
- Converts timestamps to CET/CEST
- Creates categorical variables (season, day type, rush hour, etc.)

**Output files:**
- `data/processed/weather_transformed.parquet`
- `data/processed/air_quality_transformed.parquet` (if available)
- `data/processed/traffic_transformed.parquet`

### Step 4: Data Integration

**Command:** `python scripts/main.py --integrate`

**What it does:**
- Merges weather, air quality, and traffic datasets
- Handles geographic matching between stations
- Creates city-specific datasets
- Aligns data by city and timestamp

**Output files:**
- `data/processed/merged_dataset.parquet`
- `outputs/datasets/{city}_data.parquet` (one per city)

### Step 5: Feature Engineering

**Command:** `python scripts/main.py --features`

**What it does:**
- Creates time-based features (hour, day, season, etc.)
- Calculates rolling averages (7-day, 30-day)
- Creates interaction terms
- Generates lag features

**Output files:**
- `outputs/datasets/final_dataset.parquet`
- `outputs/datasets/final_dataset.csv`

### Step 6: Report Generation

**Command:** `python scripts/main.py --report`

**What it does:**
- Generates summary statistics
- Creates data quality visualizations
- Documents missing data patterns
- Creates data dictionary

**Output files:**
- `outputs/reports/data_quality_report.md`
- `outputs/reports/data_quality_report_summary_stats.csv`
- `outputs/reports/data_quality_report_missing_data.csv`
- `outputs/reports/*.png` (visualizations)
- `outputs/data_dictionary.md`

---

## Working with Air Quality Data

Since OpenAQ API is unreliable, here's how to handle air quality data:

### Option 1: Use Helper Script (Recommended)

1. Download CSV files from EEA portal
2. Place them in `data/downloads/` (or any directory)
3. Run:
   ```bash
   python scripts/load_air_quality_data.py
   ```
4. Follow the interactive prompts to specify file paths

### Option 2: Python Code

```python
from scripts.collect.air_quality_collector import AirQualityCollector

collector = AirQualityCollector()

# Load single file
df = collector.download_from_csv('data/downloads/berlin_air_quality.csv', 'berlin')

# Load multiple files
filepaths = {
    'berlin': 'data/downloads/berlin_air_quality.csv',
    'munich': 'data/downloads/munich_air_quality.csv',
    'hamburg': 'data/downloads/hamburg_air_quality.csv',
    'cologne': 'data/downloads/cologne_air_quality.csv',
    'frankfurt': 'data/downloads/frankfurt_air_quality.csv'
}
df = collector.load_multiple_csv_files(filepaths)
```

### Option 3: Continue Without Air Quality Data

The pipeline will work with just weather and traffic data. You can add air quality data later and re-run the integration step.

---

## Inspecting Data

All raw data is saved in **both CSV and Parquet formats**:

- **CSV files:** Easy to open in Excel, Google Sheets, or text editors
- **Parquet files:** Efficient storage for processing

**Location:** `data/raw/{source}/`

**File naming:** `{source}_data_YYYYMMDD_HHMMSS.{format}`

You can inspect CSV files before running the cleaning step to verify data quality.

---

## Configuration

Edit `.env` file to change settings:

```env
# Date Range
START_DATE=2023-01-01
END_DATE=2023-01-07

# City Coordinates (already configured)
CITY_BERLIN=52.5200,13.4050
CITY_MUNICH=48.1351,11.5820
CITY_HAMBURG=53.5511,10.0000
CITY_COLOGNE=50.9375,6.9603
CITY_FRANKFURT=50.1109,8.6821
```

---

## Known Issues & Solutions

### Issue 1: OpenAQ API Returns 410 Errors

**Problem:** OpenAQ API v2 is deprecated, v3 may have different structure

**Solution:** Use manual CSV download from EEA portal (see "Working with Air Quality Data" above)

### Issue 2: Missing Air Quality Data

**Problem:** No air quality data collected

**Solution:** 
- Pipeline continues without it
- Add air quality data later using CSV download method
- Re-run integration step after adding data

### Issue 3: Traffic Data is Synthetic

**Problem:** Real traffic API may not be available

**Solution:** 
- Synthetic data is realistic and based on patterns
- If you have TomTom API key, add it to `.env`:
  ```env
  TOMTOM_API_KEY=your_key_here
  ```

---

## Data Quality Checks

The pipeline includes comprehensive quality checks:

1. **Outlier Detection:** IQR method (removes values outside 1.5 × IQR)
2. **Range Validation:** Ensures values are within expected ranges
3. **Missing Data Analysis:** Documents missing data patterns
4. **Temporal Completeness:** Checks for gaps in time series
5. **Unit Standardization:** Verifies all units are correct

All quality issues are documented in the generated reports.

---

## Output Files Summary

### Raw Data (for inspection)
- `data/raw/weather/*.csv` - Weather data
- `data/raw/air_quality/*.csv` - Air quality data (if loaded)
- `data/raw/traffic/*.csv` - Traffic data

### Processed Data
- `data/processed/*_cleaned.parquet` - Cleaned data
- `data/processed/*_transformed.parquet` - Transformed data
- `data/processed/merged_dataset.parquet` - Merged dataset

### Final Outputs
- `outputs/datasets/final_dataset.csv` - Final dataset (CSV)
- `outputs/datasets/final_dataset.parquet` - Final dataset (Parquet)
- `outputs/datasets/{city}_data.parquet` - City-specific datasets

### Reports
- `outputs/reports/data_quality_report.md` - Quality report
- `outputs/reports/*.csv` - Statistics and missing data analysis
- `outputs/reports/*.png` - Visualizations
- `outputs/data_dictionary.md` - Variable documentation

---

## Troubleshooting

### Problem: Import errors
**Solution:** Make sure virtual environment is activated and dependencies installed:
```bash
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Problem: No data collected
**Solution:** 
- Check your date range in `.env`
- Verify network connection
- For air quality: use manual CSV download

### Problem: Memory issues
**Solution:**
- Process data in smaller date ranges
- Use Parquet format (more efficient than CSV)
- Process cities separately if needed

### Problem: API rate limiting
**Solution:**
- Scripts include rate limiting delays
- If you get 429 errors, increase delays in collector scripts

---

## Next Steps

1. **Collect Data:** Run `python scripts/main.py --collect`
2. **Inspect Raw Data:** Open CSV files in `data/raw/` to verify
3. **Add Air Quality Data:** Download from EEA and use helper script
4. **Run Full Pipeline:** `python scripts/main.py --all`
5. **Review Reports:** Check `outputs/reports/` for data quality
6. **Use Final Dataset:** Load `outputs/datasets/final_dataset.csv` for analysis

---

## Contact & Support

For questions or issues:
- Check `README.md` for general information
- Check `QUICKSTART.md` for quick start guide
- Review error messages - they often include helpful suggestions

---

## Key Points to Remember

1. ✅ **Weather data works automatically** (Meteostat)
2. ✅ **Traffic data works automatically** (synthetic)
3. ⚠️ **Air quality data requires manual CSV download** (EEA portal)
4. 📊 **All data saved in both CSV and Parquet** (CSV for inspection, Parquet for processing)
5. 🔄 **Pipeline continues even if one data source fails**
6. 📝 **Check reports in `outputs/reports/`** for data quality information

---

**Last Updated:** November 2024
**Project Status:** Functional - Weather and Traffic automated, Air Quality requires manual CSV download

