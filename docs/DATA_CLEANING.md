# Data Cleaning Documentation (Bronze → Silver)

This document describes the data cleaning process for transforming raw (Bronze) data into cleaned (Silver) data.

## Overview

| Layer | Purpose | Location |
|-------|---------|----------|
| **Bronze** | Raw data as collected | `data/raw/` |
| **Silver** | Cleaned, validated, standardized | `data/silver/` |
| **Gold** | Unified, analysis-ready | `data/gold/` |

---

## Cleaning Steps

### 1. Handle Missing Values

| Dataset | Column | Strategy | Reason |
|---------|--------|----------|--------|
| Weather | `snow` | Fill with 0 | No snow = 0mm |
| Weather | `wpgt` (wind gust) | Drop column | >50% missing, not critical |
| Weather | `tsun` (sunshine) | Drop column | Sparse, not needed |
| Air Quality | `no2`, `pm10`, `o3` | Forward-fill | Pollutants change gradually |
| Traffic | All | Verify complete | Synthetic data should be complete |

### 2. Standardize Data Types

| Column | From | To | Purpose |
|--------|------|-----|---------|
| `datetime` | string | `datetime64[ns]` | Time-series operations |
| `date` | string | `date` | Date grouping |
| `hour` | float | `int8` | Memory efficiency |
| Numeric columns | `float64` | `float32` | Memory efficiency |

### 3. Remove Duplicates

- **Key**: `(city_key, datetime)`
- **Action**: Keep first occurrence
- **Reason**: Same location + time should not appear twice

### 4. Validate Ranges

| Column | Valid Range | Action |
|--------|-------------|--------|
| `temperature` | -40°C to 50°C | Flag outliers |
| `humidity` | 0% to 100% | Clip to bounds |
| `no2`, `pm10`, `o3` | 0 to 500 µg/m³ | Clip negatives to 0 |
| `traffic_index` | 0 to 100 | Clip to bounds |
| `wind_speed` | 0 to 50 m/s | Clip negatives to 0 |

### 5. Drop Unnecessary Columns

| Dataset | Columns Dropped | Reason |
|---------|-----------------|--------|
| Weather | `wpgt`, `tsun`, `dwpt` | Sparse or redundant |
| Traffic | `data_source`, `confidence` | Metadata only |
| Air Quality | `station_name`, `station_id` | City-level is sufficient |

### 6. Standardize Column Names

All columns use:
- Lowercase
- Underscores for spaces
- Consistent naming across datasets

### 7. Align Cities

Only keep cities that exist in **all three datasets**:
```
final_cities = weather_cities ∩ traffic_cities ∩ air_quality_cities
```

### 8. Derived Features

New columns calculated from existing data:

| Feature | Formula | Purpose |
|---------|---------|---------|
| `month` | Extract from datetime | Seasonal analysis |
| `is_night` | hour < 6 or hour >= 22 | Day/night patterns |
| `is_weekday` | day_of_week < 5 | Weekday vs weekend |

---

## Output Files

```
data/silver/
├── weather_cleaned.csv
├── weather_cleaned.parquet
├── air_quality_cleaned.csv
├── air_quality_cleaned.parquet
├── traffic_cleaned.csv
└── traffic_cleaned.parquet
```

---

## Quality Metrics

After cleaning, we track:

| Metric | Description |
|--------|-------------|
| `rows_before` | Original row count |
| `rows_after` | Row count after cleaning |
| `duplicates_removed` | Number of duplicate rows removed |
| `nulls_filled` | Number of null values filled |
| `outliers_clipped` | Number of values clipped to valid range |

---

## Running the Cleaner

```bash
# Activate virtual environment
.\\venv\\Scripts\\activate

# Run cleaning script
python scripts/clean/data_cleaner.py
```

---

## Data Quality Checks

The cleaner validates:

1. ✅ No null values in key columns (`city_key`, `datetime`)
2. ✅ No duplicate rows
3. ✅ All numeric values within valid ranges
4. ✅ Consistent datetime format
5. ✅ All cities present across datasets

---

## Cleaning Results (Latest Run: 2026-01-12)

### Summary Statistics

| Dataset | Rows Before | Rows After | Nulls Filled | Duplicates Removed | Outliers Clipped |
|---------|-------------|------------|--------------|-------------------|------------------|
| **Weather** | 164,259 | 142,649 | 83,808 | 0 | 0 |
| **Air Quality** | 150,484 | 143,932 | 51,552 | 0 | 0 |
| **Traffic** | 170,719 | 142,626 | 161,160 | 0 | 0 |

### City Alignment Results

| Metric | Count |
|--------|-------|
| Weather cities (before) | 76 |
| Air quality cities (before) | 69 |
| Traffic cities (before) | 79 |
| **Common cities (after)** | **66** |
| Dropped from weather | 10 |
| Dropped from air quality | 3 |
| Dropped from traffic | 13 |

### Columns After Cleaning

**Weather (22 columns):**
```
datetime, temperature, dwpt, humidity, precipitation, snow, wind_direction, 
wind_speed, wpgt, pressure, tsun, weather_code, city, city_key, lat, lon, 
date, hour, month, is_night, day_of_week, is_weekday
```

**Air Quality (13 columns):**
```
city, city_key, datetime, date, hour, no2, pm10, o3, month, is_night, 
day_of_week, is_weekday, aqi_avg
```

**Traffic (19 columns):**
```
city, city_key, datetime, date, hour, day_of_week, lat, lon, current_speed, 
free_flow_speed, congestion_level, traffic_index, is_rush_hour, is_weekend, 
is_holiday, holiday_name, month, is_night, is_weekday
```

### Derived Features Added

| Feature | Type | Description | Added To |
|---------|------|-------------|----------|
| `month` | int | Month number (1-3) | All datasets |
| `is_night` | bool | True if hour < 6 or hour >= 22 | All datasets |
| `day_of_week` | int | 0=Monday, 6=Sunday | Weather, Air Quality |
| `is_weekday` | bool | True if Monday-Friday | All datasets |
| `aqi_avg` | float | Average of NO2, PM10, O3 | Air Quality only |

### Columns Dropped

| Dataset | Columns Dropped | Reason |
|---------|-----------------|--------|
| Air Quality | `station_name`, `station_id` | City-level aggregation is sufficient |
| Traffic | `data_source`, `confidence` | Metadata not needed for analysis |

### Data Type Optimizations

| Change | Memory Impact |
|--------|---------------|
| `float64` → `float32` | ~50% reduction |
| `hour` → `int8` | ~87% reduction |
| `day_of_week` → `int8` | ~87% reduction |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-01-12 | Initial cleaning pipeline created |
| 2026-01-12 | First cleaning run completed - 66 common cities identified |

