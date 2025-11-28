# Source Code

This folder contains the main analysis and backtesting scripts for the MYR/SGD project.

## Scripts

### `main.py`
Comprehensive analysis script that provides:
- Descriptive statistics of exchange rates
- Correlation analysis between MYR and SGD
- Cointegration and stationarity testing
- Regime-specific analysis
- Simple forecasting using ARIMA
- Visualizations of time series and relationships

### `backtest.py`
Mean-reversion strategy backtesting script that includes:
- Grid search optimization for parameters
- In-sample and out-of-sample testing
- Performance metrics (Sharpe, Sortino, drawdown, etc.)
- Transaction cost modeling
- Trade analysis and visualization

## Dependencies

Both scripts require the packages listed in `requirements.txt`:
- pandas
- numpy
- scipy
- matplotlib
- statsmodels
- pandas_datareader (optional, falls back to local CSV)

## Usage

```bash
# Run comprehensive analysis
python src/main.py

# Run backtesting analysis
python src/backtest.py
```

## Data Sources

Scripts automatically try to fetch data from FRED, falling back to local CSV files in the `../data/` directory if needed.
