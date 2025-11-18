# NY Probability Map - Multi-Model Framework

This directory contains different variations of the NY Probability Map model for comparison and experimentation.

## Model Architecture Overview

All models follow the same basic workflow:
1. **Data Ingestion**: 9+ years of NQ 1-minute data
2. **Session Analysis**: Define trading sessions (Asia, London, NY)
3. **Context Classification**: Calculate variant fingerprints based on multiple factors
4. **Outcome Labeling**: Track which target level is hit first during NY session
5. **Probability Aggregation**: Calculate directional probabilities for each variant
6. **Validation**: Check probability stability across time eras
7. **PineScript Generation**: Create TradingView indicator

## Model Variations

### 1. **base_model/** (Current Implementation)
**Session Times:**
- Asia: 16:00 - 02:00 (10 hours)
- London: 02:00 - 08:00 (6 hours)
- NY: 08:00 - 16:00 (8 hours)

**Factors:**
- Asia Range Regime (Compressed/Normal/Expanded) - 200-day rolling window
- London Sweep vs Asia (None/High/Low/Both)
- NY Open vs London Mid (Above/Below/Within 25% tolerance)

**Note:** Effectively 3-factor model since transition_open = ny_open at 08:00

**Results:**
- 36 unique variants
- 2,196 trading days
- Top variant: Expanded|High|Within|Within (182 samples, 53.85% P(High))

---

### 2. **extended_ny/** (NY Session Variations)
Test different NY session windows to find optimal predictive period:

**Variations:**
- **Short NY**: 08:00 - 11:00 (3 hours - morning session only)
- **Medium NY**: 08:00 - 12:00 (4 hours - through lunch)
- **Full Day**: 08:00 - 16:00 (8 hours - current)
- **Extended**: 08:00 - 17:00 (9 hours - includes settlement)

**Goal:** Determine which NY window provides most reliable probability signals

---

### 3. **four_factor/** (True 4-Factor Model)
Separate London and NY sessions with explicit gap/transition:

**Session Times:**
- Asia: 16:00 - 02:00
- London: 02:00 - 08:00
- **Transition Gap**: 08:00 - 08:30 (30 minutes)
- NY: 08:30 - 16:00

**Factors (4 distinct):**
1. Asia Range Regime
2. London Sweep vs Asia
3. **08:00 Open** vs London Mid
4. **08:30 Open** vs London Mid

**Expected:** ~108 unique variants (3×4×3×3)

---

### 4. **alt_sessions/** (Alternative Session Boundaries)
Test different session timing configurations:

**Variation A - Traditional:**
- Asia: 20:00 - 00:00 (4 hours)
- London: 00:00 - 08:00 (8 hours - full European)
- NY: 08:00 - 16:00 (8 hours)

**Variation B - Market Hours:**
- Asia: 18:00 - 03:00 (9 hours - Tokyo + Hong Kong)
- London: 03:00 - 08:00 (5 hours - core European)
- NY: 08:00 - 15:00 (7 hours - regular NYSE hours)

**Variation C - Overlaps:**
- Asia: 16:00 - 02:00 (10 hours)
- London: 02:00 - 09:30 (7.5 hours - through US open)
- NY: 09:30 - 16:00 (6.5 hours - US regular hours)

**Goal:** Find session boundaries that maximize variant differentiation

---

### 5. **regime_windows/** (Asia Regime Window Variations)
Test different rolling window sizes for Asia range classification:

**Variations:**
- **Short-term**: 100-day rolling window (faster regime changes)
- **Current**: 200-day rolling window (baseline)
- **Long-term**: 300-day rolling window (slower regime changes)
- **Annual**: 252-day rolling window (1 trading year)

**Goal:** Determine optimal lookback period for regime classification

---

## Performance Comparison Framework

Each model generates the following metrics for comparison:

### Model Quality Metrics:
1. **Variant Count**: Number of unique variants found
2. **Sample Distribution**: Samples per variant (min/max/median)
3. **Reliability Score**: Percentage of variants with >50 samples
4. **Coverage**: Percentage of trading days matching a variant

### Probability Metrics:
5. **Directional Edge**: Average |P(High) - 50%| across all variants
6. **Top Variant Performance**: Best performing variant's win rate
7. **Stability Score**: Mean probability drift across eras (lower is better)
8. **Fail Rate**: Average fail rate across variants

### Statistical Validation:
9. **Era Stability**: Number of stable variants (<15% drift)
10. **Temporal Consistency**: Correlation of probabilities across eras
11. **Sample Adequacy**: Percentage of variants with n ≥ 30

## Running Model Comparisons

### Step 1: Generate Results for Each Model
```bash
# Base model
cd models/base_model
python3 run_analysis.py
python3 validation_analysis.py

# Extended NY variations
cd ../extended_ny
python3 run_analysis_short.py
python3 run_analysis_medium.py
python3 run_analysis_full.py

# Continue for all models...
```

### Step 2: Compare Results
```bash
cd models
python3 compare_models.py  # Generates comparison report
```

### Step 3: Select Best Model
Review comparison metrics and select optimal configuration for live trading.

## Model Selection Criteria

**Priority Order:**
1. **Stability First**: Lowest probability drift across eras
2. **Edge Magnitude**: Highest directional edge in top variants
3. **Sample Size**: Adequate samples for statistical significance
4. **Simplicity**: Fewer variants = easier to interpret and trade

## File Structure

Each model directory contains:
```
model_name/
├── run_analysis.py              # Main analysis script
├── generate_pinescript.py       # PineScript generator
├── validation_analysis.py       # Era-based stability check
├── config.py                    # Model-specific configuration
├── output/
│   ├── ny_probability_map.csv   # Probability results
│   ├── ny_probability_map.json
│   ├── daily_sessions_with_labels.csv
│   ├── validation_drift_report.csv
│   └── NY_Probability_Map.pine  # TradingView indicator
└── README.md                    # Model-specific documentation
```

## Next Steps

1. **Implement Extended NY Variations** - Test different NY session windows
2. **Build 4-Factor Model** - Add explicit transition period
3. **Test Alternative Sessions** - Experiment with different time boundaries
4. **Regime Window Analysis** - Compare different lookback periods
5. **Create Comparison Tool** - Automated model performance comparison
6. **Forward Testing** - Paper trade best models in parallel
7. **Ensemble Methods** - Combine signals from multiple models

## Development Workflow

1. Create new model in separate directory
2. Modify session times or factor calculations
3. Run full analysis pipeline
4. Compare results to base_model
5. Document findings in model README
6. If superior, update base_model or create new "best_model"

---

**Last Updated**: 2025-11-18
**Base Model Version**: 1.0 (Asia 16-02, London 02-08, NY 08-16)
