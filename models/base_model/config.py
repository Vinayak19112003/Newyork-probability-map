"""
Base Model Configuration

Continuous Gapless Sessions Model
Asia 16-02, London 02-08, NY 08-16
"""

from datetime import time

# ============================================================================
# SESSION CONFIGURATION
# ============================================================================

SESSION_TIMES = {
    'asia_start': time(16, 0),      # 16:00 (previous day)
    'asia_end': time(2, 0),         # 02:00
    'london_start': time(2, 0),     # 02:00 (continuous)
    'london_end': time(8, 0),       # 08:00
    'ny_start': time(8, 0),         # 08:00
    'ny_end': time(16, 0),          # 16:00
}

SESSION_NAMES = {
    'asia': 'Asia (16:00-02:00)',
    'london': 'London (02:00-08:00)',
    'ny': 'NY (08:00-16:00)'
}

# ============================================================================
# ANALYSIS PARAMETERS
# ============================================================================

# Asia regime classification
ASIA_RANGE_WINDOW = 200  # Rolling window for quantile calculation
QUANTILE_LOWER = 0.33    # Compressed threshold
QUANTILE_UPPER = 0.66    # Expanded threshold

# London mid tolerance band
LONDON_MID_TOLERANCE = 0.25  # 25% of London range

# Penetration tracking
PENETRATION_WINDOW = 30  # Minutes to track after first sweep

# ============================================================================
# VARIANT CONFIGURATION
# ============================================================================

FACTOR_COUNT = 3  # Effective factors (transition_open = ny_open)

FACTORS = {
    'asia_regime': {
        'values': ['Compressed', 'Normal', 'Expanded'],
        'description': 'Asia range relative to 200-day rolling quantiles'
    },
    'london_sweep': {
        'values': ['None', 'High', 'Low', 'Both'],
        'description': 'London sweep pattern vs Asia range'
    },
    'ny_vs_london': {
        'values': ['Above', 'Below', 'Within'],
        'description': 'NY open position vs London mid (±25% tolerance)'
    }
}

EXPECTED_VARIANTS = 3 * 4 * 3  # 36 variants

# ============================================================================
# RELIABILITY THRESHOLDS
# ============================================================================

RELIABILITY_THRESHOLDS = {
    'high': 150,    # n >= 150
    'medium': 50,   # 50 <= n < 150
    'low': 0        # n < 50
}

# ============================================================================
# VALIDATION CONFIGURATION
# ============================================================================

# Era definitions for stability analysis
ERAS = {
    'Era 1 (2016-2018)': ('2016-01-01', '2018-12-31'),
    'Era 2 (2019-2021)': ('2019-01-01', '2021-12-31'),
    'Era 3 (2022-2025)': ('2022-01-01', '2025-12-31')
}

# Drift threshold for stability classification
DRIFT_THRESHOLD = 15.0  # Flag variants with >15% drift

# ============================================================================
# PINESCRIPT CONFIGURATION
# ============================================================================

# Number of top variants to include in indicator
TOP_VARIANTS_COUNT = 25

# Table configuration
TABLE_ROWS = 17
TABLE_POSITION = 'position.top_right'

# Session colors (TradingView format)
SESSION_COLORS = {
    'asia': 'color.new(color.blue, 95)',
    'london': 'color.new(color.orange, 95)',
    'ny': 'color.new(color.green, 95)'
}

# ============================================================================
# OUTPUT CONFIGURATION
# ============================================================================

OUTPUT_DIR = 'output'

OUTPUT_FILES = {
    'probability_map_csv': 'ny_probability_map.csv',
    'probability_map_json': 'ny_probability_map.json',
    'daily_sessions': 'daily_sessions_with_labels.csv',
    'drift_report': 'validation_drift_report.csv',
    'era_comparison': 'era_comparison_table.csv',
    'pinescript': 'NY_Probability_Map.pine'
}

# ============================================================================
# MODEL METADATA
# ============================================================================

MODEL_INFO = {
    'name': 'Base Model - Continuous Gapless Sessions',
    'version': '1.0',
    'description': 'Asia 16-02, London 02-08, NY 08-16 with 3-factor classification',
    'created': '2025-11-18',
    'status': 'Production-Ready'
}
