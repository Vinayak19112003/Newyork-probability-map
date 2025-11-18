#!/usr/bin/env python3
"""
Validation and Stability Analysis

Splits data into three eras and checks for probability drift across time periods.
"""

import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

# Define eras
ERAS = {
    'Era 1 (2016-2018)': ('2016-01-01', '2018-12-31'),
    'Era 2 (2019-2021)': ('2019-01-01', '2021-12-31'),
    'Era 3 (2022-2025)': ('2022-01-01', '2025-12-31')
}

DRIFT_THRESHOLD = 15.0  # Flag variants with >15% drift in key probabilities

def load_daily_data(filepath='daily_sessions_with_labels.csv'):
    """Load the daily sessions data with labels."""
    print("="*80)
    print("LOADING DAILY DATA")
    print("="*80)

    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'], utc=True).dt.tz_localize(None)  # Remove timezone
    print(f"\nLoaded {len(df):,} trading days")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    return df

def split_data_by_era(df):
    """Split data into three eras."""
    print("\n" + "="*80)
    print("SPLITTING DATA BY ERA")
    print("="*80)

    era_data = {}

    for era_name, (start_date, end_date) in ERAS.items():
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        era_df = df[
            (df['date'] >= start_dt) &
            (df['date'] <= end_dt)
        ].copy()

        era_data[era_name] = era_df
        print(f"\n{era_name}: {len(era_df):,} days")

    return era_data

def calculate_era_probabilities(df):
    """Calculate probability statistics for a single era."""
    results = []

    for variant in df['variant'].unique():
        variant_data = df[df['variant'] == variant]
        n = len(variant_data)

        if n < 10:  # Skip variants with very few samples
            continue

        # Calculate probabilities
        first_high_count = (variant_data['first_sweep_side'] == 'High').sum()
        first_high_pct = (first_high_count / n * 100) if n > 0 else 0

        sweep_both_pct = variant_data['both_flag'].mean() * 100
        fail_pct = variant_data['fail_flag'].mean() * 100

        results.append({
            'variant': variant,
            'n': n,
            'first_high_pct': round(first_high_pct, 2),
            'sweep_both_pct': round(sweep_both_pct, 2),
            'fail_pct': round(fail_pct, 2)
        })

    return pd.DataFrame(results)

def analyze_all_eras(era_data):
    """Analyze probabilities for each era."""
    print("\n" + "="*80)
    print("ANALYZING PROBABILITIES BY ERA")
    print("="*80)

    era_results = {}

    for era_name, era_df in era_data.items():
        print(f"\n{era_name}...")
        era_probs = calculate_era_probabilities(era_df)
        era_results[era_name] = era_probs
        print(f"  Variants analyzed: {len(era_probs)}")

    return era_results

def calculate_drift(era_results):
    """Calculate drift between Era 1 and Era 3 for each variant."""
    print("\n" + "="*80)
    print("CALCULATING PROBABILITY DRIFT")
    print("="*80)

    era_names = list(ERAS.keys())
    era1_df = era_results[era_names[0]]
    era3_df = era_results[era_names[2]]

    # Merge Era 1 and Era 3 data
    drift_df = era1_df.merge(
        era3_df,
        on='variant',
        how='outer',
        suffixes=('_era1', '_era3')
    )

    # Calculate drift
    drift_df['drift_first_high'] = (
        drift_df['first_high_pct_era3'] - drift_df['first_high_pct_era1']
    ).abs()

    drift_df['drift_fail'] = (
        drift_df['fail_pct_era3'] - drift_df['fail_pct_era1']
    ).abs()

    # Flag unstable variants
    drift_df['is_unstable'] = (
        (drift_df['drift_first_high'] > DRIFT_THRESHOLD) |
        (drift_df['drift_fail'] > DRIFT_THRESHOLD)
    )

    # Sort by maximum drift
    drift_df['max_drift'] = drift_df[['drift_first_high', 'drift_fail']].max(axis=1)
    drift_df = drift_df.sort_values('max_drift', ascending=False)

    # Filter variants with sufficient data in both eras
    drift_df = drift_df[
        (drift_df['n_era1'].notna()) &
        (drift_df['n_era3'].notna()) &
        (drift_df['n_era1'] >= 10) &
        (drift_df['n_era3'] >= 10)
    ]

    print(f"\nVariants analyzed: {len(drift_df)}")
    print(f"Unstable variants (>{DRIFT_THRESHOLD}% drift): {drift_df['is_unstable'].sum()}")
    print(f"Stable variants: {(~drift_df['is_unstable']).sum()}")

    return drift_df

def generate_drift_report(drift_df, era_results):
    """Generate a comprehensive drift report."""
    print("\n" + "="*80)
    print("DRIFT REPORT")
    print("="*80)

    print("\n" + "-"*80)
    print("TOP 20 MOST UNSTABLE VARIANTS")
    print("-"*80)

    unstable = drift_df.head(20)
    for idx, row in unstable.iterrows():
        print(f"\nVariant: {row['variant']}")
        print(f"  Era 1: n={row['n_era1']:.0f}, P(High First)={row['first_high_pct_era1']:.1f}%, Fail={row['fail_pct_era1']:.1f}%")
        print(f"  Era 3: n={row['n_era3']:.0f}, P(High First)={row['first_high_pct_era3']:.1f}%, Fail={row['fail_pct_era3']:.1f}%")
        print(f"  Drift: ΔP(High)={row['drift_first_high']:.1f}%, ΔFail={row['drift_fail']:.1f}%")
        print(f"  Status: {'⚠ UNSTABLE' if row['is_unstable'] else '✓ Stable'}")

    print("\n" + "-"*80)
    print("TOP 10 MOST STABLE VARIANTS")
    print("-"*80)

    stable = drift_df[~drift_df['is_unstable']].tail(10)
    for idx, row in stable.iterrows():
        print(f"\nVariant: {row['variant']}")
        print(f"  Era 1: n={row['n_era1']:.0f}, P(High First)={row['first_high_pct_era1']:.1f}%")
        print(f"  Era 3: n={row['n_era3']:.0f}, P(High First)={row['first_high_pct_era3']:.1f}%")
        print(f"  Drift: ΔP(High)={row['drift_first_high']:.1f}%")

    # Summary statistics
    print("\n" + "="*80)
    print("STABILITY SUMMARY")
    print("="*80)

    print(f"\nMean drift in P(High First): {drift_df['drift_first_high'].mean():.2f}%")
    print(f"Median drift in P(High First): {drift_df['drift_first_high'].median():.2f}%")
    print(f"Max drift in P(High First): {drift_df['drift_first_high'].max():.2f}%")

    print(f"\nMean drift in Fail Rate: {drift_df['drift_fail'].mean():.2f}%")
    print(f"Median drift in Fail Rate: {drift_df['drift_fail'].median():.2f}%")
    print(f"Max drift in Fail Rate: {drift_df['drift_fail'].max():.2f}%")

    # Save detailed report
    report_file = 'validation_drift_report.csv'
    drift_df.to_csv(report_file, index=False)
    print(f"\n✓ Detailed drift report saved: {report_file}")

def create_era_comparison_table(era_results, top_n=20):
    """Create a comparison table showing probabilities across all three eras."""
    print("\n" + "="*80)
    print(f"ERA COMPARISON TABLE (Top {top_n} Variants)")
    print("="*80)

    era_names = list(ERAS.keys())

    # Get all variants that appear in at least one era
    all_variants = set()
    for era_probs in era_results.values():
        all_variants.update(era_probs['variant'].unique())

    comparison_data = []

    for variant in all_variants:
        row = {'variant': variant}

        # Track total samples across all eras
        total_samples = 0

        for era_name in era_names:
            era_probs = era_results[era_name]
            variant_data = era_probs[era_probs['variant'] == variant]

            if len(variant_data) > 0:
                row[f'{era_name}_n'] = variant_data['n'].iloc[0]
                row[f'{era_name}_high_pct'] = variant_data['first_high_pct'].iloc[0]
                total_samples += variant_data['n'].iloc[0]
            else:
                row[f'{era_name}_n'] = 0
                row[f'{era_name}_high_pct'] = np.nan

        row['total_samples'] = total_samples
        comparison_data.append(row)

    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values('total_samples', ascending=False)

    # Display top variants
    print("\n" + "-"*80)
    for idx, row in comparison_df.head(top_n).iterrows():
        print(f"\nVariant: {row['variant']}")
        for era_name in era_names:
            n = row[f'{era_name}_n']
            p_high = row[f'{era_name}_high_pct']
            if n > 0:
                print(f"  {era_name}: n={n:.0f}, P(High First)={p_high:.1f}%")
            else:
                print(f"  {era_name}: No data")
        print(f"  Total samples: {row['total_samples']:.0f}")

    # Save comparison table
    comparison_file = 'era_comparison_table.csv'
    comparison_df.to_csv(comparison_file, index=False)
    print(f"\n✓ Era comparison table saved: {comparison_file}")

def main():
    """Main validation workflow."""
    print("\n" + "="*80)
    print("VALIDATION & STABILITY ANALYSIS")
    print("="*80)

    # Load data
    df = load_daily_data()

    # Split by era
    era_data = split_data_by_era(df)

    # Analyze each era
    era_results = analyze_all_eras(era_data)

    # Calculate drift
    drift_df = calculate_drift(era_results)

    # Generate reports
    generate_drift_report(drift_df, era_results)
    create_era_comparison_table(era_results)

    print("\n" + "="*80)
    print("✓ VALIDATION COMPLETE")
    print("="*80)

    print("\nKey Findings:")
    print(f"  - {len(drift_df)} variants analyzed across eras")
    print(f"  - {drift_df['is_unstable'].sum()} variants show significant drift (>{DRIFT_THRESHOLD}%)")
    print(f"  - {(~drift_df['is_unstable']).sum()} variants are stable")
    print(f"  - Mean drift: {drift_df['drift_first_high'].mean():.2f}%")

    print("\nNext step: Run generate_pinescript.py to create TradingView indicator")

if __name__ == '__main__':
    main()
