# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation

1. **Clone or navigate to the project directory**

2. **Create and activate virtual environment:**

   **Windows:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
   
   Or run the setup script:
   ```bash
   setup_venv.bat
   venv\Scripts\activate
   ```

   **Linux/Mac:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   Or run the setup script:
   ```bash
   chmod +x setup_venv.sh
   ./setup_venv.sh
   source venv/bin/activate
   ```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up configuration:**

   **Windows:**
   ```bash
   copy config.example.env .env
   ```
   
   **Linux/Mac:**
   ```bash
   cp config.example.env .env
   ```

5. **Edit `.env` file and add your API keys:**
```env
OPENWEATHERMAP_API_KEY=your_key_here
```

**Note:** Make sure your virtual environment is activated (you should see `(venv)` in your terminal prompt) before running any commands.

## Running the Pipeline

### Option 1: Run Everything at Once
```bash
python scripts/main.py --all
```

This will:
1. Collect data from all sources
2. Clean the data
3. Transform and standardize
4. Integrate datasets
5. Engineer features
6. Generate reports

### Option 2: Run Step by Step

1. **Collect data:**
```bash
python scripts/main.py --collect
```

2. **Clean data:**
```bash
python scripts/main.py --clean
```

3. **Transform data:**
```bash
python scripts/main.py --transform
```

4. **Integrate datasets:**
```bash
python scripts/main.py --integrate
```

5. **Engineer features:**
```bash
python scripts/main.py --features
```

6. **Generate reports:**
```bash
python scripts/main.py --report
```

## Expected Output

After running the pipeline, you should have:

- **Final Dataset**: `outputs/datasets/final_dataset.parquet`
- **City-specific datasets**: `outputs/datasets/{city}_data.parquet`
- **Data Quality Report**: `outputs/reports/data_quality_report.md`
- **Data Dictionary**: `outputs/data_dictionary.md`
- **Visualizations**: PNG files in `outputs/reports/`

## Common Issues

### Issue: "API key not found"
**Solution**: Make sure you've created `.env` file and added your API key.

### Issue: "No air quality data collected"
**Solution**: EEA data may require manual download. See README.md for instructions.

### Issue: "No traffic data collected"
**Solution**: The script will automatically use synthetic traffic data if TomTom API is unavailable.

### Issue: Import errors
**Solution**: Make sure:
1. Virtual environment is activated (you should see `(venv)` in terminal)
2. All dependencies are installed:
```bash
pip install -r requirements.txt
```

### Issue: "python: command not found" (Linux/Mac)
**Solution**: Use `python3` instead of `python`:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Next Steps

1. Review the data quality report: `outputs/reports/data_quality_report.md`
2. Check the data dictionary: `outputs/data_dictionary.md`
3. Load the final dataset for analysis:
```python
import pandas as pd
df = pd.read_parquet('outputs/datasets/final_dataset.parquet')
```

## Getting API Keys

### OpenWeatherMap
1. Visit: https://openweathermap.org/api
2. Sign up for a free account
3. Get your API key from the dashboard

### TomTom (Optional)
1. Visit: https://developer.tomtom.com/
2. Sign up for a free account
3. Create an app and get your API key

Note: TomTom API is optional - the script can generate synthetic traffic data if unavailable.

## Data Collection Notes

- **Weather Data**: OpenWeatherMap free tier has limited historical data. For true historical data, consider Meteostat API (free) or OpenWeatherMap paid tier.
- **Air Quality Data**: May require manual CSV download from EEA portal. The script includes methods to load manually downloaded files.
- **Traffic Data**: If TomTom API is unavailable, synthetic data will be generated based on realistic patterns (rush hours, weekends, etc.).

## Support

For detailed documentation, see `README.md`.

