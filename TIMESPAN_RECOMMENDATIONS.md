# Recommended Timespans for Data Collection

## Current Status
- **Current data**: 8 days (2024-01-01 to 2024-01-08)
- **Cities**: 79 cities
- **Records**: ~600 weather/traffic, ~13,000 air quality (after 1 station per city)

---

## Recommended Timespans by Analysis Goal

### **Option 1: Minimum Viable (1-2 weeks)** ⚡ Quick & Simple
**Timespan:** 7-14 days

**Pros:**
- ✅ Quick to collect (~5-10 minutes)
- ✅ Good for initial exploration
- ✅ Sufficient for basic correlations
- ✅ Low API usage

**Cons:**
- ❌ Limited statistical power
- ❌ No seasonal variation
- ❌ May miss patterns

**Best for:**
- Testing the pipeline
- Initial data exploration
- Proof of concept
- Quick analysis

**Example:**
```env
START_DATE=2024-01-01
END_DATE=2024-01-14
```

---

### **Option 2: Recommended (1 month)** ⭐ **BEST BALANCE**
**Timespan:** 30 days (1 month)

**Pros:**
- ✅ Good statistical power (~2,400 records for 79 cities)
- ✅ Captures weekly patterns (weekdays vs weekends)
- ✅ Reasonable collection time (~15-20 minutes)
- ✅ Sufficient for correlation analysis
- ✅ Can detect patterns and trends

**Cons:**
- ❌ Still no seasonal variation
- ❌ Limited for time series analysis

**Best for:**
- **Most research projects** ⭐
- Correlation analysis
- Regression modeling
- City comparisons
- Statistical testing

**Example:**
```env
START_DATE=2024-01-01
END_DATE=2024-01-31
```

---

### **Option 3: Comprehensive (3 months)** 📊 **FOR SERIOUS ANALYSIS**
**Timespan:** 90 days (1 quarter)

**Pros:**
- ✅ Excellent statistical power (~7,200 records)
- ✅ Captures seasonal transition (winter → spring)
- ✅ Strong for time series analysis
- ✅ Can detect long-term patterns
- ✅ Better for machine learning models

**Cons:**
- ❌ Longer collection time (~30-45 minutes)
- ❌ Larger data files
- ❌ More processing time

**Best for:**
- Research papers
- Advanced modeling
- Time series forecasting
- Comprehensive analysis
- Publication-quality research

**Example:**
```env
START_DATE=2024-01-01
END_DATE=2024-03-31
```

---

### **Option 4: Full Year** 🌍 **MAXIMUM COVERAGE**
**Timespan:** 365 days (1 year)

**Pros:**
- ✅ Complete seasonal coverage (all 4 seasons)
- ✅ Maximum statistical power (~28,800 records)
- ✅ Can analyze seasonal patterns
- ✅ Best for long-term trends
- ✅ Publication-quality data

**Cons:**
- ❌ Very long collection time (1-2 hours)
- ❌ Very large data files
- ❌ May hit API rate limits
- ❌ Long processing time

**Best for:**
- Doctoral research
- Long-term studies
- Seasonal analysis
- Climate impact studies
- Comprehensive publications

**Example:**
```env
START_DATE=2024-01-01
END_DATE=2024-12-31
```

---

## Statistical Considerations

### Minimum Sample Size for Analysis:

| Analysis Type | Minimum Days | Minimum Records (79 cities) |
|---------------|-------------|----------------------------|
| Basic correlation | 7 days | ~553 |
| Regression analysis | 14 days | ~1,106 |
| Statistical testing | 30 days | ~2,370 |
| Time series | 60 days | ~4,740 |
| Seasonal analysis | 90+ days | ~7,110 |

### Data Points Needed:
- **Correlation analysis**: ~500-1,000 data points minimum
- **Regression models**: ~1,000-2,000 data points recommended
- **Machine learning**: ~2,000+ data points for good performance
- **Time series**: ~60+ days for meaningful patterns

---

## Practical Recommendations

### **For Your Current Project (79 cities):**

**🎯 RECOMMENDED: 1 Month (30 days)**
- **Why:** Best balance of data quality, collection time, and analysis power
- **Records:** ~2,370 (79 cities × 30 days)
- **Collection time:** ~15-20 minutes
- **Analysis:** Sufficient for correlations, regressions, and city comparisons

**Quick Start Option: 2 Weeks (14 days)**
- If you want to test quickly first
- Then expand to 1 month if needed

**Comprehensive Option: 3 Months (90 days)**
- If you need seasonal analysis
- For more robust statistical models

---

## How to Change Timespan

Edit your `.env` file:

```env
# For 1 month (recommended)
START_DATE=2024-01-01
END_DATE=2024-01-31

# For 3 months
START_DATE=2024-01-01
END_DATE=2024-03-31

# For full year
START_DATE=2024-01-01
END_DATE=2024-12-31
```

Then re-run collection:
```bash
python scripts/main.py --collect
```

---

## Collection Time Estimates

| Timespan | Cities | Estimated Time |
|----------|--------|----------------|
| 1 week | 79 | ~5-10 minutes |
| 1 month | 79 | ~15-20 minutes |
| 3 months | 79 | ~30-45 minutes |
| 1 year | 79 | ~1-2 hours |

*Note: Times include rate limiting delays*

---

## My Recommendation for You

**Start with 1 month (30 days)** - This gives you:
- ✅ Strong statistical power
- ✅ Reasonable collection time
- ✅ Good for most analyses
- ✅ Can always expand later if needed

**If time is limited:** 2 weeks (14 days) is acceptable for initial analysis.

**If you need seasonal patterns:** Go with 3 months (90 days).

---

## Summary Table

| Timespan | Days | Records* | Collection Time | Best For |
|----------|------|----------|-----------------|----------|
| **Minimum** | 7-14 | ~550-1,100 | 5-10 min | Quick tests |
| **⭐ Recommended** | **30** | **~2,370** | **15-20 min** | **Most projects** |
| **Comprehensive** | 90 | ~7,110 | 30-45 min | Advanced analysis |
| **Full Year** | 365 | ~28,800 | 1-2 hours | Long-term studies |

*Records = 79 cities × days

