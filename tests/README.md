# Tests

This folder contains unit tests for the MYR/SGD analysis project.

## Test Structure

- `test_main.py` - Tests for main analysis functions
- `test_backtest.py` - Tests for backtesting functionality
- `test_data.py` - Tests for data loading and processing

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_main.py

# Run with coverage
python -m pytest --cov=src tests/
```

## Test Coverage

Tests cover:
- Data loading and validation
- Statistical calculations
- Backtesting logic
- Performance metrics
- Error handling

## Adding Tests

When adding new functionality to `src/`, please add corresponding tests in this directory to maintain code quality and reliability.
