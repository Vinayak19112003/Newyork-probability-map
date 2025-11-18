#!/usr/bin/env python3
"""
Multi-Model Comparison Tool

Compares performance metrics across different NY Probability Map model variations.
"""

import pandas as pd
import json
import os
from pathlib import Path
import numpy as np

# Model directories to compare
MODEL_DIRS = [
    'base_model',
    'extended_ny',
    'four_factor',
    'alt_sessions',
    'regime_windows'
]

def load_model_results(model_dir):
    """Load analysis results for a single model."""
    output_dir = Path(model_dir) / 'output'

    if not output_dir.exists():
        return None

    results = {
        'name': model_dir,
        'path': str(output_dir)
    }

    # Load probability map
    prob_map_file = output_dir / 'ny_probability_map.csv'
    if prob_map_file.exists():
        prob_df = pd.read_csv(prob_map_file)
        results['prob_map'] = prob_df
        results['variant_count'] = len(prob_df)
        results['total_samples'] = prob_df['n'].sum()
        results['mean_sample_size'] = prob_df['n'].mean()
        results['median_sample_size'] = prob_df['n'].median()
        results['min_sample_size'] = prob_df['n'].min()
        results['max_sample_size'] = prob_df['n'].max()

        # Reliability distribution
        results['high_reliability'] = len(prob_df[prob_df['n'] >= 150])
        results['medium_reliability'] = len(prob_df[(prob_df['n'] >= 50) & (prob_df['n'] < 150)])
        results['low_reliability'] = len(prob_df[prob_df['n'] < 50])

        # Probability metrics
        results['mean_p_high'] = prob_df['first_high_pct'].mean()
        results['directional_edge'] = (prob_df['first_high_pct'] - 50).abs().mean()
        results['max_edge'] = (prob_df['first_high_pct'] - 50).abs().max()
        results['mean_fail_rate'] = prob_df['fail_pct'].mean()
        results['median_pen_high'] = prob_df['median_pen_high'].median()
        results['median_pen_low'] = prob_df['median_pen_low'].median()

        # Top variant
        top_variant = prob_df.loc[prob_df['n'].idxmax()]
        results['top_variant_name'] = top_variant['variant']
        results['top_variant_n'] = top_variant['n']
        results['top_variant_p_high'] = top_variant['first_high_pct']

        # Strong edge variants (>70% or <30%)
        results['strong_variants'] = len(prob_df[
            (prob_df['first_high_pct'] > 70) | (prob_df['first_high_pct'] < 30)
        ])

    # Load validation/drift report
    drift_file = output_dir / 'validation_drift_report.csv'
    if drift_file.exists():
        drift_df = pd.read_csv(drift_file)
        results['drift_report'] = drift_df
        results['mean_drift_high'] = drift_df['drift_first_high'].mean()
        results['median_drift_high'] = drift_df['drift_first_high'].median()
        results['max_drift_high'] = drift_df['drift_first_high'].max()
        results['stable_variants'] = len(drift_df[~drift_df['is_unstable']])
        results['unstable_variants'] = len(drift_df[drift_df['is_unstable']])
        results['stability_rate'] = results['stable_variants'] / len(drift_df) * 100 if len(drift_df) > 0 else 0

    # Load daily data
    daily_file = output_dir / 'daily_sessions_with_labels.csv'
    if daily_file.exists():
        daily_df = pd.read_csv(daily_file)
        results['total_days'] = len(daily_df)
        results['coverage_rate'] = (results['total_samples'] / results['total_days'] * 100) if 'total_samples' in results else 0

    return results

def generate_comparison_table(models):
    """Generate comparison table across all models."""
    print("\n" + "="*100)
    print("NY PROBABILITY MAP - MODEL COMPARISON")
    print("="*100)

    if not models:
        print("\nNo models found with output data.")
        return

    # Create comparison DataFrame
    comparison_data = []
    for model in models:
        comparison_data.append({
            'Model': model['name'],
            'Variants': model.get('variant_count', 'N/A'),
            'Total Days': model.get('total_days', 'N/A'),
            'Avg Samples': f"{model.get('mean_sample_size', 0):.1f}",
            'High Rel': model.get('high_reliability', 0),
            'Med Rel': model.get('medium_reliability', 0),
            'Low Rel': model.get('low_reliability', 0),
            'Dir Edge': f"{model.get('directional_edge', 0):.2f}%",
            'Max Edge': f"{model.get('max_edge', 0):.2f}%",
            'Fail Rate': f"{model.get('mean_fail_rate', 0):.1f}%",
            'Stability': f"{model.get('stability_rate', 0):.1f}%",
            'Mean Drift': f"{model.get('mean_drift_high', 0):.2f}%",
            'Strong Vars': model.get('strong_variants', 0)
        })

    comp_df = pd.DataFrame(comparison_data)

    print("\n" + "="*100)
    print("SUMMARY METRICS")
    print("="*100)
    print(comp_df.to_string(index=False))

    # Detailed per-model analysis
    print("\n" + "="*100)
    print("DETAILED MODEL ANALYSIS")
    print("="*100)

    for model in models:
        print(f"\n{'-'*100}")
        print(f"MODEL: {model['name'].upper()}")
        print(f"{'-'*100}")

        print(f"\n📊 Variant Statistics:")
        print(f"  Total Variants: {model.get('variant_count', 'N/A')}")
        print(f"  Sample Size: {model.get('min_sample_size', 'N/A')} - {model.get('max_sample_size', 'N/A')} (median: {model.get('median_sample_size', 'N/A')})")
        print(f"  High Reliability (n≥150): {model.get('high_reliability', 0)}")
        print(f"  Medium Reliability (50≤n<150): {model.get('medium_reliability', 0)}")
        print(f"  Low Reliability (n<50): {model.get('low_reliability', 0)}")

        print(f"\n📈 Probability Performance:")
        print(f"  Mean P(High First): {model.get('mean_p_high', 0):.2f}%")
        print(f"  Directional Edge: {model.get('directional_edge', 0):.2f}%")
        print(f"  Maximum Edge: {model.get('max_edge', 0):.2f}%")
        print(f"  Strong Edge Variants: {model.get('strong_variants', 0)}")
        print(f"  Mean Fail Rate: {model.get('mean_fail_rate', 0):.2f}%")

        print(f"\n🎯 Top Variant:")
        print(f"  Name: {model.get('top_variant_name', 'N/A')}")
        print(f"  Samples: {model.get('top_variant_n', 'N/A')}")
        print(f"  P(High First): {model.get('top_variant_p_high', 0):.2f}%")

        print(f"\n⚖️ Stability Metrics:")
        print(f"  Stability Rate: {model.get('stability_rate', 0):.1f}%")
        print(f"  Mean Drift: {model.get('mean_drift_high', 0):.2f}%")
        print(f"  Median Drift: {model.get('median_drift_high', 0):.2f}%")
        print(f"  Max Drift: {model.get('max_drift_high', 0):.2f}%")
        print(f"  Stable Variants: {model.get('stable_variants', 0)}")
        print(f"  Unstable Variants: {model.get('unstable_variants', 0)}")

        print(f"\n📅 Data Coverage:")
        print(f"  Total Trading Days: {model.get('total_days', 'N/A')}")
        print(f"  Coverage Rate: {model.get('coverage_rate', 0):.1f}%")

def generate_rankings(models):
    """Generate rankings for each metric."""
    print("\n" + "="*100)
    print("MODEL RANKINGS")
    print("="*100)

    # Create rankings
    rankings = {}

    for metric, label, reverse in [
        ('directional_edge', 'Best Directional Edge', True),
        ('stability_rate', 'Best Stability', True),
        ('strong_variants', 'Most Strong Variants', True),
        ('mean_fail_rate', 'Lowest Fail Rate', False),
        ('mean_drift_high', 'Lowest Drift', False),
        ('variant_count', 'Most Variants', True),
        ('mean_sample_size', 'Best Sample Size', True),
    ]:
        sorted_models = sorted(
            [m for m in models if metric in m],
            key=lambda x: x.get(metric, 0),
            reverse=reverse
        )

        print(f"\n🏆 {label}:")
        for i, model in enumerate(sorted_models[:3], 1):
            print(f"  {i}. {model['name']}: {model.get(metric, 'N/A')}")

def export_comparison_report(models, output_file='model_comparison_report.csv'):
    """Export comparison to CSV."""
    comparison_data = []

    for model in models:
        comparison_data.append({
            'model': model['name'],
            'variant_count': model.get('variant_count', None),
            'total_days': model.get('total_days', None),
            'mean_sample_size': model.get('mean_sample_size', None),
            'median_sample_size': model.get('median_sample_size', None),
            'high_reliability': model.get('high_reliability', None),
            'medium_reliability': model.get('medium_reliability', None),
            'low_reliability': model.get('low_reliability', None),
            'directional_edge': model.get('directional_edge', None),
            'max_edge': model.get('max_edge', None),
            'mean_fail_rate': model.get('mean_fail_rate', None),
            'stability_rate': model.get('stability_rate', None),
            'mean_drift': model.get('mean_drift_high', None),
            'median_drift': model.get('median_drift_high', None),
            'strong_variants': model.get('strong_variants', None),
            'top_variant': model.get('top_variant_name', None),
            'top_variant_n': model.get('top_variant_n', None),
            'top_variant_p_high': model.get('top_variant_p_high', None)
        })

    df = pd.DataFrame(comparison_data)
    df.to_csv(output_file, index=False)
    print(f"\n✓ Comparison report exported: {output_file}")

def main():
    """Main comparison workflow."""
    print("\n" + "="*100)
    print("LOADING MODEL RESULTS")
    print("="*100)

    models = []
    for model_dir in MODEL_DIRS:
        print(f"\nLoading {model_dir}...", end=' ')
        results = load_model_results(model_dir)
        if results:
            models.append(results)
            print("✓")
        else:
            print("⚠ No output data found")

    if not models:
        print("\n⚠ No models with output data found.")
        print("\nRun analysis scripts in each model directory first:")
        print("  cd models/base_model && python3 run_analysis.py")
        return

    # Generate comparison
    generate_comparison_table(models)
    generate_rankings(models)
    export_comparison_report(models)

    print("\n" + "="*100)
    print("✓ COMPARISON COMPLETE")
    print("="*100)

    # Recommendation
    print("\n💡 RECOMMENDATIONS:")
    print("\n1. Best Overall Balance: Model with highest (stability_rate × directional_edge)")
    print("2. Best Edge: Model with highest directional_edge and strong_variants")
    print("3. Most Stable: Model with highest stability_rate and lowest mean_drift")
    print("4. Best Coverage: Model with most variants and best sample distribution")

if __name__ == '__main__':
    main()
