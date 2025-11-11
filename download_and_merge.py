#!/usr/bin/env python3
"""
Data Ingestion and Merge Script
Loads multiple CSV files, merges them, converts timezone, and filters trading hours.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import glob
from datetime import datetime
import pytz

def load_and_merge_csv_files(data_dir='.', pattern='1m_data_part*.csv'):
    """
    Load and merge all CSV files matching the pattern.

    Args:
        data_dir: Directory containing CSV files
        pattern: Glob pattern to match CSV files

    Returns:
        Merged DataFrame sorted by timestamp
    """
    print("=" * 80)
    print("STEP 1: DATA INGESTION & MERGE")
    print("=" * 80)

    # Find all CSV files
    csv_files = sorted(glob.glob(str(Path(data_dir) / pattern)))
    print(f"\nFound {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {Path(f).name}")

    # Load and merge
    dfs = []
    for csv_file in csv_files:
        print(f"\nLoading {Path(csv_file).name}...", end=' ')
        df = pd.read_csv(csv_file, sep='\t')
        print(f"({len(df):,} rows)")
        dfs.append(df)

    # Concatenate all dataframes
    print("\nMerging all dataframes...")
    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"Total rows before cleaning: {len(merged_df):,}")

    return merged_df, csv_files

def clean_and_convert_timezone(df):
    """
    Clean data and convert timezone from UTC+3 to America/New_York.

    Args:
        df: Input DataFrame with DateTime column

    Returns:
        Cleaned DataFrame with timezone-converted index
    """
    print("\n" + "=" * 80)
    print("STEP 2: TIMEZONE CONVERSION & CLEANING")
    print("=" * 80)

    # Parse datetime
    print("\nParsing DateTime column...")
    df['DateTime'] = pd.to_datetime(df['DateTime'], format='%Y.%m.%d %H:%M:%S')

    # Sort by datetime
    print("Sorting by timestamp...")
    df = df.sort_values('DateTime').reset_index(drop=True)

    # Remove duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=['DateTime'], keep='first')
    duplicates_removed = initial_count - len(df)
    print(f"Removed {duplicates_removed:,} duplicate timestamps")

    # Localize to UTC+3 (Etc/GMT-3)
    print("\nLocalizing to UTC+3...")
    df['DateTime'] = df['DateTime'].dt.tz_localize('Etc/GMT-3')

    # Convert to America/New_York
    print("Converting to America/New_York timezone...")
    df['DateTime'] = df['DateTime'].dt.tz_convert('America/New_York')

    # Set as index
    df = df.set_index('DateTime')

    print(f"\nDate range: {df.index.min()} to {df.index.max()}")
    print(f"Total rows after timezone conversion: {len(df):,}")

    return df

def filter_trading_hours(df):
    """
    Filter data to include only NQ trading hours in America/New_York timezone.

    Rules:
    - Remove Friday 17:01 ET to Sunday 17:59 ET
    - Remove daily settlement halt (17:00-18:00 ET on weekdays)

    Args:
        df: DataFrame with DateTime index in America/New_York timezone

    Returns:
        Filtered DataFrame
    """
    print("\n" + "=" * 80)
    print("STEP 3: TRADING HOURS FILTER")
    print("=" * 80)

    initial_count = len(df)

    # Add helper columns
    df['dayofweek'] = df.index.dayofweek  # 0=Monday, 4=Friday, 6=Sunday
    df['hour'] = df.index.hour
    df['minute'] = df.index.minute

    # Rule 1: Remove Friday 17:01 ET to Sunday 17:59 ET
    print("\nApplying Rule 1: Remove Friday 17:01 - Sunday 17:59...")

    # Friday after 17:00
    friday_close = (df['dayofweek'] == 4) & ((df['hour'] > 17) | ((df['hour'] == 17) & (df['minute'] > 0)))

    # Saturday (all day)
    saturday = df['dayofweek'] == 5

    # Sunday before 18:00
    sunday_before_open = (df['dayofweek'] == 6) & (df['hour'] < 18)

    weekend_mask = friday_close | saturday | sunday_before_open
    weekend_removed = weekend_mask.sum()
    df = df[~weekend_mask]
    print(f"Removed {weekend_removed:,} weekend/non-trading rows")

    # Rule 2: Remove daily settlement halt (17:00-17:59 ET on Mon-Fri)
    print("\nApplying Rule 2: Remove daily settlement halt (17:00-17:59)...")

    # Update dayofweek after filtering
    df['dayofweek'] = df.index.dayofweek
    df['hour'] = df.index.hour

    # Weekdays during settlement hour
    settlement_mask = (df['dayofweek'] < 5) & (df['hour'] == 17)
    settlement_removed = settlement_mask.sum()
    df = df[~settlement_mask]
    print(f"Removed {settlement_removed:,} settlement halt rows")

    # Drop helper columns
    df = df.drop(columns=['dayofweek', 'hour', 'minute'])

    final_count = len(df)
    total_removed = initial_count - final_count
    print(f"\n{'='*80}")
    print(f"Total rows removed: {total_removed:,} ({100*total_removed/initial_count:.2f}%)")
    print(f"Final row count: {final_count:,}")
    print(f"{'='*80}")

    return df

def export_clean_data(df, output_file='nq_1m_et.csv'):
    """
    Export cleaned data to CSV.

    Args:
        df: Cleaned DataFrame
        output_file: Output filename
    """
    print("\n" + "=" * 80)
    print("STEP 4: EXPORT CLEAN DATA")
    print("=" * 80)

    print(f"\nExporting to {output_file}...")
    df.to_csv(output_file)

    file_size = Path(output_file).stat().st_size / (1024**2)
    print(f"File saved: {output_file} ({file_size:.2f} MB)")
    print(f"Rows: {len(df):,}")
    print(f"Columns: {', '.join(df.columns)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")

def main():
    """Main execution function."""
    print("\n" + "=" * 80)
    print("NQ 1-MINUTE DATA PROCESSOR")
    print("UTC+3 → America/New_York | Trading Hours Filter")
    print("=" * 80)

    # Step 1: Load and merge
    merged_df, csv_files = load_and_merge_csv_files()

    # Step 2: Clean and convert timezone
    clean_df = clean_and_convert_timezone(merged_df)

    # Step 3: Filter trading hours
    filtered_df = filter_trading_hours(clean_df)

    # Step 4: Export
    export_clean_data(filtered_df)

    print("\n" + "=" * 80)
    print("✓ DATA PROCESSING COMPLETE")
    print("=" * 80)
    print("\nNext step: Run run_analysis.py to compute the 108-variant probability map")

if __name__ == '__main__':
    main()
