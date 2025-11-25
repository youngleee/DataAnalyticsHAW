# UBA (Umweltbundesamt) API Setup Guide

## Overview
The UBA (Umweltbundesamt) API is the official German government source for air quality data. It provides access to over 400 monitoring stations across Germany.

## Key Features
- **Official Source**: German government data
- **Free**: No API key required
- **Comprehensive**: Over 400 monitoring stations
- **Real-time & Historical**: Both current and historical data
- **Covers Major Cities**: Berlin, Munich, Hamburg, Cologne, Frankfurt, and more
- **Multiple Pollutants**: PM2.5, PM10, NO2, O3, CO, SO2

## API Information
- **Base URL**: `https://luftqualitaet.api.bund.dev`
- **Documentation**: https://luftqualitaet.api.bund.dev/
- **Main Portal**: https://luftdaten.umweltbundesamt.de/en
- **API Versions**: v2, v3, v4 available

## Usage
The `air_quality_collector.py` script automatically uses the UBA API. No configuration needed!

## Example Endpoint
```
https://luftqualitaet.api.bund.dev/api/air_data/v2/airquality/json?component=NO2&date_from=2023-01-01&date_to=2023-01-08
```

## Pollutants Supported
- NO2 (Nitrogen Dioxide)
- PM2.5 (Particulate Matter 2.5)
- PM10 (Particulate Matter 10)
- O3 (Ozone)
- CO (Carbon Monoxide)
- SO2 (Sulfur Dioxide)

## Fallback Options
If API access fails, you can:
- Use `download_from_csv()` method with manually downloaded CSV files
- Download data from UBA portal: https://luftdaten.umweltbundesamt.de/en
- Download from EEA portal: https://www.eea.europa.eu/data-and-maps/data/air-quality-database

## Documentation
- UBA API Docs: https://luftqualitaet.api.bund.dev/
- UBA Portal: https://luftdaten.umweltbundesamt.de/en
- API v3 Documentation: https://www.umweltbundesamt.de/daten/luft/luftdaten/doc
- API v4 Documentation: https://www.umweltbundesamt.de/daten/luft/luftdaten/doc-v4
