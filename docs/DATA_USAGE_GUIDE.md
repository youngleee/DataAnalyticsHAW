# Data Usage Guide - How Your Collected Data is Used

## Overview

Once you collect data for all 79 cities, here's how it flows through the pipeline to generate insights:

```
RAW DATA → CLEAN → TRANSFORM → INTEGRATE → FEATURES → ANALYZE → INSIGHTS
```

---

## Step-by-Step Data Pipeline

### **Step 1: Raw Data Collection** ✅ (You're here)

**What you have:**
- Weather data: 79 cities × 8 days = ~632 records
- Air quality data: 79 cities × multiple stations × hourly = ~thousands of records
- Traffic data: 79 cities × 8 days = ~632 records

**Files:**
- `data/raw/weather/weather_data_TIMESTAMP.csv`
- `data/raw/air_quality/air_quality_data_TIMESTAMP.csv`
- `data/raw/traffic/traffic_data_TIMESTAMP.csv`

**What's in the data:**
- **Weather**: Temperature, humidity, wind speed, precipitation, pressure
- **Air Quality**: NO2, PM10, O3 measurements from monitoring stations
- **Traffic**: Traffic index, congestion levels

---

### **Step 2: Data Cleaning** 🧹

**Command:** `python scripts/main.py --clean`

**What happens:**
- Removes duplicates
- Handles missing values
- Removes outliers (using IQR method)
- Validates data ranges (e.g., temperature -50 to 50°C)
- Standardizes column names

**Output:**
- `data/processed/weather_cleaned.parquet`
- `data/processed/air_quality_cleaned.parquet`
- `data/processed/traffic_cleaned.parquet`

**Why:** Clean data ensures accurate analysis

---

### **Step 3: Data Transformation** 🔄

**Command:** `python scripts/main.py --transform`

**What happens:**
- **Unit standardization**: All temperatures to °C, all pollution to μg/m³
- **Time alignment**: Converts all data to hourly resolution
- **Timezone conversion**: All timestamps to CET/CEST
- **Category creation**: 
  - Season (winter, spring, summer, fall)
  - Day type (weekday, weekend)
  - Rush hour (yes/no)
  - Time of day (morning, afternoon, evening, night)

**Output:**
- `data/processed/weather_transformed.parquet`
- `data/processed/air_quality_transformed.parquet`
- `data/processed/traffic_transformed.parquet`

**Why:** Consistent format enables merging and comparison

---

### **Step 4: Data Integration** 🔗

**Command:** `python scripts/main.py --integrate`

**What happens:**
- **Merges all three datasets** by city and timestamp
- **Geographic matching**: Links weather stations, air quality stations, and traffic points by city
- **Creates unified dataset**: One row per city per hour/day with all variables
- **City-specific datasets**: Separate files for each city

**Output:**
- `data/processed/merged_dataset.parquet` (all cities combined)
- `outputs/datasets/berlin_data.parquet` (Berlin only)
- `outputs/datasets/munich_data.parquet` (Munich only)
- ... (one file per city)

**Why:** Single dataset enables cross-variable analysis

**Example merged row:**
```
city: Berlin
date: 2024-01-01
temperature: 6.9°C
humidity: 75%
wind_speed: 3.2 m/s
no2: 27.0 μg/m³
pm10: 20.0 μg/m³
o3: 21.0 μg/m³
traffic_index: 45
season: winter
day_type: weekday
```

---

### **Step 5: Feature Engineering** 🛠️

**Command:** `python scripts/main.py --features`

**What happens:**
- **Time features**: Hour, day of week, month, season (cyclical encoding)
- **Rolling averages**: 7-day and 30-day moving averages for pollutants
- **Lag features**: Previous day's traffic → today's pollution
- **Interaction terms**: temperature × traffic, wind_speed × traffic
- **Derived features**: 
  - Heat index (temperature + humidity)
  - Pollution ratios (NO2/O3)
  - Exceedance indicators (above thresholds)

**Output:**
- `outputs/datasets/final_dataset.parquet` (ready for analysis)
- `outputs/datasets/final_dataset.csv` (for easy viewing)

**Why:** Rich features improve model performance and reveal patterns

---

### **Step 6: Analysis & Insights** 📊

#### **6.1 Correlation Analysis** (Already Available!)

**Command:** `python scripts/analyze/correlation_analysis.py`

**What it does:**
- Calculates correlation matrices between all variables
- Generates heatmaps showing relationships
- Creates scatter plots for key relationships
- Performs statistical tests (Pearson correlation)
- Runs regression analysis

**Output:**
- `outputs/reports/correlation_heatmap_TIMESTAMP.png`
- `outputs/reports/scatter_plots_TIMESTAMP.png`
- `outputs/reports/correlation_report_TIMESTAMP.txt`

**Insights you get:**
- Which weather factors most affect pollution?
- Does traffic correlate with air quality?
- How do pollutants relate to each other?
- Which cities have different patterns?

**Example findings:**
```
NO2 vs Traffic Index: r = 0.65 (strong positive correlation)
PM10 vs Wind Speed: r = -0.45 (moderate negative - wind disperses particles)
O3 vs Temperature: r = 0.72 (strong positive - higher temp = more O3)
```

---

#### **6.2 Advanced Analysis** (Next Steps - See PROJECT_ROADMAP.md)

**A. Statistical Modeling**
- **Multiple Regression**: Predict pollution from weather + traffic
- **Time Series**: Forecast future pollution levels
- **Machine Learning**: Random Forest, XGBoost for prediction

**B. Comparative Analysis**
- **City comparisons**: Which cities have worst air quality?
- **Seasonal patterns**: How does pollution change by season?
- **Urban vs. suburban**: Compare different station types

**C. Policy Insights**
- **Traffic impact**: Quantify how traffic affects pollution
- **Weather influence**: How much does weather explain pollution?
- **Intervention scenarios**: What if traffic reduced by 20%?

---

## Real-World Use Cases

### **1. Research Question: "How does traffic affect air pollution?"**

**Analysis:**
1. Load final dataset
2. Calculate correlation: traffic_index vs NO2, PM10
3. Build regression model: `pollution = f(traffic, weather)`
4. Visualize relationship with scatter plots
5. Test statistical significance

**Result:** 
- "Traffic explains 42% of NO2 variation in Berlin"
- "Each 10-point increase in traffic index = +3.2 μg/m³ NO2"

---

### **2. Research Question: "Which cities have the worst air quality?"**

**Analysis:**
1. Load merged dataset
2. Group by city
3. Calculate average pollution levels
4. Rank cities
5. Visualize with bar charts

**Result:**
- Ranking of cities by pollution levels
- Identification of problem areas

---

### **3. Research Question: "How does weather affect pollution?"**

**Analysis:**
1. Calculate correlations: temperature, wind, humidity vs pollutants
2. Seasonal analysis: compare winter vs summer
3. Weather-pollution interaction plots
4. Regression with weather variables

**Result:**
- "Wind speed explains 35% of PM10 variation"
- "Temperature strongly correlates with O3 (r=0.72)"

---

### **4. Research Question: "Can we predict pollution from weather and traffic?"**

**Analysis:**
1. Split data: training (80%) / testing (20%)
2. Train machine learning model (Random Forest)
3. Evaluate: R², RMSE, MAE
4. Feature importance analysis
5. Make predictions

**Result:**
- Model accuracy: R² = 0.78
- Most important features: traffic_index, temperature, wind_speed
- Predictions for future dates

---

## Quick Start: Run Full Pipeline

```bash
# Step 1: Collect data (already done or in progress)
python scripts/main.py --collect

# Step 2-6: Process and analyze
python scripts/main.py --all

# Or run step by step:
python scripts/main.py --clean      # Clean data
python scripts/main.py --transform  # Transform data
python scripts/main.py --integrate  # Merge datasets
python scripts/main.py --features   # Engineer features
python scripts/main.py --report     # Generate reports

# Step 7: Correlation analysis
python scripts/analyze/correlation_analysis.py
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW DATA COLLECTION                       │
│  Weather (79 cities) │ Air Quality (79 cities) │ Traffic   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      DATA CLEANING                           │
│  Remove duplicates │ Handle missing │ Remove outliers       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA TRANSFORMATION                       │
│  Standardize units │ Align time │ Create categories          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     DATA INTEGRATION                         │
│  Merge by city & time │ Create unified dataset              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   FEATURE ENGINEERING                        │
│  Time features │ Rolling averages │ Lag features            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      ANALYSIS                                │
│  Correlation │ Regression │ ML Models │ Visualizations      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      INSIGHTS                                │
│  Reports │ Charts │ Predictions │ Recommendations           │
└─────────────────────────────────────────────────────────────┘
```

---

## What You Can Answer with This Data

### **Descriptive Questions:**
- What are the average pollution levels in each city?
- How does pollution vary by season?
- Which cities have the worst air quality?
- What are typical weather patterns?

### **Analytical Questions:**
- Does traffic significantly affect air pollution?
- How much does weather explain pollution variation?
- Are there differences between cities?
- What are the key drivers of pollution?

### **Predictive Questions:**
- Can we predict tomorrow's pollution from today's weather and traffic?
- What would pollution be if traffic reduced by 20%?
- How will pollution change with climate change?

### **Prescriptive Questions:**
- What policies would most reduce pollution?
- Should traffic restrictions be implemented?
- Which cities need most intervention?

---

## Output Files Summary

### **Processed Data:**
- `data/processed/merged_dataset.parquet` - All cities, all variables
- `outputs/datasets/final_dataset.parquet` - With engineered features
- `outputs/datasets/{city}_data.parquet` - City-specific datasets

### **Analysis Results:**
- `outputs/reports/correlation_heatmap.png` - Correlation visualization
- `outputs/reports/scatter_plots.png` - Relationship plots
- `outputs/reports/correlation_report.txt` - Statistical results
- `outputs/reports/data_quality_report.md` - Data quality assessment

### **Visualizations:**
- Heatmaps showing correlations
- Scatter plots for relationships
- Time series plots
- City comparison charts
- Seasonal analysis plots

---

## Next Steps After Data Collection

1. **Run the full pipeline** to process your data
2. **Run correlation analysis** to see initial relationships
3. **Explore the data** using the final dataset
4. **Build models** for prediction (see PROJECT_ROADMAP.md)
5. **Generate insights** and write your research report

---

## Tips for Effective Analysis

1. **Start with correlation analysis** - Quick overview of relationships
2. **Visualize first** - Charts reveal patterns better than numbers
3. **Compare cities** - Look for differences and similarities
4. **Consider seasonality** - Weather and pollution vary by season
5. **Test hypotheses** - Don't just describe, test relationships
6. **Document findings** - Keep notes on what you discover

---

**Remember:** The data is just the beginning. The real value comes from the analysis and insights you extract!

