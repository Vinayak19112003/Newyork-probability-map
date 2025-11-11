# NY Probability Map - 108-Variant Context Engine

A comprehensive quantitative analysis framework for NQ futures trading, featuring a dynamic 4-factor model that generates 108 unique market context variants with associated probabilities.

## 📊 Overview

This project analyzes 9+ years of 1-minute NQ data (2016-2025) to create a probability map for the New York trading session (08:30-11:00 ET). The model identifies which London session level (High or Low) is most likely to be swept first during the NY session, based on four contextual factors.

## 🎯 Key Features

- **108 Unique Variants**: Comprehensive context engine based on 4 dynamic factors
- **9+ Years of Data**: Analysis of 2,193 trading days from 2016-2025
- **Dynamic Asia Range Regime**: Rolling 200-day quantile-based classification
- **TradingView Integration**: Ready-to-use PineScript v5 indicator
- **Validation Analysis**: Era-based stability testing to identify drift
- **Real-time Context Detection**: Live variant matching and probability display

## 📈 The 4-Factor Model

### Factor 1: Asia Range Regime (3 variants)
- **Compressed**: Asia range < 33rd percentile (200-day rolling)
- **Normal**: Asia range between 33rd and 66th percentile
- **Expanded**: Asia range > 66th percentile

### Factor 2: London Sweep Pattern (4 variants)
- **None**: London stays within Asia range
- **High**: London sweeps Asia High only
- **Low**: London sweeps Asia Low only
- **Both**: London sweeps both Asia High and Low

### Factor 3: Transition Open vs London Mid (3 variants)
- **Above**: Transition open (05:00) > London Mid + (0.25 × London Range)
- **Below**: Transition open < London Mid - (0.25 × London Range)
- **Within**: Transition open within the ±25% band

### Factor 4: NY Open vs London Mid (3 variants)
- **Above**: NY open (08:30) > London Mid + (0.25 × London Range)
- **Below**: NY open < London Mid - (0.25 × London Range)
- **Within**: NY open within the ±25% band

**Total Variants**: 3 × 4 × 3 × 3 = 108

## 📊 Analysis Results

### Dataset Statistics
- **Total 1-minute bars**: 3,025,725
- **Trading days analyzed**: 2,193
- **Unique variants found**: 105 (out of 108 possible)
- **Date range**: January 2017 - September 2025

### Overall Probabilities
- **First Sweep High**: 51.7% (1,134 days)
- **First Sweep Low**: 48.3% (1,059 days)
- **Fail Rate**: 38.08% (opposite level also hit)
- **Median Penetration**: 14.37 points

### Reliability Distribution
- **High Reliability** (≥150 samples): 0 variants
- **Medium Reliability** (50-150 samples): 10 variants
- **Low Reliability** (<50 samples): 95 variants

### Top Performing Variants

| Variant | n | P(High First) | P(Fail) | Reliability |
|---------|---|---------------|---------|-------------|
| Expanded\|High\|Above\|Above | 85 | 92.94% | 34.12% | Medium |
| Normal\|High\|Above\|Above | 66 | 92.42% | 31.82% | Medium |
| Expanded\|High\|Within\|Above | 63 | 95.24% | 36.51% | Medium |

## 🔬 Validation Analysis

### Era-Based Stability Testing

Data split into three eras:
- **Era 1 (2016-2018)**: 482 days
- **Era 2 (2019-2021)**: 752 days
- **Era 3 (2022-2025)**: 957 days

### Stability Results
- **Variants analyzed**: 15 (with sufficient data across eras)
- **Unstable variants** (>15% drift): 9
- **Stable variants**: 6
- **Mean drift in P(High First)**: 8.79%
- **Max drift observed**: 28.98%

### Most Stable Variants
1. **Expanded|Low|Within|Above**: 1.2% drift
2. **Expanded|None|Within|Above**: 1.4% drift
3. **Expanded|High|Within|Below**: 2.3% drift

## 🛠️ Installation & Usage

### Prerequisites

```bash
pip install pandas numpy pytz matplotlib seaborn
```

### Step 1: Data Processing

```bash
# Merge and clean 1-minute data
python3 download_and_merge.py

# This will:
# - Load all CSV files
# - Convert UTC+3 → America/New_York
# - Filter trading hours
# - Export: nq_1m_et.csv
```

### Step 2: Run Analysis

```bash
# Calculate 108-variant probability map
python3 run_analysis.py

# Outputs:
# - ny_probability_map.csv
# - ny_probability_map.json
# - daily_sessions_with_labels.csv
```

### Step 3: Validation

```bash
# Check for probability drift across eras
python3 validation_analysis.py

# Outputs:
# - validation_drift_report.csv
# - era_comparison_table.csv
```

### Step 4: Generate TradingView Indicator

```bash
# Create PineScript v5 indicator
python3 generate_pinescript.py

# Output:
# - NY_Probability_Map.pine (ready to paste into TradingView)
```

## 📺 TradingView Setup

1. Open [TradingView](https://tradingview.com)
2. Click **Pine Editor** at the bottom
3. Copy contents of `NY_Probability_Map.pine`
4. Paste into Pine Editor
5. Click **Add to Chart**

### Indicator Features

- **Session Boxes**: Visual overlays for Asia, London, and NY sessions
- **London Levels**: Horizontal lines showing target High/Low
- **Probability Table**: Live display showing:
  - Current variant fingerprint
  - P(High First) and P(Low First)
  - P(Fail) - probability opposite level also gets hit
  - Median penetration (in points)
  - Sample size and reliability rating
  - Current London High/Low values

### Customization Options

- Toggle session box visibility
- Adjust colors for each session
- Show/hide London levels
- Show/hide probability table
- Adjust Asia Range rolling window (default: 200)

## 📁 Project Structure

```
Newyork-probability-map/
├── 1m_data_part1.csv          # Raw 1-minute data (7 parts)
├── ...
├── 1m_data_part7.csv
├── requirements.txt            # Python dependencies
├── download_and_merge.py       # Step 1: Data ingestion & cleaning
├── run_analysis.py             # Step 2: 108-variant analysis
├── validation_analysis.py      # Step 3: Era-based stability testing
├── generate_pinescript.py      # Step 4: TradingView indicator generator
├── nq_1m_et.csv               # Cleaned 1-minute data (178 MB)
├── ny_probability_map.csv     # Probability map (105 variants)
├── ny_probability_map.json    # JSON format for PineScript
├── daily_sessions_with_labels.csv  # Daily session data with outcomes
├── validation_drift_report.csv     # Drift analysis results
├── era_comparison_table.csv        # Era comparison table
├── NY_Probability_Map.pine    # TradingView indicator (ready to use)
└── README.md                  # This file
```

## 📊 Output Files

### ny_probability_map.csv
Contains probability statistics for each variant:
- `variant`: Full variant string (e.g., "Expanded|High|Above|Above")
- `n`: Sample size
- `first_high_pct`: P(London High swept first)
- `first_low_pct`: P(London Low swept first)
- `sweep_both_pct`: P(both levels hit during NY session)
- `fail_pct`: P(opposite level also hit after first sweep)
- `median_pen_high/low`: Median overshoot in points
- `reliability`: High/Medium/Low based on sample size

### validation_drift_report.csv
Shows probability drift between Era 1 and Era 3:
- `drift_first_high`: Absolute change in P(High First)
- `drift_fail`: Absolute change in P(Fail)
- `is_unstable`: Flag for >15% drift
- Comparison of n, probabilities across eras

### NY_Probability_Map.pine
Complete TradingView indicator with:
- Embedded probability map data (105 variants)
- Real-time context detection
- Dynamic Asia Range regime calculation
- Session visualization
- Probability table display

## 🧮 Methodology

### Session Definitions (America/New_York)
- **Asia Session**: 20:00 (prev day) - 00:00
- **London Session**: 02:00 - 05:00
- **Transition**: 05:00 - 08:30
- **NY Session (Label Window)**: 08:30 - 11:00

### Label Calculation
For each trading day during the NY window (08:30-11:00):
- **first_sweep_side**: Which London level (High/Low) was hit first
- **fail_flag**: Did opposite level also get hit? (1/0)
- **both_flag**: Were both levels hit during the window? (1/0)
- **median_penetration**: Median overshoot measured over 30 minutes after first sweep

### Dynamic Asia Range Classification
Unlike static point-based systems, this model uses a **rolling 200-day quantile** approach:
1. Calculate Asia Range for each day
2. For each day, compute 33rd and 66th percentile of the previous 200 days
3. Classify current day's range relative to these dynamic thresholds
4. This adapts to changing market volatility over time

## 📉 Key Findings

### Directional Edge
- Most variants show **strong directional bias** (>80% probability)
- "Above|Above" patterns strongly favor High sweeps (92-96%)
- "Below|Below" patterns strongly favor Low sweeps (90-98%)

### Failure Patterns
- Fail rate varies widely (20-65%) depending on variant
- Higher fail rates in "Within|Within" patterns (more balanced)
- Lower fail rates in extreme positioning variants

### Penetration
- Median penetration ranges from 5-25 points
- High sweeps average 12-19 points overshoot
- Low sweeps average 13-24 points overshoot

### Reliability Concerns
- Only 10 variants have medium reliability (50-150 samples)
- 95 variants have low reliability (<50 samples)
- Consider focusing on top 10-20 most reliable variants for trading

## ⚠️ Important Considerations

### Statistical Limitations
1. **Sample Size**: Most variants have <50 occurrences over 9 years
2. **Drift**: 60% of analyzed variants show >15% drift across eras
3. **Market Evolution**: Probabilities may change as market structure evolves
4. **Overfitting Risk**: 108 variants on 2,193 days = ~21 samples per variant on average

### Usage Recommendations
1. **Focus on High-Reliability Variants**: Use only the top 10-20 variants by sample size
2. **Monitor Drift**: Re-run analysis periodically to check for probability changes
3. **Combine with Other Factors**: Don't use probabilities in isolation
4. **Risk Management**: Always use proper position sizing and stop losses
5. **Forward Testing**: Validate any trading strategy on out-of-sample data

## 🔄 Updating the Analysis

To update with new data:

1. Add new 1-minute data to CSV files
2. Re-run all scripts in sequence:
   ```bash
   python3 download_and_merge.py
   python3 run_analysis.py
   python3 validation_analysis.py
   python3 generate_pinescript.py
   ```
3. Update the TradingView indicator with new PineScript

## 📝 License

This project is provided as-is for educational and research purposes.

## 🙏 Acknowledgments

- Data timeframe: 2016-2025 (9+ years)
- Instrument: NQ Futures (1-minute bars)
- Timezone: America/New_York (Eastern Time)

## 📧 Contact

For questions or issues, please open an issue on GitHub.

---

**Disclaimer**: This analysis is for educational purposes only. Past performance does not guarantee future results. Trading futures involves substantial risk of loss and is not suitable for all investors.
