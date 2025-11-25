"""
Comprehensive Correlation Analysis Script

Analyzes correlations between air quality, weather, and traffic data.
Generates visualizations, statistical tests, and summary reports.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class CorrelationAnalyzer:
    """Perform comprehensive correlation analysis on air quality, weather, and traffic data."""
    
    def __init__(self, data_dir='data/raw'):
        """Initialize analyzer with data directory."""
        self.data_dir = Path(data_dir)
        self.output_dir = Path('outputs/reports')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for output files
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.merged_data = None
        self.correlation_matrix = None
        
    def load_data(self):
        """Load and merge all datasets."""
        print("=" * 70)
        print("STEP 1: LOADING DATA")
        print("=" * 70)
        
        # Find latest files
        aq_dir = self.data_dir / 'air_quality'
        weather_dir = self.data_dir / 'weather'
        traffic_dir = self.data_dir / 'traffic'
        
        aq_files = list(aq_dir.glob('air_quality_data_*.csv'))
        weather_files = list(weather_dir.glob('weather_data_*.csv'))
        traffic_files = list(traffic_dir.glob('traffic_data_*.csv'))
        
        if not aq_files or not weather_files or not traffic_files:
            raise FileNotFoundError("Required data files not found. Please run data collection first.")
        
        # Get most recent files
        aq_file = max(aq_files, key=lambda p: p.stat().st_mtime)
        weather_file = max(weather_files, key=lambda p: p.stat().st_mtime)
        traffic_file = max(traffic_files, key=lambda p: p.stat().st_mtime)
        
        print(f"\nLoading files:")
        print(f"  Air Quality: {aq_file.name}")
        print(f"  Weather: {weather_file.name}")
        print(f"  Traffic: {traffic_file.name}")
        
        # Load datasets
        air_quality = pd.read_csv(aq_file)
        weather = pd.read_csv(weather_file)
        traffic = pd.read_csv(traffic_file)
        
        print(f"\nLoaded data:")
        print(f"  Air Quality: {len(air_quality):,} records")
        print(f"  Weather: {len(weather):,} records")
        print(f"  Traffic: {len(traffic):,} records")
        
        # Parse dates
        air_quality['date'] = pd.to_datetime(air_quality['date'])
        weather['date'] = pd.to_datetime(weather['date'])
        traffic['date'] = pd.to_datetime(traffic['date'])
        
        # Aggregate air quality to daily averages (since weather/traffic are daily)
        print("\nAggregating air quality data to daily averages...")
        aq_daily = air_quality.groupby(['city', 'date']).agg({
            'no2': 'mean',
            'pm10': 'mean',
            'o3': 'mean'
        }).reset_index()
        
        print(f"  Daily air quality records: {len(aq_daily):,}")
        
        # Store date ranges for error reporting
        aq_date_min = aq_daily['date'].min()
        aq_date_max = aq_daily['date'].max()
        weather_date_min = weather['date'].min()
        weather_date_max = weather['date'].max()
        traffic_date_min = traffic['date'].min()
        traffic_date_max = traffic['date'].max()
        
        # Merge all datasets
        print("\nMerging datasets...")
        print(f"  Air quality date range: {aq_date_min} to {aq_date_max}")
        print(f"  Weather date range: {weather_date_min} to {weather_date_max}")
        print(f"  Traffic date range: {traffic_date_min} to {traffic_date_max}")
        
        # Check for overlapping dates
        aq_dates = set(aq_daily['date'].dt.date)
        weather_dates = set(weather['date'].dt.date)
        traffic_dates = set(traffic['date'].dt.date)
        
        common_dates = aq_dates & weather_dates & traffic_dates
        print(f"  Common dates across all datasets: {len(common_dates)}")
        
        if len(common_dates) == 0:
            print("\n⚠ WARNING: No overlapping dates found between datasets!")
            print("  This may be due to different date ranges in the data files.")
            print("  The analysis will continue but may have limited results.")
        
        # Get available columns from traffic data
        traffic_cols = ['city', 'date', 'traffic_index', 'congestion_level']
        available_traffic_cols = [col for col in traffic_cols if col in traffic.columns]
        # Add optional columns if they exist
        for col in ['current_speed', 'free_flow_speed']:
            if col in traffic.columns:
                available_traffic_cols.append(col)
        
        merged = aq_daily.merge(
            weather[['city', 'date', 'temperature', 'temp_min', 'temp_max', 
                    'wind_speed', 'precipitation', 'pressure', 'wpgt']],
            on=['city', 'date'],
            how='inner'
        ).merge(
            traffic[available_traffic_cols],
            on=['city', 'date'],
            how='inner'
        )
        
        # Add derived features
        if 'temp_max' in merged.columns and 'temp_min' in merged.columns:
            merged['temp_range'] = merged['temp_max'] - merged['temp_min']
        merged['month'] = merged['date'].dt.month
        merged['day_of_week'] = merged['date'].dt.dayofweek
        merged['is_weekend'] = merged['day_of_week'].isin([5, 6]).astype(int)
        merged['season'] = merged['month'].apply(self._get_season)
        
        print(f"  Merged records: {len(merged):,}")
        print(f"  Cities: {', '.join(merged['city'].unique())}")
        print(f"  Date range: {merged['date'].min().date()} to {merged['date'].max().date()}")
        
        self.merged_data = merged
        return merged
    
    def _get_season(self, month):
        """Convert month to season."""
        if month in [12, 1, 2]:
            return 'Winter'
        elif month in [3, 4, 5]:
            return 'Spring'
        elif month in [6, 7, 8]:
            return 'Summer'
        else:
            return 'Fall'
    
    def calculate_correlations(self):
        """Calculate correlation matrices."""
        print("\n" + "=" * 70)
        print("STEP 2: CALCULATING CORRELATIONS")
        print("=" * 70)
        
        # Select numeric columns for correlation
        numeric_cols = [
            'no2', 'pm10', 'o3',  # Pollutants
            'temperature', 'wind_speed', 'precipitation', 'pressure',  # Weather
            'traffic_index', 'congestion_level'  # Traffic
        ]
        
        # Filter to available columns
        available_cols = [col for col in numeric_cols if col in self.merged_data.columns]
        
        # Calculate correlation matrix
        self.correlation_matrix = self.merged_data[available_cols].corr()
        
        print("\nCorrelation matrix calculated.")
        print(f"Variables analyzed: {len(available_cols)}")
        
        return self.correlation_matrix
    
    def visualize_correlations(self):
        """Create correlation visualizations."""
        print("\n" + "=" * 70)
        print("STEP 3: CREATING VISUALIZATIONS")
        print("=" * 70)
        
        # 1. Full correlation heatmap
        print("\n1. Creating full correlation heatmap...")
        plt.figure(figsize=(14, 10))
        mask = np.triu(np.ones_like(self.correlation_matrix, dtype=bool))
        sns.heatmap(self.correlation_matrix, annot=True, cmap='RdBu_r', center=0,
                   fmt='.2f', square=True, mask=mask, cbar_kws={'label': 'Correlation'})
        plt.title('Correlation Matrix: Air Quality vs Weather & Traffic Factors', 
                 fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / f'correlation_heatmap_{self.timestamp}.png', dpi=300)
        print(f"   Saved: correlation_heatmap_{self.timestamp}.png")
        plt.close()
        
        # 2. Focused heatmap: pollutants vs predictors
        print("2. Creating pollutant-focused heatmap...")
        pollutant_cols = ['no2', 'pm10', 'o3']
        predictor_cols = [col for col in self.correlation_matrix.columns 
                         if col not in pollutant_cols]
        
        if all(col in self.correlation_matrix.index for col in pollutant_cols):
            focused_corr = self.correlation_matrix.loc[pollutant_cols, predictor_cols]
            
            plt.figure(figsize=(12, 4))
            sns.heatmap(focused_corr, annot=True, cmap='RdYlBu_r', center=0,
                       fmt='.2f', cbar_kws={'label': 'Correlation'})
            plt.title('Air Pollutants vs Weather & Traffic Factors', 
                     fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(self.output_dir / f'pollutant_correlations_{self.timestamp}.png', dpi=300)
            print(f"   Saved: pollutant_correlations_{self.timestamp}.png")
            plt.close()
        
        # 3. Scatter plots for key relationships
        print("3. Creating scatter plots...")
        self._create_scatter_plots()
        
        # 4. City-specific correlations
        print("4. Creating city-specific analysis...")
        self._create_city_analysis()
        
        # 5. Time-based analysis
        print("5. Creating time-based analysis...")
        self._create_time_analysis()
    
    def _create_scatter_plots(self):
        """Create scatter plots for key relationships."""
        fig, axes = plt.subplots(3, 3, figsize=(18, 15))
        fig.suptitle('Key Relationships: Air Pollutants vs Weather & Traffic', 
                     fontsize=16, fontweight='bold')
        
        relationships = [
            # Row 1: NO2
            ('traffic_index', 'no2', 'NO2 vs Traffic Index', axes[0, 0]),
            ('temperature', 'no2', 'NO2 vs Temperature', axes[0, 1]),
            ('wind_speed', 'no2', 'NO2 vs Wind Speed', axes[0, 2]),
            # Row 2: PM10
            ('traffic_index', 'pm10', 'PM10 vs Traffic Index', axes[1, 0]),
            ('wind_speed', 'pm10', 'PM10 vs Wind Speed', axes[1, 1]),
            ('precipitation', 'pm10', 'PM10 vs Precipitation', axes[1, 2]),
            # Row 3: O3
            ('temperature', 'o3', 'O3 vs Temperature', axes[2, 0]),
            ('wind_speed', 'o3', 'O3 vs Wind Speed', axes[2, 1]),
            ('traffic_index', 'o3', 'O3 vs Traffic Index', axes[2, 2]),
        ]
        
        for x_col, y_col, title, ax in relationships:
            if x_col in self.merged_data.columns and y_col in self.merged_data.columns:
                data = self.merged_data[[x_col, y_col]].dropna()
                if len(data) > 0:
                    ax.scatter(data[x_col], data[y_col], alpha=0.6, s=50)
                    ax.set_xlabel(x_col.replace('_', ' ').title())
                    ax.set_ylabel(f'{y_col.upper()} (µg/m³)')
                    ax.set_title(title)
                    
                    # Add correlation coefficient
                    if len(data) > 1:
                        corr, p_val = pearsonr(data[x_col], data[y_col])
                        ax.text(0.05, 0.95, f'r = {corr:.3f}\np = {p_val:.3f}',
                               transform=ax.transAxes, verticalalignment='top',
                               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            else:
                ax.text(0.5, 0.5, 'Data not available', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f'scatter_plots_{self.timestamp}.png', dpi=300)
        print(f"   Saved: scatter_plots_{self.timestamp}.png")
        plt.close()
    
    def _create_city_analysis(self):
        """Create city-specific correlation analysis."""
        cities = self.merged_data['city'].unique()
        
        # Calculate correlations by city
        city_correlations = {}
        for city in cities:
            city_data = self.merged_data[self.merged_data['city'] == city]
            numeric_cols = ['no2', 'pm10', 'o3', 'traffic_index', 
                           'temperature', 'wind_speed']
            available_cols = [col for col in numeric_cols 
                            if col in city_data.columns]
            if len(available_cols) > 1:
                city_corr = city_data[available_cols].corr()
                city_correlations[city] = city_corr
        
        # Create heatmap for each city
        n_cities = len(city_correlations)
        if n_cities > 0:
            fig, axes = plt.subplots(1, n_cities, figsize=(6*n_cities, 5))
            if n_cities == 1:
                axes = [axes]
            
            for idx, (city, corr_matrix) in enumerate(city_correlations.items()):
                pollutant_cols = [col for col in ['no2', 'pm10', 'o3'] 
                                if col in corr_matrix.index]
                predictor_cols = [col for col in corr_matrix.columns 
                                 if col not in pollutant_cols]
                
                if pollutant_cols and predictor_cols:
                    focused = corr_matrix.loc[pollutant_cols, predictor_cols]
                    sns.heatmap(focused, annot=True, cmap='RdYlBu_r', center=0,
                               fmt='.2f', ax=axes[idx], cbar_kws={'label': 'Correlation'})
                    axes[idx].set_title(f'{city}', fontweight='bold')
            
            plt.suptitle('City-Specific Correlations: Pollutants vs Predictors', 
                        fontsize=14, fontweight='bold')
            plt.tight_layout()
            plt.savefig(self.output_dir / f'city_correlations_{self.timestamp}.png', dpi=300)
            print(f"   Saved: city_correlations_{self.timestamp}.png")
            plt.close()
    
    def _create_time_analysis(self):
        """Create time-based analysis visualizations."""
        # Monthly averages
        monthly_avg = self.merged_data.groupby('month').agg({
            'no2': 'mean',
            'pm10': 'mean',
            'o3': 'mean',
            'temperature': 'mean',
            'traffic_index': 'mean'
        })
        
        # Plot monthly trends
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        # Monthly pollutants
        monthly_avg[['no2', 'pm10', 'o3']].plot(ax=axes[0, 0], marker='o')
        axes[0, 0].set_title('Monthly Average Pollutant Levels', fontweight='bold')
        axes[0, 0].set_xlabel('Month')
        axes[0, 0].set_ylabel('Concentration (µg/m³)')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Monthly temperature and traffic
        ax2 = axes[0, 1]
        ax2_twin = ax2.twinx()
        monthly_avg['temperature'].plot(ax=ax2, color='red', marker='o', label='Temperature')
        monthly_avg['traffic_index'].plot(ax=ax2_twin, color='blue', marker='s', label='Traffic Index')
        ax2.set_title('Monthly Temperature and Traffic', fontweight='bold')
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Temperature (°C)', color='red')
        ax2_twin.set_ylabel('Traffic Index', color='blue')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        ax2.grid(True, alpha=0.3)
        
        # Weekend vs Weekday
        weekend_comp = self.merged_data.groupby('is_weekend').agg({
            'no2': 'mean',
            'pm10': 'mean',
            'traffic_index': 'mean'
        })
        if len(weekend_comp) > 0:
            # Only set index if we have data
            if len(weekend_comp) == 2:
                weekend_comp.index = ['Weekday', 'Weekend']
            elif len(weekend_comp) == 1:
                # Only one type of day available
                if weekend_comp.index[0] == 0:
                    weekend_comp.index = ['Weekday']
                else:
                    weekend_comp.index = ['Weekend']
            
            weekend_comp[['no2', 'pm10']].plot(kind='bar', ax=axes[1, 0])
            axes[1, 0].set_title('Weekend vs Weekday: Pollutant Levels', fontweight='bold')
            axes[1, 0].set_ylabel('Concentration (µg/m³)')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3, axis='y')
        
        # Seasonal analysis
        seasonal_avg = self.merged_data.groupby('season').agg({
            'no2': 'mean',
            'pm10': 'mean',
            'o3': 'mean',
            'temperature': 'mean'
        })
        seasonal_avg[['no2', 'pm10', 'o3']].plot(kind='bar', ax=axes[1, 1])
        axes[1, 1].set_title('Seasonal Average Pollutant Levels', fontweight='bold')
        axes[1, 1].set_ylabel('Concentration (µg/m³)')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / f'time_analysis_{self.timestamp}.png', dpi=300)
        print(f"   Saved: time_analysis_{self.timestamp}.png")
        plt.close()
    
    def statistical_tests(self):
        """Perform statistical correlation tests."""
        print("\n" + "=" * 70)
        print("STEP 4: STATISTICAL TESTS")
        print("=" * 70)
        
        results = []
        
        # Key relationships to test
        relationships = [
            ('NO2', 'traffic_index', 'no2'),
            ('NO2', 'temperature', 'no2'),
            ('NO2', 'wind_speed', 'no2'),
            ('PM10', 'traffic_index', 'pm10'),
            ('PM10', 'wind_speed', 'pm10'),
            ('PM10', 'precipitation', 'pm10'),
            ('O3', 'temperature', 'o3'),
            ('O3', 'wind_speed', 'o3'),
        ]
        
        print("\nPearson Correlation Tests:")
        print("-" * 70)
        print(f"{'Relationship':<30} {'r':>8} {'p-value':>12} {'Significance':>15}")
        print("-" * 70)
        
        for pollutant, predictor, col in relationships:
            if predictor in self.merged_data.columns and col in self.merged_data.columns:
                data = self.merged_data[[predictor, col]].dropna()
                if len(data) > 2:
                    corr, p_val = pearsonr(data[predictor], data[col])
                    
                    if p_val < 0.001:
                        sig = '***'
                    elif p_val < 0.01:
                        sig = '**'
                    elif p_val < 0.05:
                        sig = '*'
                    else:
                        sig = ''
                    
                    results.append({
                        'pollutant': pollutant,
                        'predictor': predictor,
                        'correlation': corr,
                        'p_value': p_val,
                        'significance': sig
                    })
                    
                    print(f"{pollutant} vs {predictor:<20} {corr:8.3f} {p_val:12.4f} {sig:>15}")
        
        return pd.DataFrame(results)
    
    def regression_analysis(self):
        """Perform multiple regression analysis."""
        print("\n" + "=" * 70)
        print("STEP 5: REGRESSION ANALYSIS")
        print("=" * 70)
        
        regression_results = []
        
        # Predictors
        predictors = ['traffic_index', 'temperature', 'wind_speed', 'precipitation']
        available_predictors = [p for p in predictors if p in self.merged_data.columns]
        
        # For each pollutant
        for pollutant in ['no2', 'pm10', 'o3']:
            if pollutant not in self.merged_data.columns:
                continue
            
            # Prepare data
            X = self.merged_data[available_predictors].dropna()
            y = self.merged_data.loc[X.index, pollutant]
            
            if len(X) > len(available_predictors) and len(y) > 0:
                # Fit model
                model = LinearRegression()
                model.fit(X, y)
                y_pred = model.predict(X)
                
                # Calculate metrics
                r2 = r2_score(y, y_pred)
                
                print(f"\n{pollutant.upper()} Regression Model:")
                print("-" * 50)
                print(f"R² Score: {r2:.4f}")
                print(f"Sample size: {len(X)}")
                print("\nCoefficients:")
                for feature, coef in zip(available_predictors, model.coef_):
                    print(f"  {feature:20s}: {coef:10.4f}")
                print(f"  {'Intercept':20s}: {model.intercept_:10.4f}")
                
                regression_results.append({
                    'pollutant': pollutant.upper(),
                    'r2_score': r2,
                    'sample_size': len(X),
                    'coefficients': dict(zip(available_predictors, model.coef_)),
                    'intercept': model.intercept_
                })
        
        return regression_results
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        print("\n" + "=" * 70)
        print("STEP 6: GENERATING SUMMARY REPORT")
        print("=" * 70)
        
        report_path = self.output_dir / f'correlation_report_{self.timestamp}.txt'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("CORRELATION ANALYSIS REPORT\n")
            f.write("=" * 70 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Dataset summary
            f.write("DATASET SUMMARY\n")
            f.write("-" * 70 + "\n")
            f.write(f"Total records: {len(self.merged_data):,}\n")
            f.write(f"Cities: {', '.join(self.merged_data['city'].unique())}\n")
            f.write(f"Date range: {self.merged_data['date'].min().date()} to "
                   f"{self.merged_data['date'].max().date()}\n\n")
            
            # Top correlations
            f.write("TOP CORRELATIONS WITH AIR POLLUTANTS\n")
            f.write("-" * 70 + "\n")
            
            for pollutant in ['no2', 'pm10', 'o3']:
                if pollutant in self.correlation_matrix.index:
                    f.write(f"\n{pollutant.upper()}:\n")
                    correlations = self.correlation_matrix[pollutant].sort_values(
                        ascending=False, key=abs
                    )
                    for var, corr in correlations.items():
                        if var != pollutant and not pd.isna(corr):
                            f.write(f"  {var:25s}: {corr:7.3f}\n")
            
            # Statistical tests
            f.write("\n" + "=" * 70 + "\n")
            f.write("STATISTICAL SIGNIFICANCE\n")
            f.write("-" * 70 + "\n")
            f.write("Significance levels: *** p<0.001, ** p<0.01, * p<0.05\n\n")
            
            test_results = self.statistical_tests()
            for _, row in test_results.iterrows():
                f.write(f"{row['pollutant']} vs {row['predictor']:<20} "
                       f"r={row['correlation']:7.3f}, p={row['p_value']:.4f} "
                       f"{row['significance']}\n")
            
            # Regression results
            f.write("\n" + "=" * 70 + "\n")
            f.write("REGRESSION ANALYSIS\n")
            f.write("-" * 70 + "\n")
            
            reg_results = self.regression_analysis()
            for result in reg_results:
                f.write(f"\n{result['pollutant']} Model:\n")
                f.write(f"  R² Score: {result['r2_score']:.4f}\n")
                f.write(f"  Sample size: {result['sample_size']}\n")
                f.write("  Coefficients:\n")
                for var, coef in result['coefficients'].items():
                    f.write(f"    {var:20s}: {coef:10.4f}\n")
                f.write(f"    {'Intercept':20s}: {result['intercept']:10.4f}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 70 + "\n")
        
        print(f"\nSummary report saved: {report_path}")
        return report_path
    
    def run_full_analysis(self):
        """Run complete analysis pipeline."""
        print("\n" + "=" * 70)
        print("CORRELATION ANALYSIS PIPELINE")
        print("=" * 70)
        
        # Step 1: Load data
        self.load_data()
        
        if len(self.merged_data) == 0:
            print("\n" + "=" * 70)
            print("⚠ ERROR: No data after merging!")
            print("=" * 70)
            print("\nThe datasets have different date ranges.")
            print("\nSOLUTION:")
            print("  1. Collect weather and traffic data for the same date range as air quality")
            print("  2. Or collect air quality data for the same date range as weather/traffic")
            print("\nTo collect matching data, run:")
            print("  python scripts/main.py --collect")
            print("  (Make sure START_DATE and END_DATE in .env match across all collectors)")
            return None
        
        # Step 2: Calculate correlations
        self.calculate_correlations()
        
        # Step 3: Create visualizations
        self.visualize_correlations()
        
        # Step 4: Statistical tests
        test_results = self.statistical_tests()
        
        # Step 5: Regression analysis
        regression_results = self.regression_analysis()
        
        # Step 6: Generate report
        report_path = self.generate_summary_report()
        
        print("\n" + "=" * 70)
        print("ANALYSIS COMPLETE!")
        print("=" * 70)
        print(f"\nOutput files saved to: {self.output_dir}")
        print(f"  - Correlation heatmaps")
        print(f"  - Scatter plots")
        print(f"  - City-specific analysis")
        print(f"  - Time-based analysis")
        print(f"  - Summary report: {report_path.name}")
        print("\nAll visualizations use timestamp:", self.timestamp)
        
        return {
            'merged_data': self.merged_data,
            'correlation_matrix': self.correlation_matrix,
            'test_results': test_results,
            'regression_results': regression_results
        }


def main():
    """Main function."""
    analyzer = CorrelationAnalyzer()
    results = analyzer.run_full_analysis()
    return results


if __name__ == "__main__":
    main()

