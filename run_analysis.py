#!/usr/bin/env python3
"""
108-Variant NY Probability Map Analysis (CORRECTED LOGIC)

Key Fix: London Session is now 00:00-05:00 (merged, gapless)
This eliminates the time gap issue and creates continuous sessions.
"""

import pandas as pd
import numpy as np
import json
from datetime import time, timedelta
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION (CORRECTED)
# ============================================================================

# Session time boundaries (America/New_York) - GAPLESS!
SESSION_TIMES = {
    'asia_start': time(20, 0),      # 20:00 (previous day)
    'asia_end': time(0, 0),         # 00:00
    'london_start': time(0, 0),     # 00:00 (MERGED - no gap!)
    'london_end': time(5, 0),       # 05:00 (MERGED - full European session)
    'transition_start': time(5, 0), # 05:00
    'transition_end': time(8, 30),  # 08:30
    'ny_start': time(8, 30),        # 08:30
    'ny_end': time(11, 0),          # 11:00
}

# Analysis parameters
ASIA_RANGE_WINDOW = 200  # Rolling window for Asia range quantiles
LONDON_MID_TOLERANCE = 0.25  # 25% of London range for "Within" band
PENETRATION_WINDOW = 30  # Minutes to track penetration after first sweep

# ============================================================================
# STEP 1: DATA LOADING
# ============================================================================

def load_clean_data(filepath='nq_1m_et.csv'):
    """Load the cleaned NQ 1-minute data."""
    print("="*80)
    print("LOADING CLEAN DATA")
    print("="*80)

    df = pd.read_csv(filepath, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York')
    print(f"\nLoaded {len(df):,} rows")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print(f"Columns: {list(df.columns)}")

    return df

# ============================================================================
# STEP 2: SESSION BOUNDARY CALCULATION (CORRECTED)
# ============================================================================

def get_session_data(df, date, start_time, end_time, prev_day=False):
    """
    Extract OHLC data for a specific session.

    Args:
        df: DataFrame with minute data
        date: Trading date
        start_time: Session start time
        end_time: Session end time
        prev_day: If True, session starts on previous day

    Returns:
        Dictionary with session OHLC, midpoint, and range
    """
    if prev_day:
        start_dt = pd.Timestamp.combine(date - pd.Timedelta(days=1), start_time)
    else:
        start_dt = pd.Timestamp.combine(date, start_time)

    end_dt = pd.Timestamp.combine(date, end_time)

    # Handle midnight crossing
    if end_time < start_time and not prev_day:
        end_dt += pd.Timedelta(days=1)

    # Localize to America/New_York (handle DST transitions)
    try:
        start_dt = start_dt.tz_localize('America/New_York', nonexistent='shift_forward', ambiguous='NaT')
    except:
        start_dt = start_dt.tz_localize('America/New_York', nonexistent='shift_forward')

    try:
        end_dt = end_dt.tz_localize('America/New_York', nonexistent='shift_forward', ambiguous='NaT')
    except:
        end_dt = end_dt.tz_localize('America/New_York', nonexistent='shift_forward')

    # Extract session data
    session_data = df[(df.index >= start_dt) & (df.index < end_dt)]

    if len(session_data) == 0:
        return None

    return {
        'open': session_data['Open'].iloc[0],
        'high': session_data['High'].max(),
        'low': session_data['Low'].min(),
        'close': session_data['Close'].iloc[-1],
        'midpoint': (session_data['High'].max() + session_data['Low'].min()) / 2,
        'range': session_data['High'].max() - session_data['Low'].min(),
        'data': session_data
    }

def calculate_daily_sessions(df):
    """
    Calculate session boundaries and features for each trading day.

    CORRECTED: London is now 00:00-05:00 (gapless!)

    Returns:
        DataFrame with one row per trading day containing all session features
    """
    print("\n" + "="*80)
    print("CALCULATING SESSION BOUNDARIES (CORRECTED)")
    print("="*80)
    print("\nSession Times:")
    print("  Asia:       20:00 (prev) - 00:00")
    print("  London:     00:00 - 05:00 (MERGED - No Gap!)")
    print("  Transition: 05:00 - 08:30")
    print("  NY:         08:30 - 11:00")

    # Get unique trading dates
    dates = df.index.normalize().unique()

    daily_sessions = []

    for i, date in enumerate(dates):
        if i % 100 == 0:
            print(f"Processing day {i+1}/{len(dates)}...", end='\r')

        # Extract each session
        asia = get_session_data(df, date,
                               SESSION_TIMES['asia_start'],
                               SESSION_TIMES['asia_end'],
                               prev_day=True)

        # CORRECTED: London is now 00:00-05:00 (full session, no gap)
        london = get_session_data(df, date,
                                 SESSION_TIMES['london_start'],
                                 SESSION_TIMES['london_end'])

        transition = get_session_data(df, date,
                                     SESSION_TIMES['transition_start'],
                                     SESSION_TIMES['transition_end'])

        ny = get_session_data(df, date,
                             SESSION_TIMES['ny_start'],
                             SESSION_TIMES['ny_end'])

        # Skip days with missing sessions
        if any(s is None for s in [asia, london, transition, ny]):
            continue

        daily_sessions.append({
            'date': date,
            # Asia session
            'asia_open': asia['open'],
            'asia_high': asia['high'],
            'asia_low': asia['low'],
            'asia_close': asia['close'],
            'asia_mid': asia['midpoint'],
            'asia_range': asia['range'],
            # London session (CORRECTED: now 00:00-05:00)
            'london_open': london['open'],
            'london_high': london['high'],
            'london_low': london['low'],
            'london_close': london['close'],
            'london_mid': london['midpoint'],
            'london_range': london['range'],
            # Transition
            'transition_open': transition['open'],
            'transition_high': transition['high'],
            'transition_low': transition['low'],
            'transition_close': transition['close'],
            # NY session
            'ny_open': ny['open'],
            'ny_high': ny['high'],
            'ny_low': ny['low'],
            'ny_close': ny['close'],
            # Raw data for label calculation
            'ny_data': ny['data']
        })

    sessions_df = pd.DataFrame(daily_sessions)
    print(f"\n\nCalculated sessions for {len(sessions_df):,} trading days")

    return sessions_df

# ============================================================================
# STEP 3: 108-VARIANT CONTEXT ENGINE
# ============================================================================

def calculate_asia_range_regime(df):
    """
    Calculate dynamic Asia Range Regime using 200-day rolling quantiles.

    Returns:
        DataFrame with 'asia_regime' column (Compressed/Normal/Expanded)
    """
    print("\n" + "="*80)
    print("CALCULATING ASIA RANGE REGIME (Dynamic)")
    print("="*80)

    # Calculate rolling quantiles
    df['asia_range_q33'] = df['asia_range'].rolling(
        window=ASIA_RANGE_WINDOW, min_periods=50
    ).quantile(0.33)

    df['asia_range_q66'] = df['asia_range'].rolling(
        window=ASIA_RANGE_WINDOW, min_periods=50
    ).quantile(0.66)

    # Classify regime
    def classify_regime(row):
        if pd.isna(row['asia_range_q33']):
            return None
        if row['asia_range'] < row['asia_range_q33']:
            return 'Compressed'
        elif row['asia_range'] > row['asia_range_q66']:
            return 'Expanded'
        else:
            return 'Normal'

    df['asia_regime'] = df.apply(classify_regime, axis=1)

    # Remove rows with insufficient data
    initial_count = len(df)
    df = df.dropna(subset=['asia_regime'])
    removed = initial_count - len(df)

    print(f"\nRemoved {removed} days (insufficient rolling data)")
    print(f"Remaining days: {len(df):,}")
    print(f"\nAsia Regime Distribution:")
    print(df['asia_regime'].value_counts())

    return df

def calculate_london_sweep(df):
    """
    Calculate London Sweep pattern relative to Asia range.

    CORRECTED: London is now 00:00-05:00 vs Asia 20:00-00:00

    Returns:
        DataFrame with 'london_sweep' column (None/High/Low/Both)
    """
    print("\n" + "="*80)
    print("CALCULATING LONDON SWEEP PATTERN (CORRECTED)")
    print("="*80)
    print("Comparing London (00:00-05:00) vs Asia (20:00-00:00)")

    def classify_sweep(row):
        swept_high = row['london_high'] > row['asia_high']
        swept_low = row['london_low'] < row['asia_low']

        if swept_high and swept_low:
            return 'Both'
        elif swept_high:
            return 'High'
        elif swept_low:
            return 'Low'
        else:
            return 'None'

    df['london_sweep'] = df.apply(classify_sweep, axis=1)

    print(f"\nLondon Sweep Distribution:")
    print(df['london_sweep'].value_counts())

    return df

def calculate_open_vs_london_mid(df, open_col, label):
    """
    Calculate Open position relative to London Midpoint with tolerance band.

    CORRECTED: London Mid is now from 00:00-05:00 session

    Args:
        df: DataFrame
        open_col: Column name for the open price
        label: Label for the new column

    Returns:
        DataFrame with new column (Above/Below/Within)
    """
    print(f"\n{'='*80}")
    print(f"CALCULATING {label.upper()} (CORRECTED)")
    print(f"{'='*80}")
    print(f"Using London Mid from 00:00-05:00 session")

    # Calculate tolerance band
    df['london_mid_tolerance'] = df['london_range'] * LONDON_MID_TOLERANCE
    df['london_mid_upper'] = df['london_mid'] + df['london_mid_tolerance']
    df['london_mid_lower'] = df['london_mid'] - df['london_mid_tolerance']

    def classify_position(row):
        if row[open_col] > row['london_mid_upper']:
            return 'Above'
        elif row[open_col] < row['london_mid_lower']:
            return 'Below'
        else:
            return 'Within'

    df[label] = df.apply(classify_position, axis=1)

    print(f"\n{label} Distribution:")
    print(df[label].value_counts())

    return df

def create_variant_fingerprint(df):
    """
    Create unique variant fingerprint from 4 factors.

    Returns:
        DataFrame with 'variant' column
    """
    print("\n" + "="*80)
    print("CREATING VARIANT FINGERPRINTS")
    print("="*80)

    df['variant'] = (
        df['asia_regime'] + '|' +
        df['london_sweep'] + '|' +
        df['transition_vs_london_mid'] + '|' +
        df['ny_open_vs_london_mid']
    )

    unique_variants = df['variant'].nunique()
    print(f"\nUnique variants found: {unique_variants}")
    print(f"\nTop 10 most common variants:")
    print(df['variant'].value_counts().head(10))

    return df

# ============================================================================
# STEP 4: LABEL CALCULATION (CORRECTED)
# ============================================================================

def calculate_labels(df):
    """
    Calculate outcome labels for the NY window (08:30-11:00).

    CORRECTED: Target levels are now from London 00:00-05:00 session

    Labels:
    - first_sweep_side: Which level was hit first (High/Low)
    - fail_flag: Did the opposite level get hit after first sweep?
    - both_flag: Were both levels hit during the window?
    - median_penetration: Median overshoot after first sweep (30min window)

    Returns:
        DataFrame with label columns
    """
    print("\n" + "="*80)
    print("CALCULATING OUTCOME LABELS (CORRECTED)")
    print("="*80)
    print("Target levels from London 00:00-05:00 session")

    labels = []

    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"Processing label {idx+1}/{len(df)}...", end='\r')

        ny_data = row['ny_data']
        target_high = row['london_high']  # From 00:00-05:00 session
        target_low = row['london_low']    # From 00:00-05:00 session

        # Track sweep times
        hit_high_time = None
        hit_low_time = None

        for ts, price_row in ny_data.iterrows():
            if price_row['High'] >= target_high and hit_high_time is None:
                hit_high_time = ts
            if price_row['Low'] <= target_low and hit_low_time is None:
                hit_low_time = ts

        # Determine first sweep side
        if hit_high_time is None and hit_low_time is None:
            first_sweep_side = None
            first_sweep_time = None
        elif hit_high_time is None:
            first_sweep_side = 'Low'
            first_sweep_time = hit_low_time
        elif hit_low_time is None:
            first_sweep_side = 'High'
            first_sweep_time = hit_high_time
        else:
            if hit_high_time < hit_low_time:
                first_sweep_side = 'High'
                first_sweep_time = hit_high_time
            else:
                first_sweep_side = 'Low'
                first_sweep_time = hit_low_time

        # Calculate flags
        both_flag = 1 if (hit_high_time is not None and hit_low_time is not None) else 0

        if first_sweep_side == 'High':
            fail_flag = 1 if hit_low_time is not None else 0
        elif first_sweep_side == 'Low':
            fail_flag = 1 if hit_high_time is not None else 0
        else:
            fail_flag = 0

        # Calculate median penetration
        median_penetration = np.nan

        if first_sweep_time is not None:
            penetration_window_end = first_sweep_time + pd.Timedelta(minutes=PENETRATION_WINDOW)
            penetration_data = ny_data[
                (ny_data.index >= first_sweep_time) &
                (ny_data.index < penetration_window_end)
            ]

            if len(penetration_data) > 0:
                if first_sweep_side == 'High':
                    # Track overshoots above target_high
                    overshoots = penetration_data['High'] - target_high
                    overshoots = overshoots[overshoots > 0]
                else:
                    # Track overshoots below target_low
                    overshoots = target_low - penetration_data['Low']
                    overshoots = overshoots[overshoots > 0]

                if len(overshoots) > 0:
                    median_penetration = overshoots.median()

        labels.append({
            'first_sweep_side': first_sweep_side,
            'fail_flag': fail_flag,
            'both_flag': both_flag,
            'median_penetration': median_penetration
        })

    # Add labels to dataframe
    labels_df = pd.DataFrame(labels, index=df.index)
    df = pd.concat([df, labels_df], axis=1)

    # Remove rows with no sweep
    initial_count = len(df)
    df = df.dropna(subset=['first_sweep_side'])
    removed = initial_count - len(df)

    print(f"\n\nRemoved {removed} days with no sweep")
    print(f"Remaining days: {len(df):,}")

    print(f"\nFirst Sweep Distribution:")
    print(df['first_sweep_side'].value_counts())

    print(f"\nFail Rate: {df['fail_flag'].mean()*100:.2f}%")
    print(f"Both Hit Rate: {df['both_flag'].mean()*100:.2f}%")
    print(f"Median Penetration (all): {df['median_penetration'].median():.2f} points")

    return df

# ============================================================================
# STEP 5: AGGREGATE PROBABILITIES
# ============================================================================

def aggregate_probabilities(df):
    """
    Aggregate outcomes by variant to create probability map.

    Returns:
        DataFrame with probability statistics for each variant
    """
    print("\n" + "="*80)
    print("AGGREGATING PROBABILITIES BY VARIANT")
    print("="*80)

    results = []

    for variant in df['variant'].unique():
        variant_data = df[df['variant'] == variant]
        n = len(variant_data)

        # Calculate probabilities
        first_high_count = (variant_data['first_sweep_side'] == 'High').sum()
        first_low_count = (variant_data['first_sweep_side'] == 'Low').sum()

        first_high_pct = (first_high_count / n * 100) if n > 0 else 0
        first_low_pct = (first_low_count / n * 100) if n > 0 else 0

        sweep_both_pct = variant_data['both_flag'].mean() * 100
        fail_pct = variant_data['fail_flag'].mean() * 100

        # Median penetration by side
        high_sweeps = variant_data[variant_data['first_sweep_side'] == 'High']
        low_sweeps = variant_data[variant_data['first_sweep_side'] == 'Low']

        median_pen_high = high_sweeps['median_penetration'].median() if len(high_sweeps) > 0 else np.nan
        median_pen_low = low_sweeps['median_penetration'].median() if len(low_sweeps) > 0 else np.nan

        # Reliability tag
        if n < 50:
            reliability = 'Low'
        elif n < 150:
            reliability = 'Medium'
        else:
            reliability = 'High'

        # Parse variant components
        parts = variant.split('|')

        results.append({
            'variant': variant,
            'asia_regime': parts[0],
            'london_sweep': parts[1],
            'transition_vs_london': parts[2],
            'ny_open_vs_london': parts[3],
            'n': n,
            'first_high_pct': round(first_high_pct, 2),
            'first_low_pct': round(first_low_pct, 2),
            'sweep_both_pct': round(sweep_both_pct, 2),
            'fail_pct': round(fail_pct, 2),
            'median_pen_high': round(median_pen_high, 2) if not np.isnan(median_pen_high) else None,
            'median_pen_low': round(median_pen_low, 2) if not np.isnan(median_pen_low) else None,
            'reliability': reliability
        })

    prob_map = pd.DataFrame(results)
    prob_map = prob_map.sort_values('n', ascending=False)

    print(f"\nTotal variants: {len(prob_map)}")
    print(f"\nReliability distribution:")
    print(prob_map['reliability'].value_counts())

    print(f"\nTop 10 variants by sample size:")
    print(prob_map[['variant', 'n', 'first_high_pct', 'reliability']].head(10))

    return prob_map

# ============================================================================
# STEP 6: EXPORT RESULTS
# ============================================================================

def export_results(prob_map, daily_data, csv_file='ny_probability_map.csv',
                  json_file='ny_probability_map.json'):
    """Export probability map to CSV and JSON."""
    print("\n" + "="*80)
    print("EXPORTING RESULTS")
    print("="*80)

    # Export CSV
    prob_map.to_csv(csv_file, index=False)
    print(f"\n✓ Exported CSV: {csv_file}")
    print(f"  Rows: {len(prob_map)}")

    # Export JSON
    prob_map_json = prob_map.to_dict(orient='records')
    with open(json_file, 'w') as f:
        json.dump(prob_map_json, f, indent=2)
    print(f"✓ Exported JSON: {json_file}")

    # Also save daily data for validation
    daily_data_file = 'daily_sessions_with_labels.csv'
    daily_data.drop(columns=['ny_data'], inplace=True)
    daily_data.to_csv(daily_data_file, index=False)
    print(f"✓ Exported daily data: {daily_data_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main analysis workflow."""
    print("\n" + "="*80)
    print("108-VARIANT NY PROBABILITY MAP ANALYSIS")
    print("CORRECTED: London Session = 00:00-05:00 (Gapless!)")
    print("="*80)

    # Step 1: Load data
    df = load_clean_data()

    # Step 2: Calculate session boundaries (CORRECTED)
    sessions_df = calculate_daily_sessions(df)

    # Step 3: Calculate 4-factor context
    sessions_df = calculate_asia_range_regime(sessions_df)
    sessions_df = calculate_london_sweep(sessions_df)
    sessions_df = calculate_open_vs_london_mid(
        sessions_df, 'transition_open', 'transition_vs_london_mid'
    )
    sessions_df = calculate_open_vs_london_mid(
        sessions_df, 'ny_open', 'ny_open_vs_london_mid'
    )
    sessions_df = create_variant_fingerprint(sessions_df)

    # Step 4: Calculate labels (CORRECTED - using London 00:00-05:00)
    sessions_df = calculate_labels(sessions_df)

    # Step 5: Aggregate probabilities
    prob_map = aggregate_probabilities(sessions_df)

    # Step 6: Export results
    export_results(prob_map, sessions_df)

    print("\n" + "="*80)
    print("✓ ANALYSIS COMPLETE (CORRECTED LOGIC)")
    print("="*80)
    print("\nKey Correction:")
    print("  London Session: 00:00-05:00 (was 02:00-05:00)")
    print("  This eliminates the time gap and creates continuous sessions!")
    print("\nNext steps:")
    print("1. Run validation_analysis.py to check probability drift across eras")
    print("2. Run generate_pinescript.py to create TradingView indicator")

if __name__ == '__main__':
    main()
