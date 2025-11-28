# Test files for data loading and processing

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDataProcessing:
    """Test cases for data loading and processing"""
    
    def test_csv_loading(self):
        """Test CSV file loading"""
        # Test if data files exist
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        myr_file = os.path.join(data_dir, 'usd_myr.csv')
        sgd_file = os.path.join(data_dir, 'usd_sgd.csv')
        
        assert os.path.exists(myr_file), "MYR CSV file not found"
        assert os.path.exists(sgd_file), "SGD CSV file not found"
        
        # Test loading
        myr_data = pd.read_csv(myr_file, parse_dates=['observation_date'], index_col='observation_date')
        sgd_data = pd.read_csv(sgd_file, parse_dates=['observation_date'], index_col='observation_date')
        
        assert 'DEXMAUS' in myr_data.columns
        assert 'DEXSIUS' in sgd_data.columns
        assert len(myr_data) > 0
        assert len(sgd_data) > 0
    
    def test_data_structure(self):
        """Test data structure and format"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        myr_data = pd.read_csv(os.path.join(data_dir, 'usd_myr.csv'), 
                              parse_dates=['observation_date'], 
                              index_col='observation_date')
        
        # Check index is datetime
        assert isinstance(myr_data.index, pd.DatetimeIndex)
        
        # Check for missing values
        assert myr_data['DEXMAUS'].isna().sum() == 0, "MYR data has missing values"
        
        # Check data types
        assert pd.api.types.is_numeric_dtype(myr_data['DEXMAUS'])
        
        # Check reasonable values (MYR should be around 3-5 per USD)
        assert myr_data['DEXMAUS'].min() > 0
        assert myr_data['DEXMAUS'].max() < 10
    
    def test_cross_rate_calculation(self):
        """Test MYR/SGD cross rate calculation"""
        # Create sample data
        usd_myr = 4.0  # 4 MYR per USD
        usd_sgd = 1.6  # 1.6 SGD per USD
        
        # Calculate cross rate (MYR per SGD)
        myr_sgd = usd_myr / usd_sgd
        
        expected = 4.0 / 1.6  # 2.5 MYR per SGD
        assert abs(myr_sgd - expected) < 1e-10
    
    def test_data_alignment(self):
        """Test data alignment between MYR and SGD"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        myr_data = pd.read_csv(os.path.join(data_dir, 'usd_myr.csv'), 
                              parse_dates=['observation_date'], 
                              index_col='observation_date')
        sgd_data = pd.read_csv(os.path.join(data_dir, 'usd_sgd.csv'), 
                              parse_dates=['observation_date'], 
                              index_col='observation_date')
        
        # Align data
        aligned_data = pd.concat([myr_data['DEXMAUS'], sgd_data['DEXSIUS']], axis=1).dropna()
        
        assert len(aligned_data) > 0
        assert len(aligned_data.columns) == 2
        assert not aligned_data.isna().any().any()  # No missing values after alignment
    
    def test_date_range(self):
        """Test data date range"""
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        myr_data = pd.read_csv(os.path.join(data_dir, 'usd_myr.csv'), 
                              parse_dates=['observation_date'], 
                              index_col='observation_date')
        
        # Check date range is reasonable (should start around 2000)
        assert myr_data.index.year.min() >= 2000
        assert myr_data.index.year.max() >= 2020  # Should have recent data


if __name__ == "__main__":
    pytest.main([__file__])
