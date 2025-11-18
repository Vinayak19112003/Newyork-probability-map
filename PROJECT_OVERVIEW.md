# NY Probability Map - Quantitative Trading Framework

A comprehensive multi-model framework for analyzing NQ futures trading probabilities based on session-based market structure.

## 🎯 Project Overview

This framework analyzes 9+ years of NQ (Nasdaq 100 E-mini futures) 1-minute data to create probability maps that predict the direction of the first sweep during the NY trading session based on pre-NY market context.

### Core Concept

**Question**: Given the context from Asia and London sessions, what is the probability that the NY session will sweep the London High first vs London Low first?

**Approach**:
1. Classify each trading day based on multiple context factors (Asia range, London sweep pattern, price positioning)
2. Calculate historical probabilities for each unique variant
3. Generate live trading signals via TradingView indicator

## 📊 Project Structure

```
Newyork-probability-map/
├── download_and_merge.py        # Data ingestion (9+ years NQ 1min)
├── nq_1m_et.csv                 # Clean data (3M+ rows, 178 MB)
│
├── models/                       # Multi-model framework
│   ├── README.md                 # Model overview and methodology
│   ├── compare_models.py         # Cross-model comparison tool
│   ├── create_new_model.sh       # Template generator for new models
│   │
│   ├── base_model/               # ✅ Production model (validated)
│   │   ├── config.py             # Model configuration
│   │   ├── run_analysis.py       # Main analysis pipeline
│   │   ├── generate_pinescript.py # TradingView indicator generator
│   │   ├── validation_analysis.py # Era-based stability check
│   │   ├── README.md             # Model documentation
│   │   └── output/               # Generated results
│   │       ├── ny_probability_map.csv       # 36 variants
│   │       ├── ny_probability_map.json
│   │       ├── daily_sessions_with_labels.csv # 2,196 days
│   │       ├── validation_drift_report.csv
│   │       ├── era_comparison_table.csv
│   │       └── NY_Probability_Map.pine      # TradingView indicator
│   │
│   ├── extended_ny/              # NY session length experiments
│   ├── four_factor/              # True 4-factor model with transition
│   ├── alt_sessions/             # Alternative session boundaries
│   └── regime_windows/           # Different Asia regime lookback periods
│
└── PROJECT_OVERVIEW.md           # This file
```

## 🚀 Quick Start

### 1. Data Preparation (Already Complete)
```bash
# Data is already processed: nq_1m_et.csv
# 3,025,725 rows covering 2016-11-14 to 2025-10-01
```

### 2. Run Base Model Analysis
```bash
cd models/base_model
python3 run_analysis.py         # Generate probability map (36 variants)
python3 validation_analysis.py  # Check stability across eras
python3 generate_pinescript.py  # Create TradingView indicator
```

### 3. Use TradingView Indicator
```bash
# Copy contents of: models/base_model/output/NY_Probability_Map.pine
# Paste into TradingView Pine Editor
# Apply to NQ futures chart
```

### 4. Experiment with New Models
```bash
cd models
./create_new_model.sh extended_ny/short_ny   # Create new model
cd extended_ny/short_ny
# Edit config.py with your parameters
python3 run_analysis.py
```

### 5. Compare All Models
```bash
cd models
python3 compare_models.py  # Generate comparison report
```

## 📈 Base Model Results

**Configuration:**
- Asia: 16:00 - 02:00 (10 hours)
- London: 02:00 - 08:00 (6 hours)
- NY: 08:00 - 16:00 (8 hours)

**Performance:**
- ✅ **36 unique variants** (3-factor model)
- ✅ **2,196 trading days** analyzed
- ✅ **5.52% mean drift** across eras (very stable)
- ✅ **53.8% stability rate** (variants with <15% drift)
- ⚠️ **46.13% fail rate** (both levels hit)
- ⚠️ **52.8% low reliability** (variants with <50 samples)

**Top Variants:**
1. Expanded|High|Within|Within (182 samples, 53.85% P(High))
2. Expanded|High|Above|Above (153 samples, 88.24% P(High)) ⭐
3. Normal|High|Above|Above (134 samples, 85.82% P(High)) ⭐

**Strong Directional Edges:**
- **Above|Above variants**: 85-92% P(High) - Strong bullish
- **Below|Below variants**: 9-16% P(High) - Strong bearish

## 🧪 Model Experimentation Framework

### Current Models

#### ✅ Base Model (Production)
- **Status**: Validated and ready
- **Sessions**: Asia 16-02, London 02-08, NY 08-16
- **Factors**: 3 (Asia regime, London sweep, NY vs London)
- **Variants**: 36
- **Use Case**: Foundation model for all comparisons

#### 🚧 Extended NY (Planned)
- **Goal**: Test different NY session lengths
- **Variations**: 3hr (08-11), 4hr (08-12), 8hr (08-16), 9hr (08-17)
- **Hypothesis**: Shorter windows may reduce fail rate

#### 🚧 Four Factor (Planned)
- **Goal**: Restore 4th factor with transition gap
- **Sessions**: Asia 16-02, London 02-08, Gap 08:00-08:30, NY 08:30-16
- **Factors**: 4 (adds separate 08:00 vs 08:30 price)
- **Expected**: ~108 variants

#### 🚧 Alt Sessions (Planned)
- **Goal**: Test alternative session boundaries
- **Variations**: Traditional (20-00-08), Market Hours, Overlaps
- **Hypothesis**: Different boundaries may improve edge

#### 🚧 Regime Windows (Planned)
- **Goal**: Optimize Asia regime lookback period
- **Variations**: 100-day, 200-day, 300-day, 252-day
- **Hypothesis**: Different windows affect regime classification

### Creating New Models

```bash
cd models
./create_new_model.sh your_experiment/variation_name
```

This creates a complete model template with:
- Configuration file (config.py)
- Analysis scripts (copied from base_model)
- README template for documentation
- Output directory structure

## 📊 Key Metrics for Model Comparison

### Statistical Quality
- **Variant Count**: Number of unique patterns found
- **Sample Distribution**: Samples per variant (avoid too many low-n variants)
- **Coverage Rate**: % of days matching a variant
- **Reliability**: % of variants with adequate samples

### Edge & Performance
- **Directional Edge**: Average |P(High) - 50%| across variants
- **Max Edge**: Largest directional bias found
- **Strong Variants**: Count of variants with >70% or <30% edge
- **Fail Rate**: % of days where both levels hit

### Stability
- **Stability Rate**: % of variants with <15% drift across eras
- **Mean Drift**: Average probability change between Era 1 and Era 3
- **Temporal Consistency**: Do probabilities hold over time?

## 🛠️ Technical Architecture

### Data Pipeline
1. **Ingestion**: `download_and_merge.py`
   - Loads 7 CSV parts from GitHub
   - Converts UTC+3 → America/New_York
   - Filters weekends and settlement periods
   - Output: `nq_1m_et.csv` (3M rows)

2. **Session Calculation**: `run_analysis.py`
   - Extracts Asia, London, NY sessions
   - Calculates ranges, sweeps, price relationships
   - Creates variant fingerprints

3. **Label Generation**: `run_analysis.py`
   - Tracks first sweep during NY session
   - Measures penetration beyond target
   - Flags failures (both levels hit)

4. **Probability Aggregation**: `run_analysis.py`
   - Groups by variant
   - Calculates directional probabilities
   - Computes reliability metrics

5. **Validation**: `validation_analysis.py`
   - Splits data into 3 eras
   - Measures probability drift
   - Identifies stable variants

6. **Indicator Generation**: `generate_pinescript.py`
   - Embeds top 25 variants
   - Creates live context detection
   - Builds probability table display

### TradingView Indicator Features

**Live Detection:**
- Session backgrounds (color-coded)
- London High/Low lines (fixed, don't move)
- Real-time variant calculation

**Probability Table (17 rows):**
- P(High First), P(Low First), P(Fail)
- Expected penetration
- Sample size and reliability
- Asia Range and Regime
- London Range and Sweep
- NY Open position
- Target levels (London High/Low)

## 📖 Development Workflow

### 1. Hypothesis Formation
- Identify aspect to test (session times, factors, parameters)
- Document expected outcome

### 2. Model Creation
```bash
cd models
./create_new_model.sh category/model_name
cd category/model_name
```

### 3. Configuration
- Edit `config.py` with new parameters
- Modify `run_analysis.py` if custom logic needed
- Document changes in README.md

### 4. Execution
```bash
python3 run_analysis.py         # Generate probabilities
python3 validation_analysis.py  # Check stability
python3 generate_pinescript.py  # Create indicator
```

### 5. Comparison
```bash
cd ../..
python3 compare_models.py  # Compare to all other models
```

### 6. Documentation
- Update model README with results
- Add findings to comparison notes
- If superior to base, consider promoting

## 🎯 Research Questions

### Session Timing
- ✅ Continuous gapless sessions (base_model)
- ⏳ What is optimal NY session length?
- ⏳ Do overlapping sessions improve signal?
- ⏳ Impact of pre-market data?

### Factor Engineering
- ✅ 3-factor model validated
- ⏳ Does 4th factor (transition) add value?
- ⏳ Should we add volume/volatility factors?
- ⏳ Time-of-day sub-sessions?

### Regime Classification
- ✅ 200-day rolling window (base_model)
- ⏳ Optimal lookback period?
- ⏳ Alternative regime definitions (ATR, volatility)?
- ⏳ Market-adaptive regimes?

### Probability Stability
- ✅ 3-era validation implemented
- ⏳ Does edge persist in forward testing?
- ⏳ Which variants are most stable?
- ⏳ Optimal sample size thresholds?

## 📚 Key Learnings (Base Model)

### What Works ✅
1. **Session-based structure** creates meaningful market context
2. **Asia range regime** differentiates market states effectively
3. **London sweep patterns** provide strong directional signals
4. **"Above|Above" and "Below|Below"** variants show 85%+ edges
5. **Probability stability** across 9 years is remarkably good
6. **Simple 3-factor model** is interpretable and tradeable

### Challenges ⚠️
1. **High fail rate** (46%) limits reliability
2. **Sample distribution** skewed - many low-n variants
3. **Lost 4th factor** due to gapless session design
4. **Long NY window** (8 hours) may dilute signal
5. **No volume data** - pure price action only

### Future Directions 🔮
1. **Shorter NY windows** to reduce fail rate
2. **Add transition gap** to restore 4th factor
3. **Volume filters** to improve signal quality
4. **Machine learning** for multi-factor weighting
5. **Ensemble methods** combining multiple models
6. **Real-time adaptation** based on recent data

## 🤝 Contributing

To add a new model variation:

1. Create model using template script
2. Run full analysis pipeline
3. Document results thoroughly
4. Compare to base_model
5. If superior, document why
6. Consider submitting as new base

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- NQ futures data from [source]
- TradingView for indicator platform
- Quantitative trading community

---

**Project Version**: 1.0
**Last Updated**: 2025-11-18
**Status**: ✅ Base Model Production-Ready, Framework Active
