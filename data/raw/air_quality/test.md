# OpenAQ API v3 Setup Guide

## Overview
OpenAQ API v3 provides access to global air quality data. Version 1 and 2 were retired on January 31, 2025.

## Getting Started

### 1. Register for an API Key
- Visit: https://explore.openaq.org/register
- Create an account and get your API key

### 2. Configure API Key
Add your API key to your `.env` file:
```
OPENAQ_API_KEY=your_openaq_api_key_here
```

### 3. API Features
- Real-time and historical air quality data
- Global coverage (100+ countries)
- Pollutants: PM2.5, PM10, NO2, O3, CO, SO2, BC, and more
- Hourly, daily, and yearly averaged measurements
- Bounding box queries

### 4. Usage
The `air_quality_collector.py` script will automatically use your API key if configured.

### 5. Fallback Options
If API key is not available, you can:
- Use `download_from_csv()` method with manually downloaded EEA CSV files
- Download data from EEA portal: https://www.eea.europa.eu/data-and-maps/data/air-quality-database

## Documentation
- OpenAQ API v3 Docs: https://docs.openaq.org/
- API Reference: https://docs.openaq.org/reference/get_locations
