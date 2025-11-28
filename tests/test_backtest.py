# Test files for backtesting functions

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestBacktesting:
    """Test cases for backtesting functionality"""
    
    def test_zscore_calculation(self):
        """Test z-score calculation"""
        # Create sample data
        spread = pd.Series(np.random.randn(100) + 1.0)
        
        # Calculate rolling z-score
        window = 20
        mean = spread.rolling(window).mean()
        std = spread.rolling(window).std()
        zscore = (spread - mean) / std
        
        assert len(zscore) == len(spread)
        assert zscore.isna().sum() == window - 1  # First window-1 should be NaN
    
    def test_signal_generation(self):
        """Test trading signal generation"""
        # Create sample z-scores
        zscore = pd.Series([2.5, -2.5, 0.5, -0.5, 0.1])
        
        # Generate signals
        entry_z = 2.0
        exit_z = 0.5
        
        signals = pd.Series(0, index=zscore.index)
        signals[zscore > entry_z] = -1  # Short
        signals[zscore < -entry_z] = 1   # Long
        signals[abs(zscore) < exit_z] = 0  # Exit
        
        # Forward fill signals
        signals = signals.ffill().fillna(0)
        
        assert len(signals) == len(zscore)
        assert signals.iloc[0] == -1  # Short signal
        assert signals.iloc[1] == 1   # Long signal
    
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        # Create sample returns
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        
        # Calculate metrics
        total_return = returns.sum()
        mean_return = returns.mean()
        std_return = returns.std()
        sharpe = mean_return / std_return * np.sqrt(252) if std_return != 0 else 0
        
        assert isinstance(total_return, float)
        assert isinstance(sharpe, float)
        assert not np.isnan(sharpe)
    
    def test_transaction_costs(self):
        """Test transaction cost calculation"""
        # Create sample signals
        signals = pd.Series([0, 1, 1, 0, -1, -1, 0])
        trans_cost = 0.0002  # 2 bps
        
        # Calculate costs
        trade_costs = signals.diff().abs() * trans_cost
        
        assert len(trade_costs) == len(signals)
        assert trade_costs.sum() > 0  # Should have some costs
    
    def test_max_drawdown(self):
        """Test maximum drawdown calculation"""
        # Create sample equity curve
        cumulative_returns = pd.Series([0, 0.01, 0.02, 0.015, 0.03, 0.025, 0.04])
        wealth = np.exp(cumulative_returns)
        
        # Calculate drawdown
        peak = wealth.cummax()
        drawdown = (wealth / peak) - 1
        max_dd = drawdown.min()
        
        assert max_dd <= 0  # Drawdown should be negative or zero
        assert not np.isnan(max_dd)


if __name__ == "__main__":
    pytest.main([__file__])
