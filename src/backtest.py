# Improved Robust Backtesting for MYR/SGD Mean-Reversion Strategy
# Enhancements:
# - Fetch data directly from FRED (requires pandas_datareader; pip install if needed)
# - Fallback to local CSVs if fetch fails
# - Add transaction costs (configurable, default 2 bps per trade)
# - Accurate max drawdown calculation
# - Additional metrics: Sortino ratio, number of trades, average trade duration, average win/loss, Kelly fraction
# - Grid search optimization on in-sample period (2021-03-01 to 2023-12-31) to find best parameters (window, entry_z, exit_z) based on Sharpe
# - Apply best parameters to out-of-sample (2024-01-01 to 2025-11-28) and full period
# - Improved visualization with entry/exit markers
# - Regime start date configurable

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# Function to fetch data (FRED or local)
def fetch_data(start_date='2021-03-01', end_date='2025-11-28'):
    try:
        import pandas_datareader.data as web
        print("Fetching from FRED...")
        myr = web.DataReader('DEXMAUS', 'fred', start_date, end_date)['DEXMAUS']
        sgd = web.DataReader('DEXSIUS', 'fred', start_date, end_date)['DEXSIUS']
        df = pd.concat([myr, sgd], axis=1).dropna()
        df.columns = ['USD_MYR', 'USD_SGD']
    except (ImportError, ModuleNotFoundError) as e:
        print(f"pandas_datareader not available or incompatible: {e}")
        print("Loading local CSVs...")
        myr = pd.read_csv('../data/usd_myr.csv', parse_dates=['observation_date'], index_col='observation_date')['DEXMAUS']
        sgd = pd.read_csv('../data/usd_sgd.csv', parse_dates=['observation_date'], index_col='observation_date')['DEXSIUS']
        df = pd.concat([myr, sgd], axis=1).dropna()
        df.columns = ['USD_MYR', 'USD_SGD']
    except Exception as e:
        print(f"FRED fetch failed: {e}. Loading local CSVs...")
        myr = pd.read_csv('../data/usd_myr.csv', parse_dates=['observation_date'], index_col='observation_date')['DEXMAUS']
        sgd = pd.read_csv('../data/usd_sgd.csv', parse_dates=['observation_date'], index_col='observation_date')['DEXSIUS']
        df = pd.concat([myr, sgd], axis=1).dropna()
        df.columns = ['USD_MYR', 'USD_SGD']
    df['MYR_SGD'] = df['USD_MYR'] / df['USD_SGD']
    return df.loc[start_date:end_date]

# Backtest function (returns metrics dict)
def run_backtest(data, window, entry_z, exit_z, trans_cost=0.0002):
    data = data.copy()
    data['log_spread'] = np.log(data['MYR_SGD'])
    
    # Z-score
    data['mean'] = data['log_spread'].rolling(window).mean()
    data['std'] = data['log_spread'].rolling(window).std()
    data['zscore'] = (data['log_spread'] - data['mean']) / data['std']
    
    # Signals
    data['signal'] = 0
    data.loc[data['zscore'] > entry_z, 'signal'] = -1  # Short spread
    data.loc[data['zscore'] < -entry_z, 'signal'] = 1   # Long spread
    data.loc[abs(data['zscore']) < exit_z, 'signal'] = 0  # Exit
    
    data['signal'] = data['signal'].ffill().fillna(0)
    
    # Returns
    data['spread_ret'] = data['log_spread'].diff()
    data['trade_cost'] = data['signal'].diff().abs() * trans_cost
    data['strategy_ret'] = data['signal'].shift(1) * data['spread_ret'] - data['trade_cost'].shift(1).fillna(0)
    
    # Cumulative
    data['cum_ret'] = data['strategy_ret'].cumsum().dropna()
    
    # Metrics
    if len(data['strategy_ret'].dropna()) < 10:
        return {'sharpe': -np.inf}  # Invalid
    
    annual_factor = 252
    total_return = data['strategy_ret'].sum()
    cagr = np.exp(total_return * annual_factor / len(data)) - 1 if len(data) > 0 else 0
    mean_ret = data['strategy_ret'].mean()
    std_ret = data['strategy_ret'].std()
    sharpe = mean_ret / std_ret * np.sqrt(annual_factor) if std_ret != 0 else 0
    
    # Sortino
    downside_std = data['strategy_ret'][data['strategy_ret'] < 0].std()
    sortino = mean_ret / downside_std * np.sqrt(annual_factor) if downside_std != 0 else 0
    
    # Max DD
    wealth = np.exp(data['cum_ret'].fillna(0))
    peak = wealth.cummax()
    drawdown = (wealth / peak) - 1
    max_dd = drawdown.min()
    
    # Trades
    positions = data['signal'] != 0
    trade_starts = (positions.diff() > 0)  # Entry points
    num_trades = trade_starts.sum()
    
    # Trade durations
    trade_durations = []
    current = 0
    for i in range(len(positions)):
        if positions.iloc[i]:
            current += 1
        else:
            if current > 0:
                trade_durations.append(current)
                current = 0
    if current > 0:
        trade_durations.append(current)
    avg_duration = np.mean(trade_durations) if trade_durations else 0
    
    # Avg win/loss
    cum_position = positions.cumsum()  # Unique group per trade block
    trade_returns = data['strategy_ret'].groupby(cum_position).sum()
    trade_returns = trade_returns[trade_returns != 0]  # Only actual trades
    win_rate = (trade_returns > 0).mean() if len(trade_returns) > 0 else 0
    avg_win = trade_returns[trade_returns > 0].mean() if any(trade_returns > 0) else 0
    avg_loss = trade_returns[trade_returns < 0].mean() if any(trade_returns < 0) else -1  # Avoid div0
    
    # Kelly (assuming loss=1 unit, win=b units)
    if avg_loss != 0 and avg_win > 0:
        b = avg_win / -avg_loss
        kelly = (win_rate * b - (1 - win_rate)) / b if b > 0 else 0
    else:
        kelly = 0
    
    metrics = {
        'total_return': total_return,
        'cagr': cagr,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_dd': max_dd,
        'win_rate': win_rate,
        'num_trades': num_trades,
        'avg_duration': avg_duration,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'kelly': kelly
    }
    return metrics, data

# Print metrics table
def print_metrics(period_name, metrics):
    print(f"=== {period_name} Performance ===")
    print(f"Total log return: {metrics['total_return']:.3f}")
    print(f"CAGR: {metrics['cagr']*100:.2f}%")
    print(f"Annualized Sharpe: {metrics['sharpe']:.3f}")
    print(f"Annualized Sortino: {metrics['sortino']:.3f}")
    print(f"Max drawdown: {metrics['max_dd']*100:.2f}%")
    print(f"Win rate: {metrics['win_rate']*100:.1f}%")
    print(f"Number of trades: {metrics['num_trades']}")
    print(f"Avg trade duration (days): {metrics['avg_duration']:.1f}")
    print(f"Avg win return: {metrics['avg_win']:.4f}")
    print(f"Avg loss return: {metrics['avg_loss']:.4f}")
    print(f"Kelly fraction: {metrics['kelly']:.2f}")

# Visualization
def plot_results(data, entry_z, exit_z):
    plt.figure(figsize=(14, 8))
    
    # Equity curve
    plt.subplot(2, 1, 1)
    data['cum_ret'].plot(label='Strategy Cum Return')
    (data['log_spread'] - data['log_spread'].iloc[0]).plot(label='Raw Spread Cum Change', alpha=0.5)
    plt.title('Strategy Equity Curve vs Raw Spread')
    plt.legend()
    
    # Z-score with signals
    plt.subplot(2, 1, 2)
    data['zscore'].plot(color='gray', alpha=0.7, label='Z-score')
    data['log_spread'].rolling(20).mean().plot(color='black', label='20d MA Spread')
    
    # Entries/Exits
    entry_long = data[(data['signal'].shift(1) == 0) & (data['signal'] == 1)].index
    entry_short = data[(data['signal'].shift(1) == 0) & (data['signal'] == -1)].index
    exits = data[(data['signal'].shift(1) != 0) & (data['signal'] == 0)].index
    
    plt.scatter(entry_long, data['zscore'].loc[entry_long], color='green', marker='^', label='Long Entry')
    plt.scatter(entry_short, data['zscore'].loc[entry_short], color='red', marker='v', label='Short Entry')
    plt.scatter(exits, data['zscore'].loc[exits], color='black', marker='x', label='Exit')
    
    plt.axhline(entry_z, color='red', linestyle='--')
    plt.axhline(-entry_z, color='green', linestyle='--')
    plt.axhline(exit_z, color='blue', linestyle='--', alpha=0.5)
    plt.axhline(-exit_z, color='blue', linestyle='--', alpha=0.5)
    plt.title('Z-score with Entry/Exit Signals')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

# Main
if __name__ == "__main__":
    df = fetch_data()
    
    # Split samples
    in_sample = df.loc['2021-03-01':'2023-12-31']
    out_sample = df.loc['2024-01-01':'2025-11-28']
    full_sample = df
    
    # Grid search params
    windows = [30, 60, 90, 120]
    entries = [1.5, 1.75, 2.0, 2.25]
    exits = [0.0, 0.25, 0.5, 0.75]
    
    best_sharpe = -np.inf
    best_params = None
    for w in windows:
        for en in entries:
            for ex in exits:
                metrics, _ = run_backtest(in_sample, w, en, ex)
                if metrics['sharpe'] > best_sharpe:
                    best_sharpe = metrics['sharpe']
                    best_params = (w, en, ex)
    
    print(f"\nBest In-Sample Params (max Sharpe {best_sharpe:.3f}): window={best_params[0]}, entry_z={best_params[1]}, exit_z={best_params[2]}")
    
    # Run on in-sample
    in_metrics, _ = run_backtest(in_sample, *best_params)
    print_metrics("In-Sample (2021-03-01 to 2023-12-31)", in_metrics)
    
    # Run on out-of-sample
    out_metrics, out_data = run_backtest(out_sample, *best_params)
    print_metrics("Out-of-Sample (2024-01-01 to 2025-11-28)", out_metrics)
    
    # Run on full
    full_metrics, full_data = run_backtest(full_sample, *best_params)
    print_metrics("Full Period (2021-03-01 to 2025-11-28)", full_metrics)
    
    # Plot out-of-sample as example
    plot_results(out_data, best_params[1], best_params[2])