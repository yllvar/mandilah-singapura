# Data Folder

This folder contains the raw and processed data files for the MYR/SGD analysis project.

## Files

- `usd_myr.csv` - USD to MYR exchange rate data from FRED (DEXMAUS)
- `usd_sgd.csv` - USD to SGD exchange rate data from FRED (DEXSIUS)

## Data Source

Both files are sourced from the Federal Reserve Economic Data (FRED) database:

- DEXMAUS: U.S. / Malaysia Exchange Rate
- DEXSIUS: U.S. / Singapore Exchange Rate

## Format

- CSV format with daily observations
- Columns: `observation_date`, `DEXMAUS`/`DEXSIUS`
- Date format: YYYY-MM-DD
- Exchange rates: Local currency units per USD

## Update Process

Data can be updated using the pandas_datareader functionality in the analysis scripts, or manually downloaded from FRED.

## Usage

The scripts in `src/` automatically read from these files. If updating data, ensure the column names and format remain consistent.
