import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from datetime import datetime

# Fix for Python 3.12 distutils compatibility
try:
    import pandas_datareader.data as web
    PANDAS_DATAREADER_AVAILABLE = True
except ImportError as e:
    print(f"pandas_datareader not available: {e}")
    PANDAS_DATAREADER_AVAILABLE = False

# Step 1: Fetch data from FRED (or load from CSV if fetch fails)
def fetch_data(start_date='2000-01-01', end_date=datetime.now().strftime('%Y-%m-%d')):
    if PANDAS_DATAREADER_AVAILABLE:
        try:
            print("Fetching data from FRED...")
            myr = web.DataReader('DEXMAUS', 'fred', start_date, end_date)
            sgd = web.DataReader('DEXSIUS', 'fred', start_date, end_date)
            myr.columns = ['USD_MYR']
            sgd.columns = ['USD_SGD']
            df = pd.concat([myr, sgd], axis=1).dropna()
            print(f"Data fetched successfully from {start_date} to {end_date}. Rows: {len(df)}")
            return df
        except Exception as e:
            print(f"Error fetching from FRED: {e}")
            print("Loading from local CSVs instead...")
    
    # Fallback to local CSVs
    print("Loading from local CSVs...")
    myr = pd.read_csv('../data/usd_myr.csv', parse_dates=['observation_date'], index_col='observation_date')
    sgd = pd.read_csv('../data/usd_sgd.csv', parse_dates=['observation_date'], index_col='observation_date')
    myr = myr[['DEXMAUS']].rename(columns={'DEXMAUS': 'USD_MYR'})
    sgd = sgd[['DEXSIUS']].rename(columns={'DEXSIUS': 'USD_SGD'})
    df = pd.concat([myr, sgd], axis=1).dropna()
    print(f"Loaded local data. Rows: {len(df)}")
    return df

# Step 2: Comprehensive Analysis Functions
def compute_basics(df):
    print("\n=== 1. Descriptive Statistics ===")
    print("Explanation: This section provides basic stats on the exchange rates. USD_MYR and USD_SGD represent how many local units per USD. Higher values mean weaker local currency.")
    print(df.describe())
    
    df['MYR_SGD'] = df['USD_MYR'] / df['USD_SGD']  # Cross-rate: MYR per SGD
    print("\nMYR/SGD Cross-Rate Stats (higher = MYR weaker vs SGD):")
    print(df['MYR_SGD'].describe())

def compute_correlations(df):
    print("\n=== 2. Correlation Analysis ===")
    print("Explanation: We compute Pearson correlation on daily log returns to measure how similarly MYR and SGD move against the USD. A positive value indicates they weaken/strengthen together, common in ASEAN due to shared factors like US rates and China trade. Typical range: 0.4-0.6 long-term.")
    
    log_returns = np.log(df).diff().dropna()
    corr_coef, p_value = stats.pearsonr(log_returns['USD_MYR'], log_returns['USD_SGD'])
    print(f"Full Period Pearson Correlation: {corr_coef:.4f} (p-value: {p_value:.4f})")
    
    rolling_corr = log_returns['USD_MYR'].rolling(252).corr(log_returns['USD_SGD'])
    print(f"Median 1-Year Rolling Correlation: {rolling_corr.median():.4f}")
    print("Insight: Correlation spikes during crises (e.g., 2008, 2020) and drops in stable periods. Useful for diversification or hedging.")
    
    return rolling_corr

def compute_cointegration_and_stationarity(df):
    print("\n=== 3. Cointegration and Stationarity Tests ===")
    print("Explanation: Cointegration checks if USD/MYR and USD/SGD have a stable long-term relationship. Stationarity tests check if the spread tends to revert to a mean.")
    print("Note: Advanced statistical tests require statsmodels package. Using basic analysis instead.")
    
    df['log_spread'] = np.log(df['USD_MYR']) - np.log(df['USD_SGD'])  # log(MYR/SGD)
    
    # Basic stationarity check using simple statistics
    spread_mean = df['log_spread'].mean()
    spread_std = df['log_spread'].std()
    
    # Calculate how often the spread returns to mean
    deviations = df['log_spread'] - spread_mean
    mean_reversions = (deviations.shift(1) * deviations < 0).sum()  # Sign changes
    total_periods = len(deviations) - 1
    reversion_rate = mean_reversions / total_periods if total_periods > 0 else 0
    
    print(f"log(MYR/SGD) Spread - Mean: {spread_mean:.4f}, Std: {spread_std:.4f}")
    print(f"Mean reversion rate: {reversion_rate:.2%} (higher suggests more mean-reverting behavior)")
    
    if reversion_rate > 0.3:
        print("Insight: High mean reversion rate suggests potential for mean-reversion strategies.")
    else:
        print("Insight: Low mean reversion rate suggests trending behavior - be cautious with mean-reversion strategies.")

def analyze_regimes(df):
    print("\n=== 4. Regime-Specific Analysis ===")
    print("Explanation: MYR/SGD shows regime shifts due to policy changes and crises. We analyze key periods to identify behavioral patterns.")
    
    regimes = {
        'Full (2000-2025)': df,
        'Post-Peg (2005-2014)': df['2005-07-01':'2014-12-31'],
        'Oil Crash/Recovery (2015-2020)': df['2015-01-01':'2020-12-31'],
        'Post-COVID (2021-2025)': df['2021-01-01':]
    }
    
    for name, sub_df in regimes.items():
        if len(sub_df) < 100: 
            continue
            
        # Calculate basic statistics for each regime
        log_spread = np.log(sub_df['USD_MYR'] / sub_df['USD_SGD'])
        volatility = log_spread.std() * np.sqrt(252)  # Annualized volatility
        trend = (log_spread.iloc[-1] - log_spread.iloc[0]) / len(log_spread) * 252  # Annualized trend
        
        print(f"{name} - Volatility: {volatility:.3f}, Trend: {trend:+.3f}/year")
        
        if abs(trend) < 0.1:
            print(f"  -> Stable regime (suitable for mean-reversion)")
        elif trend > 0.1:
            print(f"  -> MYR weakening regime")
        else:
            print(f"  -> MYR strengthening regime")

def forecast_myr(df):
    print("\n=== 5. Simple Forecasting ===")
    print("Explanation: Basic trend extrapolation for log(MYR/SGD). Note: This is simplified - real forecasts should incorporate fundamentals like GDP, interest rates, and policy changes.")
    
    log_spread = np.log(df['USD_MYR'] / df['USD_SGD']).dropna()
    
    # Simple linear trend forecast
    recent_data = log_spread.tail(252)  # Last year of data
    x = np.arange(len(recent_data))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, recent_data)
    
    # Forecast 6 months ahead (126 trading days)
    last_value = recent_data.iloc[-1]
    forecast_6m = last_value + slope * 126
    
    print(f"Current log(MYR/SGD): {last_value:.4f}")
    print(f"6-month trend forecast: {forecast_6m:.4f}")
    print(f"Implied MYR/SGD rate: {np.exp(forecast_6m):.4f}")
    print(f"Trend strength (R²): {r_value**2:.3f}")
    
    if forecast_6m < last_value:
        print("Insight: Trend suggests MYR strengthening vs SGD")
    else:
        print("Insight: Trend suggests MYR weakening vs SGD")
    
    print("Note: This is a simple trend extrapolation. Consult economic analysis for proper forecasts.")

def visualize(df, rolling_corr):
    print("\n=== 6. Visualizations ===")
    print("Explanation: Plots provide intuitive insights. Time series show trends, spread highlights divergences, rolling corr shows relationship stability.")
    
    plt.figure(figsize=(14, 10))
    
    # Subplot 1: Exchange Rates
    plt.subplot(3, 1, 1)
    df[['USD_MYR', 'USD_SGD']].plot(ax=plt.gca())
    plt.title('USD/MYR and USD/SGD Time Series')
    plt.ylabel('Local per USD')
    
    # Subplot 2: Log Spread
    plt.subplot(3, 1, 2)
    df['log_spread'].plot(color='red')
    plt.axhline(df['log_spread'].mean(), color='black', linestyle='--')
    plt.title('log(MYR/SGD) Spread')
    plt.ylabel('Log Spread')
    
    # Subplot 3: Rolling Correlation
    plt.subplot(3, 1, 3)
    rolling_corr.plot(color='blue')
    plt.axhline(rolling_corr.mean(), color='green', linestyle='--')
    plt.title('1-Year Rolling Correlation of Returns')
    plt.ylabel('Correlation')
    
    plt.tight_layout()
    plt.savefig('myr_sgd_analysis.png')
    print("Visualizations saved as 'myr_sgd_analysis.png'. Open to view.")

# Main Execution
if __name__ == "__main__":
    df = fetch_data()
    compute_basics(df)
    rolling_corr = compute_correlations(df)
    compute_cointegration_and_stationarity(df)
    analyze_regimes(df)
    forecast_myr(df)
    visualize(df, rolling_corr)
    print("\nAnalysis Complete. For predictions, consult latest economic reports as models are indicative.")
