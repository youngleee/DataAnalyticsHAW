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

## Changelog

| Date | Change |
|------|--------|
| 2026-01-12 | Initial cleaning pipeline created |

